"""End-to-end tests for procedural task generation, oracle solution execution, and layered verification."""

import os
import tempfile
import pytest

from software.environment.software_sim.context import SoftwareContext
from software.environment.software_sim.db_generator import DatabaseGenerator
from software.environment.software_sim.domains import get_domain_spec
from software.environment.software_sim.task_generator import TaskGenerator
from software.solution.oracle import OracleSolver
from software.tools.software_client import SoftwareClient
from software.verifiers.layered import LayeredVerifier


@pytest.mark.parametrize("domain_name", ["logistics", "research", "clinical_trials", "finops", "real_estate"])
def test_task_generator_and_oracle_solver(domain_name: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, f"{domain_name}.db")
        spec = get_domain_spec(domain_name)

        # 1. Seed database
        gen = DatabaseGenerator(spec, seed=42)
        gen.populate_database(db_path, records_per_entity=15)

        # 2. Generate task
        task_gen = TaskGenerator(app_spec=spec, db_path=db_path, seed=42)
        task = task_gen.generate_task()

        assert "task_id" in task
        assert "instruction" in task
        assert "assertions" in task
        assert "oracle_trajectory" in task
        assert len(task["oracle_trajectory"]) > 0

        # 3. Create client & verifier before execution (initial state)
        ctx = SoftwareContext(db_path=db_path, app_spec=spec)
        client = SoftwareClient(context=ctx)
        verifier = LayeredVerifier(client)

        # Before oracle runs, the task should NOT be completed
        initial_result = verifier.verify(task)
        assert initial_result.success is False

        # 4. Run Oracle Solver
        solver = OracleSolver(client)
        solve_result = solver.solve_task(task)
        assert solve_result["success"] is True

        # 5. Run Layered Verifier after oracle runs
        final_result = verifier.verify(task)
        assert final_result.success is True, f"Verification failed:\n{final_result.feedback}"
        assert final_result.percentage == 1.0
        assert final_result.score == final_result.max_score
