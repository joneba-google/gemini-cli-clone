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

# Dockerfile for Jetski/Antigravity Worker Job using the Python SDK
# This container runs the manager script (workflow/worker.py) which orchestrates
# the code generation and evaluation in-process using google-antigravity and Firestore synchronization.

FROM python:3.11.9-slim-bookworm

# 1. Install system utilities and pre-install external linters
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    file \
    procps \
    shellcheck \
    xz-utils \
    ca-certificates \
    && ARCH=$(dpkg --print-architecture) \
    && case "$ARCH" in \
        amd64) ACTIONLINT_ARCH="linux_amd64" ;; \
        arm64) ACTIONLINT_ARCH="linux_arm64" ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
       esac \
    && curl -sSLo /tmp/actionlint.tar.gz "https://github.com/rhysd/actionlint/releases/download/v1.7.7/actionlint_1.7.7_${ACTIONLINT_ARCH}.tar.gz" \
    && tar -xzf /tmp/actionlint.tar.gz -C /usr/local/bin actionlint \
    && chmod +x /usr/local/bin/actionlint \
    && rm -rf /tmp/actionlint.tar.gz /var/lib/apt/lists/*

# Copy Node.js 20 and npm directly from the official node:20-slim image
COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# 2. Create non-root system user and establish working directory
RUN useradd -m -u 1000 appuser

WORKDIR /app

# 3. Install Python dependencies using requirements.txt for optimized build layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copy the pipeline orchestration script and prompts with non-root ownership
COPY --chown=appuser:appuser workflow/ /app/workflow/
COPY --chown=appuser:appuser agent_prompts/ /app/agent_prompts/
RUN chown -R appuser:appuser /app

# 5. Switch to unprivileged user
USER appuser

# 6. Execute script directly
ENTRYPOINT ["python", "/app/workflow/worker.py"]
