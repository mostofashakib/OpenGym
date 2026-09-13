"""High-level client for interacting with the Software Environment.

Can operate either in-process using SoftwareContext / SoftwareService,
or over transport if configured.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from software.environment.software_sim.context import SoftwareContext
from software.environment.software_sim.service import SoftwareService
from software.environment.software_sim.spec import AppSpec


class SoftwareClient:
    """Client interface for interacting with a generated software application."""

    def __init__(
        self,
        db_path: str = "/tmp/software_sim.db",
        app_spec_path: Optional[str] = None,
        context: Optional[SoftwareContext] = None,
    ) -> None:
        if context is not None:
            self._ctx = context
        else:
            self._ctx = SoftwareContext(db_path=db_path, app_spec_path=app_spec_path)
        self._service: SoftwareService = self._ctx.service

    @property
    def service(self) -> SoftwareService:
        return self._service

    @property
    def app_spec(self) -> AppSpec:
        if self._ctx.app_spec is not None:
            return self._ctx.app_spec
        from software.environment.software_sim.domains import get_domain_spec
        return get_domain_spec("logistics")

    def get_schema(self) -> Dict[str, Any]:
        """Fetch the full declarative schema of the application."""
        return self._service.get_schema()

    def search(
        self,
        entity_name: str,
        query: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search and filter records."""
        return self._service.search_entities(
            entity_name=entity_name,
            query=query,
            status_filter=status_filter,
            limit=limit,
        )

    def get(self, entity_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get an entity record by ID."""
        return self._service.get_entity(entity_name=entity_name, entity_id=entity_id)

    def create(
        self,
        entity_name: str,
        fields: Dict[str, Any],
        actor: str = "agent",
    ) -> Dict[str, Any]:
        """Create a new entity record."""
        return self._service.create_entity(entity_name=entity_name, fields=fields, actor=actor)

    def update(
        self,
        entity_name: str,
        entity_id: str,
        fields: Dict[str, Any],
        actor: str = "agent",
    ) -> Dict[str, Any]:
        """Update fields on an existing record."""
        return self._service.update_entity(
            entity_name=entity_name,
            entity_id=entity_id,
            fields=fields,
            actor=actor,
        )

    def transition(
        self,
        entity_name: str,
        entity_id: str,
        action: str,
        actor: str = "agent",
        actor_role: str = "admin",
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Transition an entity through its lifecycle workflow."""
        return self._service.transition_entity(
            entity_name=entity_name,
            entity_id=entity_id,
            action=action,
            actor=actor,
            actor_role=actor_role,
            payload=payload,
        )

    def get_audit_trail(
        self,
        entity_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit log records."""
        return self._service.get_audit_log(entity_id=entity_id, limit=limit)

    def calculate_state_hash(self) -> str:
        """Compute the cryptographic SHA-256 hash of the current database state."""
        return self._service.calculate_state_hash()
