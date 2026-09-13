#!/usr/bin/env python3
"""CLI bridge connecting software-ui Next.js web application to SoftwareContext & SoftwareService."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

LOCAL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = LOCAL_DIR.parent
sys.path.insert(0, str(LOCAL_DIR))
sys.path.insert(0, str(LOCAL_DIR / "environment"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "software"))

try:
    from software_sim.context import SoftwareContext
    from software_sim.domains import get_all_domains
except ImportError:
    from software.environment.software_sim.context import SoftwareContext
    from software.environment.software_sim.domains import get_all_domains


def get_context() -> SoftwareContext:
    db_env = os.environ.get("SOFTWARE_DB")
    if db_env:
        db_path = Path(db_env)
    elif (REPO_ROOT / "software.db").exists():
        db_path = REPO_ROOT / "software.db"
    else:
        db_path = Path("/tmp/software.db")

    domain = os.environ.get("SOFTWARE_DOMAIN", "logistics")
    split = os.environ.get("SOFTWARE_SPLIT", "iid")
    seed = int(os.environ.get("SOFTWARE_SEED", "42"))
    role = os.environ.get("SOFTWARE_ROLE", "admin")

    ctx = SoftwareContext(db_path=db_path, domain=domain, split=split, seed=seed, actor_role=role)
    ctx.ensure_initialized()
    return ctx


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command argument"}))
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    ctx = get_context()

    try:
        if cmd == "list_domains":
            domains = get_all_domains()
            splits = ["iid", "new_ui", "new_vocab", "new_workflow", "ood"]
            print(json.dumps({"ok": True, "domains": domains, "splits": splits, "current_domain": ctx.domain, "current_split": ctx.split}))

        elif cmd == "get_schema":
            schema = ctx.service.get_schema()
            # If app_spec has ui_layout, pass layout family
            spec = ctx.app_spec
            layout = "sidebar_table"
            if spec and hasattr(spec, "ui_layout") and spec.ui_layout:
                layout = spec.ui_layout.layout_family.value if hasattr(spec.ui_layout.layout_family, "value") else str(spec.ui_layout.layout_family)
            print(json.dumps({"ok": True, "schema": schema, "layout": layout, "domain": ctx.domain, "split": ctx.split}))

        elif cmd == "search_entities":
            entity_name = args[0]
            query = args[1] if len(args) > 1 else ""
            filters = json.loads(args[2]) if len(args) > 2 and args[2] != "" else None
            page = int(args[3]) if len(args) > 3 and args[3] != "" else 1
            page_size = int(args[4]) if len(args) > 4 and args[4] != "" else 25
            res = ctx.execute_tool("search_entities", {
                "entity_name": entity_name,
                "query": query,
                "filters": filters,
                "page": page,
                "page_size": page_size,
            })
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "get_entity":
            entity_name = args[0]
            entity_id = args[1]
            res = ctx.execute_tool("get_entity", {"entity_name": entity_name, "entity_id": entity_id})
            print(json.dumps({"ok": True, "entity": res.get("entity", res)}))

        elif cmd == "create_entity":
            entity_name = args[0]
            fields = json.loads(args[1])
            res = ctx.execute_tool("create_entity", {"entity_name": entity_name, "fields": fields})
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "update_entity":
            entity_name = args[0]
            entity_id = args[1]
            fields = json.loads(args[2])
            res = ctx.execute_tool("update_entity", {"entity_name": entity_name, "entity_id": entity_id, "fields": fields})
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "transition_entity":
            entity_name = args[0]
            entity_id = args[1]
            action = args[2]
            fields = json.loads(args[3]) if len(args) > 3 and args[3] != "" else {}
            res = ctx.execute_tool("transition_entity", {
                "entity_name": entity_name,
                "entity_id": entity_id,
                "action": action,
                "fields": fields,
            })
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "get_audit_log":
            res = ctx.execute_tool("get_audit_log", {})
            print(json.dumps({"ok": True, "audit_log": res.get("audit_log", [])}))

        elif cmd == "get_state_hash":
            h = ctx.calculate_state_hash()
            print(json.dumps({"ok": True, "state_hash": h}))

        elif cmd == "reset_app":
            new_domain = args[0] if len(args) > 0 and args[0] != "" else ctx.domain
            new_split = args[1] if len(args) > 1 and args[1] != "" else ctx.split
            new_seed = int(args[2]) if len(args) > 2 and args[2] != "" else ctx.seed
            ctx.reset(domain=new_domain, split=new_split, seed=new_seed)
            print(json.dumps({"ok": True, "status": "reset", "domain": new_domain, "split": new_split, "seed": new_seed}))

        elif cmd == "submit_task":
            summary = args[0] if args else "Software task completed"
            affected = args[1] if len(args) > 1 else ""
            res = ctx.service.submit_task(summary=summary, affected_ids=affected)
            print(json.dumps({"ok": True, "submission": res}))

        else:
            print(json.dumps({"error": f"Unknown command '{cmd}'"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
