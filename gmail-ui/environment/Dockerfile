# Two images from one context, so the agent's container never contains the
# world's source or its seed. The agent could otherwise inspect private data
# directly from disk.
FROM python:3.12-slim AS base
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash procps util-linux \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/opt
ENV PYTHONDONTWRITEBYTECODE=1

# --------------------------------------------------------------------------
# world: owns the workspace database and serves the Gmail tools.
# --------------------------------------------------------------------------
FROM base AS world
RUN useradd --system --no-create-home --home-dir /var/lib/gmail \
        --shell /usr/sbin/nologin gmaild
COPY environment/gmail_sim /opt/gmail_sim
COPY environment/rl_env.py /opt/rl_env.py
COPY environment/bin/gmaild-entrypoint environment/bin/gmail-admin /usr/local/bin/
RUN chmod 0755 /usr/local/bin/gmaild-entrypoint /usr/local/bin/gmail-admin \
    && mkdir -p /var/lib/gmail \
    && python3 -m gmail_sim.service seed \
         --db /var/lib/gmail/gmail.db \
         --snapshot /var/lib/gmail/gmail_seed_snapshot.sql \
    && chown -R gmaild:gmaild /var/lib/gmail \
    && chmod 0700 /var/lib/gmail
WORKDIR /var/lib/gmail
ENTRYPOINT ["/usr/local/bin/gmaild-entrypoint"]

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

RUN mkdir -p /opt/gmail_sim
COPY environment/gmail_sim/__init__.py environment/gmail_sim/protocol.py \
     environment/gmail_sim/tool_definitions.py environment/gmail_sim/agent_cli.py \
     environment/gmail_sim/mcp_server.py environment/gmail_sim/admin_cli.py /opt/gmail_sim/
COPY environment/gmail_sim /opt/grading/gmail_sim
COPY verifiers /opt/grading/verifiers
COPY tools /opt/tools
COPY agent /opt/agent
COPY observability /opt/observability
COPY environment/bin/gmail /usr/local/bin/gmail
COPY environment/bin/gmail-mcp /usr/local/bin/gmail-mcp
COPY environment/bin/gmail-admin /usr/local/bin/gmail-admin
RUN chmod 0755 /usr/local/bin/gmail /usr/local/bin/gmail-mcp \
    && chmod 0750 /usr/local/bin/gmail-admin \
    && chown -R root:root /opt/grading \
    && chmod -R go-rwx /opt/grading \
    && chmod 0700 /opt/grading \
    && mkdir -p /app \
    && chown agent:agent /app
WORKDIR /app
CMD ["sh", "-c", "sleep infinity"]
