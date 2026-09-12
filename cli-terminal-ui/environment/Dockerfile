# Two images from one context, so the agent's container never contains the
# world's source or its seed.
FROM python:3.12-slim AS base
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash procps util-linux \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/opt
ENV PYTHONDONTWRITEBYTECODE=1

# --------------------------------------------------------------------------
# world: owns the workspace database and serves the Terminal tools.
# --------------------------------------------------------------------------
FROM base AS world
RUN useradd --system --no-create-home --home-dir /var/lib/terminal \
        --shell /usr/sbin/nologin terminald
COPY environment/terminal_sim /opt/terminal_sim
COPY environment/rl_env.py /opt/rl_env.py
COPY environment/bin/terminald-entrypoint environment/bin/terminal-admin /usr/local/bin/
RUN chmod 0755 /usr/local/bin/terminald-entrypoint /usr/local/bin/terminal-admin \
    && mkdir -p /var/lib/terminal \
    && python3 -m terminal_sim.admin_cli seed --db /var/lib/terminal/terminal.db \
    && chown -R terminald:terminald /var/lib/terminal \
    && chmod 0700 /var/lib/terminal
WORKDIR /var/lib/terminal
ENTRYPOINT ["/usr/local/bin/terminald-entrypoint"]

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

RUN mkdir -p /opt/terminal_sim
COPY environment/terminal_sim/__init__.py environment/terminal_sim/protocol.py \
     environment/terminal_sim/tool_definitions.py environment/terminal_sim/agent_cli.py \
     environment/terminal_sim/mcp_server.py environment/terminal_sim/admin_cli.py /opt/terminal_sim/
COPY environment/terminal_sim /opt/grading/terminal_sim
COPY verifiers /opt/grading/verifiers
COPY tools /opt/tools
COPY agent /opt/agent
COPY environment/bin/terminal /usr/local/bin/terminal
COPY environment/bin/terminal-mcp /usr/local/bin/terminal-mcp
COPY environment/bin/terminal-admin /usr/local/bin/terminal-admin
RUN chmod 0755 /usr/local/bin/terminal /usr/local/bin/terminal-mcp \
    && chmod 0750 /usr/local/bin/terminal-admin \
    && chown -R root:root /opt/grading \
    && chmod -R go-rwx /opt/grading \
    && chmod 0700 /opt/grading \
    && mkdir -p /app \
    && chown agent:agent /app
WORKDIR /app
CMD ["sh", "-c", "sleep infinity"]
