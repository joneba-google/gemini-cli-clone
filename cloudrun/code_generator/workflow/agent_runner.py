"""Google Antigravity SDK Agent Runner and Context Management.

Provides execution wrappers for executing Coding and Evaluator AI Agents using
the Google Antigravity SDK. Includes serialized working directory controls
and automatic local sandbox approvals.
"""

import asyncio
import contextlib
import logging
import os
from typing import Any, Iterator


@contextlib.contextmanager
def working_directory(path: str | os.PathLike) -> Iterator[None]:
    """Safely and temporarily changes the working directory.

    Guarantees restoration of the original CWD even in the event of failures.

    Args:
        path: Directory path to switch to.

    Yields:
        None.
    """
    original_cwd = os.getcwd()
    logging.debug("Switching working directory from %s to %s", original_cwd, path)
    os.chdir(path)
    try:
        yield
    finally:
        logging.debug("Restoring working directory to %s", original_cwd)
        os.chdir(original_cwd)


# Permitted tool allowlist for headless sandbox operations
ALLOWED_SANDBOX_TOOLS = {
    # Reading tools
    "view_file",
    "read_file",
    # File writing & editing tools
    "replace_file_content",
    "multi_replace_file_content",
    "write_file",
    "write_to_file",
    # Command execution
    "run_command",
}

# Registering global agent hooks for local sandbox tool calls
try:
    from google.antigravity import Agent, LocalAgentConfig, hooks, policy
except ImportError:
    Agent, LocalAgentConfig, hooks, policy = None, None, None, None

if hooks is not None:
    @hooks.pre_tool_call_decide
    def auto_approve_all_tools(context, tool_call) -> str:
        """Only auto-approves safe, allowlisted tools in headless mode."""
        if tool_call.name in ALLOWED_SANDBOX_TOOLS:
            logging.debug("Auto-approving allowlisted sandbox tool call: %s", tool_call.name)
            return "PROCEED"
        logging.warning("Rejecting non-allowlisted tool call: %s", tool_call.name)
        return "REJECT"


class AgentRunnerError(Exception):
    """Raised when the AI Agent fails to run or complete execution loops."""


class AgentRunner:
    """Manages AI Agent setups and coordinates conversation execution loops."""

    _cwd_lock: asyncio.Lock | None = None

    def __init__(
        self,
        project_id: str,
        location: str = "global",
        model_name: str = "gemini-3.5-flash",
        script_dir: str | None = None,
    ) -> None:
        """Initializes the runner with target Vertex AI details.

        Args:
            project_id: Target Google Cloud Platform Project ID.
            location: Global endpoint location of Vertex AI services (default: "global").
            model_name: Base LLM version string.
            script_dir: Directory containing system/prompt markdown files.
        """
        self.project_id = project_id
        self.location = location or "global"
        self.model_name = model_name
        self.script_dir = script_dir or os.path.dirname(
            os.path.abspath(__file__)
        )

    def _load_prompt_file(self, filename: str) -> str | None:
        """Helper to read a localized system instruction prompt markdown file.

        Args:
            filename: Name of the prompt file inside the script directory.

        Returns:
            The text content if file exists, else None.
        """
        path = os.path.abspath(os.path.join(self.script_dir, filename))
        if not path.startswith(os.path.abspath(self.script_dir)):
            logging.warning("Path traversal attempt detected in prompt loading: %s", filename)
            return None

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except IOError as e:
                logging.warning(
                    "Failed to read prompt file '%s': %s", filename, e
                )
        return None

    async def run_agent(
        self,
        role: str,
        prompt: str,
        repo_path: str,
        system_prompt_file: str | None = None,
    ) -> tuple[str, list[Any]]:
        """Launches and manages an asynchronous conversation with an Antigravity Agent.

        Args:
            role: Label representing the agent's role (e.g., 'Coding Agent').
            prompt: User message prompt guiding the immediate task.
            repo_path: Target directory root of the repository to execute in.
            system_prompt_file: Optional filename of system prompt markdown.

        Returns:
            Tuple of (full_output_text, resolved_chunks_list).

        Raises:
            AgentRunnerError: If Agent fails to run or execution fails.
        """
        if Agent is None:
            raise AgentRunnerError("Google Antigravity SDK is not installed.")

        logging.info("Initializing Agent '%s' inside %s", role, repo_path)

        # Build fallback / configured system instructions
        system_instructions = f"You are the {role}. You must complete the requested tasks in the workspace."
        if system_prompt_file:
            loaded_instructions = self._load_prompt_file(system_prompt_file)
            if loaded_instructions:
                system_instructions = loaded_instructions
                logging.info(
                    "System prompt successfully loaded from %s",
                    system_prompt_file
                )
            else:
                logging.warning(
                    "Requested system prompt file '%s' not found. Reverting to default instructions.",
                    system_prompt_file,
                )

        config = LocalAgentConfig(
            vertex=True,
            project=self.project_id,
            location=self.location,
            model=self.model_name,
            system_instructions=system_instructions,
            policies=[policy.allow_all()],
            workspaces=[repo_path],
        )

        resolved_chunks: list[Any] = []
        stdout_list: list[str] = []
        thinking_list: list[str] = []

        if AgentRunner._cwd_lock is None:
            AgentRunner._cwd_lock = asyncio.Lock()

        try:
            # We change CWD to the repo workspace because the Antigravity SDK Agent
            # interacts relative to the current working process directory.
            # Since os.chdir is process-wide, we must serialize execution to prevent
            # concurrent tasks from corrupting the CWD.
            async with AgentRunner._cwd_lock:
                with working_directory(repo_path):
                    async with Agent(config) as agent:
                        logging.info(
                            "[%s] Sending initial task prompt to conversation loop...",
                            role,
                        )
                        response = await agent.chat(prompt)
                        resolved_chunks = await response.resolve()

                        for chunk in resolved_chunks:
                            chunk_type = chunk.__class__.__name__
                            chunk_text = getattr(chunk, "text", None)
                            if chunk_type == "Text" and chunk_text:
                                stdout_list.append(chunk_text)
                            elif chunk_type == "Thought" and chunk_text:
                                thinking_list.append(chunk_text)
                            elif chunk_type == "ToolCall":
                                tool_name = getattr(chunk, "name", "unknown")
                                tool_args = getattr(chunk, "args", {})
                                logging.info("[%s Tool Call]: %s with args %s", role, tool_name, tool_args)

            full_output = "".join(stdout_list).strip()
            if not full_output and stdout_list:
                full_output = "\n".join(stdout_list)

            logging.info("Agent '%s' execution completed successfully.", role)
            return full_output, resolved_chunks

        except Exception as e:
            logging.exception("Failed to execute agent loop for role: %s", role)
            raise AgentRunnerError(f"Agent '{role}' execution failed: {e}") from e
