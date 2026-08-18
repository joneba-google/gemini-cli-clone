# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""GCLI Orchestrator Package.

This package contains all components of the SSR Agent Orchestrator:
- config: Configuration loading and validation.
- command_executor: Subprocess execution utility.
- github_client: GitHub v3 REST API client.
- agent_runner: Google Antigravity SDK wrapper.
- preflight_filter: Preflight test verification filtering.
- orchestrator: Orchestration state machine coordinating code generation and evaluation.
"""
