# Two images from one context, so the agent's container never contains the
# world's source or its seed.
FROM python:3.12-slim AS base
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash procps util-linux \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/opt
ENV PYTHONDONTWRITEBYTECODE=1

# --------------------------------------------------------------------------
# world: owns the workspace database and serves the Browser tools.
# --------------------------------------------------------------------------
FROM base AS world
RUN useradd --system --no-create-home --home-dir /var/lib/browser \
        --shell /usr/sbin/nologin browserd
COPY environment/browser_sim /opt/browser_sim
COPY environment/rl_env.py /opt/rl_env.py
COPY environment/bin/browserd-entrypoint environment/bin/browser-admin /usr/local/bin/
RUN chmod 0755 /usr/local/bin/browserd-entrypoint /usr/local/bin/browser-admin \
    && mkdir -p /var/lib/browser \
    && python3 -m browser_sim.admin_cli seed --db /var/lib/browser/browser.db \
    && chown -R browserd:browserd /var/lib/browser \
    && chmod 0700 /var/lib/browser
WORKDIR /var/lib/browser
ENTRYPOINT ["/usr/local/bin/browserd-entrypoint"]

# --------------------------------------------------------------------------
# agent: the client half only. No seed, no service, no database.
# --------------------------------------------------------------------------
FROM base AS agent
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl jq nodejs npm \
    && npm install --global @anthropic-ai/claude-code@2.1.258 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash agent
ENV SHELL=/bin/bash

RUN mkdir -p /opt/browser_sim
COPY environment/browser_sim/__init__.py environment/browser_sim/protocol.py \
     environment/browser_sim/tool_definitions.py environment/browser_sim/agent_cli.py \
     environment/browser_sim/mcp_server.py environment/browser_sim/admin_cli.py /opt/browser_sim/
COPY environment/browser_sim /opt/grading/browser_sim
COPY verifiers /opt/grading/verifiers
COPY tools /opt/tools
COPY agent /opt/agent
COPY environment/bin/browser /usr/local/bin/browser
COPY environment/bin/browser-mcp /usr/local/bin/browser-mcp
COPY environment/bin/browser-admin /usr/local/bin/browser-admin
RUN chmod 0755 /usr/local/bin/browser /usr/local/bin/browser-mcp \
    && chmod 0750 /usr/local/bin/browser-admin \
    && chown -R root:root /opt/grading \
    && chmod -R go-rwx /opt/grading \
    && chmod 0700 /opt/grading \
    && mkdir -p /app \
    && chown agent:agent /app
WORKDIR /app
CMD ["sh", "-c", "sleep infinity"]
