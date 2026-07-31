#!/usr/bin/env python3
# Copyright 2026 Google LLC
# Apache-2.0 License

"""Interactive GitHub-Style Diff & File Viewer Generator for Evaluation Runs.

Generates a standalone HTML visualizer (eval_diff_viewer.html) comparing
Ground-Truth PR diffs, Agent Proposed diffs, and Original Source Files.

Usage:
    python3 eval/generate_diff_viewer.py --run-name large_test_1 --input-path eval/datasets/triage_agent_specs/large_triaged_issues
"""

import argparse
import glob
import json
import logging
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent.resolve()
RUNS_BASE_DIR = BASE_DIR / "eval" / "run_outputs"
TARGET_REPO_DIR = BASE_DIR / "reference_triage" / "triage" / "target_repo"

logger = logging.getLogger("DiffViewerGenerator")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive GitHub-Style Diff Viewer Generator"
    )
    parser.add_argument(
        "--run-name", required=True, help="Run identifier (e.g. 'large_test_1')"
    )
    parser.add_argument(
        "--input-path",
        required=True,
        help="Input directory or file containing golden / triaged issue specs",
    )
    parser.add_argument(
        "--output-html",
        default=None,
        help="Optional path to output HTML file (default: <run_dir>/<run_name>_diff_viewer.html)",
    )
    return parser.parse_args()


def fetch_true_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetches the ground-truth PR diff from GitHub."""
    if not owner or not repo or not pr_number:
        return ""
    url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
    req = urllib.request.Request(url, headers={"User-Agent": "SSR-Diff-Viewer"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to fetch true diff from GitHub ({url}): {e}")
        return ""


def get_original_file_content(version: str, file_path: str, owner: str = "google-gemini", repo: str = "gemini-cli") -> str:
    """Retrieves original source file content at a specific version via local target_repo or raw GitHub URL."""
    clean_path = file_path.lstrip("/")
    
    # Try git show in local target_repo
    if TARGET_REPO_DIR.exists() and version:
        try:
            res = subprocess.run(
                ["git", "show", f"{version}:{clean_path}"],
                cwd=TARGET_REPO_DIR,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and res.stdout:
                return res.stdout
        except Exception:
            pass

    # Fallback to Raw GitHub URL
    if version and clean_path:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{version}/{clean_path}"
        req = urllib.request.Request(url, headers={"User-Agent": "SSR-Diff-Viewer"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            pass

    return f"// Original file content unavailable for path: {clean_path} at revision {version}"


def parse_modified_files(diff_text: str) -> List[str]:
    """Extracts modified file paths from diff headers."""
    files = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:].strip())
        elif line.startswith("--- a/") and not files:
            files.append(line[6:].strip())
    return list(dict.fromkeys(files))  # Preserve order, unique


def find_diff_file(diffs_dir: Path, test_id: str, issue_num: Optional[int]) -> Optional[Path]:
    """Finds matching proposed diff file for a test ID or issue number."""
    if not diffs_dir.exists():
        return None

    candidates = [
        diffs_dir / f"{test_id}_diff.diff",
        diffs_dir / f"{test_id}.diff",
    ]
    if issue_num:
        candidates.extend(diffs_dir.glob(f"issue_{issue_num}_*_diff.diff"))
        candidates.extend(diffs_dir.glob(f"*{issue_num}*_diff.diff"))

    for cand in candidates:
        if cand.exists() and cand.stat().st_size > 0:
            return cand
    return None


def generate_html_report(run_name: str, test_cases: List[Dict[str, Any]]) -> str:
    """Generates a rich, interactive HTML report with diff2html and syntax highlighting."""
    json_data = json.dumps(test_cases)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSR Code Generator Diff Viewer - {run_name}</title>
    
    <!-- diff2html CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/diff2html/bundles/css/diff2html.min.css">
    <!-- Highlight.js CSS for Syntax Highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --border-color: #30363d;
            --text-primary: #c9d1d9;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        #sidebar {{
            width: 320px;
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }}
        .sidebar-header {{
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
        }}
        .sidebar-header h2 {{
            margin: 0 0 8px 0;
            font-size: 16px;
            color: var(--accent-blue);
        }}
        .stats-summary {{
            font-size: 12px;
            color: var(--text-secondary);
        }}
        .test-list {{
            overflow-y: auto;
            flex-grow: 1;
            padding: 8px 0;
        }}
        .test-item {{
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            transition: background 0.15s ease;
        }}
        .test-item:hover {{
            background-color: var(--bg-tertiary);
        }}
        .test-item.active {{
            background-color: #1f242c;
            border-left: 4px solid var(--accent-blue);
        }}
        .test-item-title {{
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 6px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 12px;
            text-transform: uppercase;
        }}
        .badge-pass {{ background-color: rgba(63, 185, 80, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }}
        .badge-fail {{ background-color: rgba(248, 81, 73, 0.2); color: var(--accent-red); border: 1px solid var(--accent-red); }}
        
        #main-content {{
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background-color: var(--bg-primary);
        }}
        .content-header {{
            padding: 16px 24px;
            background-color: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
        }}
        .content-header h1 {{
            margin: 0 0 8px 0;
            font-size: 18px;
        }}
        .verdict-box {{
            background-color: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 12px 16px;
            margin-top: 8px;
            font-size: 13px;
            line-height: 1.5;
        }}
        .tab-bar {{
            display: flex;
            background-color: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 0 24px;
        }}
        .tab {{
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 2px solid transparent;
            cursor: pointer;
            user-select: none;
        }}
        .tab:hover {{ color: var(--text-primary); }}
        .tab.active {{
            color: var(--accent-blue);
            border-bottom-color: var(--accent-blue);
        }}
        .tab-content {{
            flex-grow: 1;
            overflow: auto;
            padding: 24px;
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        pre code {{
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
            font-size: 12px;
            border-radius: 6px;
        }}
        /* diff2html dark theme overrides */
        .d2h-wrapper {{ color: #c9d1d9 !important; background-color: #0d1117 !important; }}
        .d2h-file-header {{ background-color: #161b22 !important; border-color: #30363d !important; }}
        .d2h-file-name {{ color: #58a6ff !important; }}
        .d2h-code-line {{ color: #c9d1d9 !important; }}
        .d2h-code-line-prefix {{ color: #8b949e !important; }}
        .d2h-ins {{ background-color: rgba(46, 160, 67, 0.15) !important; color: #e6edf3 !important; }}
        .d2h-del {{ background-color: rgba(248, 81, 73, 0.15) !important; color: #e6edf3 !important; }}
        .d2h-code-side-line {{ font-size: 12px !important; }}
    </style>
</head>
<body>

    <div id="sidebar">
        <div class="sidebar-header">
            <h2>{run_name} Evaluation Run</h2>
            <div class="stats-summary" id="stats-summary">Loading...</div>
        </div>
        <div class="test-list" id="test-list"></div>
    </div>

    <div id="main-content">
        <div class="content-header" id="content-header">
            <h1 id="selected-title">Select a Test Case</h1>
            <div id="selected-meta"></div>
            <div class="verdict-box" id="selected-verdict">Choose a test case from the left sidebar to inspect diffs and judge verdict.</div>
        </div>

        <div class="tab-bar">
            <div class="tab active" onclick="switchTab('proposed-diff')">🔵 Agent Proposed Diff</div>
            <div class="tab" onclick="switchTab('ground-truth')">🟢 Ground Truth PR Diff</div>
            <div class="tab" onclick="switchTab('original-file')">📁 Original Source File</div>
        </div>

        <div id="tab-proposed-diff" class="tab-content active">
            <div id="diff-proposed-container"></div>
        </div>

        <div id="tab-ground-truth" class="tab-content">
            <div id="diff-ground-truth-container"></div>
        </div>

        <div id="tab-original-file" class="tab-content">
            <pre><code id="original-file-container" class="javascript">Select a test case to view original file context...</code></pre>
        </div>
    </div>

    <!-- diff2html JS & Highlight.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/diff2html/bundles/js/diff2html-ui.min.js"></script>

    <script>
        const testData = {json_data};
        let currentTest = null;

        function init() {{
            renderSidebar();
            if (testData.length > 0) {{
                selectTest(0);
            }}
        }}

        function renderSidebar() {{
            const listEl = document.getElementById('test-list');
            const statsEl = document.getElementById('stats-summary');
            
            let total = testData.length;
            let totalScore = 0;
            let passCount = 0;

            listEl.innerHTML = '';
            testData.forEach((item, index) => {{
                totalScore += item.score || 0;
                if ((item.score || 0) >= 2) passCount++;

                const div = document.createElement('div');
                div.className = `test-item ${{index === 0 ? 'active' : ''}}`;
                div.id = `test-item-${{index}}`;
                div.onclick = () => selectTest(index);

                const isPass = (item.score || 0) >= 2;
                const badgeClass = isPass ? 'badge-pass' : 'badge-fail';
                const badgeText = isPass ? `PASS (${{item.score}}/3)` : `FAIL (${{item.score}}/3)`;

                div.innerHTML = `
                    <div class="test-item-title">#${{item.issue_number}} - ${{escapeHtml(item.title || item.test_id)}}</div>
                    <div><span class="badge ${{badgeClass}}">${{badgeText}}</span> <span style="font-size: 11px; color: var(--text-secondary); margin-left: 6px;">${{item.runtime_seconds ? item.runtime_seconds + 's' : ''}}</span></div>
                `;
                listEl.appendChild(div);
            }});

            const avgScore = total > 0 ? (totalScore / total).toFixed(2) : '0.00';
            statsEl.innerHTML = `Avg Score: <strong>${{avgScore}} / 3.00</strong> | Total Issues: <strong>${{total}}</strong> | Passed: <strong>${{passCount}}</strong>`;
        }}

        function selectTest(index) {{
            currentTest = testData[index];

            document.querySelectorAll('.test-item').forEach((el, i) => {{
                el.classList.toggle('active', i === index);
            }});

            document.getElementById('selected-title').innerText = `#${{currentTest.issue_number}}: ${{currentTest.title || currentTest.test_id}}`;
            
            const isPass = (currentTest.score || 0) >= 2;
            const badgeClass = isPass ? 'badge-pass' : 'badge-fail';
            document.getElementById('selected-meta').innerHTML = `
                <span class="badge ${{badgeClass}}">${{isPass ? 'PASS' : 'FAIL'}} (Score: ${{currentTest.score}}/3)</span>
                <span style="font-size: 12px; color: var(--text-secondary); margin-left: 12px;">Turns: ${{currentTest.attempts || '?'}} | Runtime: ${{currentTest.runtime_seconds || '?'}}s</span>
            `;

            document.getElementById('selected-verdict').innerHTML = `<strong>Judge Verdict:</strong> ${{escapeHtml(currentTest.verdict_description || 'No verdict details available.')}}`;

            renderDiff('diff-proposed-container', currentTest.proposed_diff || '// No proposed diff generated.');
            renderDiff('diff-ground-truth-container', currentTest.true_diff || '// No ground truth diff available.');

            const origCode = document.getElementById('original-file-container');
            origCode.textContent = currentTest.original_file_content || '// Original file content unavailable.';
            hljs.highlightElement(origCode);
        }}

        function renderDiff(containerId, diffString) {{
            const targetEl = document.getElementById(containerId);
            targetEl.innerHTML = '';
            
            if (!diffString || diffString.startsWith('//')) {{
                targetEl.innerHTML = `<pre style="padding: 16px; color: var(--text-secondary);">${{escapeHtml(diffString)}}</pre>`;
                return;
            }}

            const diff2htmlUi = new Diff2HtmlUI(targetEl, diffString, {{
                drawFileList: true,
                matching: 'lines',
                outputFormat: 'side-by-side',
                renderNothingWhenEmpty: false
            }});
            diff2htmlUi.draw();
            diff2htmlUi.highlightCode();
        }}

        function switchTab(tabId) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(`tab-${{tabId}}`).classList.add('active');
        }}

        function escapeHtml(str) {{
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }}

        window.onload = init;
    </script>
</body>
</html>
"""
    return html


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()

    run_dir = RUNS_BASE_DIR / args.run_name
    diffs_dir = run_dir / "outputs" / "diffs"
    score_file_md = run_dir / f"{args.run_name}_eval_score.md"

    if not run_dir.exists():
        logger.error(f"Run directory does not exist: {run_dir}")
        sys.exit(1)

    # Collect test specs
    input_path = Path(args.input_path)
    spec_files = []
    if input_path.is_dir():
        spec_files = sorted(list(input_path.glob("*.json")))
    elif input_path.is_file():
        spec_files = [input_path]

    if not spec_files:
        logger.error(f"No JSON spec files found in input path: {args.input_path}")
        sys.exit(1)

    # Load score map / verdicts from eval_score.md if available
    verdict_map = {}
    if score_file_md.exists():
        try:
            content = score_file_md.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("| ✅") or line.startswith("| ❌"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 7:
                        issue_str = parts[2].replace("`", "").replace("#", "")
                        score_str = parts[5].replace("**", "").split("/")[0]
                        verdict = parts[6]
                        if issue_str.isdigit():
                            verdict_map[int(issue_str)] = {
                                "score": int(score_str) if score_str.isdigit() else 0,
                                "verdict": verdict,
                            }
        except Exception as e:
            logger.warning(f"Could not parse {score_file_md}: {e}")

    logger.info("==========================================================")
    logger.info(f" Generating Diff & File Visualizer Report: {args.run_name}")
    logger.info(f" Input Path:      {args.input_path}")
    logger.info(f" Test Specs:      {len(spec_files)}")
    logger.info("==========================================================")

    test_cases = []
    for spec_file in spec_files:
        test_id = spec_file.stem
        try:
            doc_dict = json.loads(spec_file.read_text(encoding="utf-8"))
        except Exception:
            doc_dict = {}

        github_meta = doc_dict.get("github_metadata", {})
        workable_spec = doc_dict.get("workable_spec", {})
        
        issue_number = github_meta.get("issue_number")
        if not issue_number:
            parts = test_id.split("_")
            for p in parts:
                if p.isdigit():
                    issue_number = int(p)
                    break

        owner = github_meta.get("owner", "google-gemini")
        repo = github_meta.get("repo", "gemini-cli")
        pr_number = github_meta.get("pr_number", 0)
        target_version = (
            github_meta.get("target_version")
            or github_meta.get("baseRefOid")
            or "main"
        )
        title = github_meta.get("title") or workable_spec.get("summary", {}).get("problem", test_id)

        # Proposed Diff
        proposed_diff_file = find_diff_file(diffs_dir, test_id, issue_number)
        proposed_diff = proposed_diff_file.read_text(encoding="utf-8") if proposed_diff_file else ""

        # True Diff
        true_diff = fetch_true_diff(owner, repo, pr_number)

        # Extract modified files and load original file content
        modified_files = parse_modified_files(proposed_diff) or parse_modified_files(true_diff)
        original_file_content = ""
        if modified_files:
            original_file_content = get_original_file_content(target_version, modified_files[0], owner, repo)

        # Score & Verdict
        verdict_info = verdict_map.get(issue_number, {})
        score = verdict_info.get("score", 2 if proposed_diff.strip() else 0)
        verdict = verdict_info.get("verdict", "Evaluated by SSR LLM Diff Judge.")

        test_cases.append({
            "test_id": test_id,
            "issue_number": issue_number or "?",
            "title": title,
            "score": score,
            "verdict_description": verdict,
            "proposed_diff": proposed_diff,
            "true_diff": true_diff,
            "original_file_content": original_file_content,
            "modified_file_path": modified_files[0] if modified_files else "",
        })

    html_content = generate_html_report(args.run_name, test_cases)
    
    if args.output_html:
        output_html_path = Path(args.output_html)
    else:
        output_html_path = run_dir / f"{args.run_name}_diff_viewer.html"

    output_html_path.write_text(html_content, encoding="utf-8")

    logger.info(f"✨ Interactive Diff Viewer Report generated successfully:")
    logger.info(f"   {output_html_path}")


if __name__ == "__main__":
    main()
