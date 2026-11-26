"""
CERBERUS-XA: AI Reasoning & Evidence Verification Module (Member 4)
Demo Output Integrity & Freshness Regression Tests

Regenerates all 10 demo scenarios into a temporary directory in-process,
and verifies exact structural identity with the committed backend/reasoning/demo_outputs/
ignoring non-deterministic request_id fields.
"""

import json
from pathlib import Path
import tempfile
import pytest

from backend.reasoning.regenerate_demo_outputs import regenerate_all


def _strip_request_ids(obj):
    """Recursively removes 'request_id' fields from JSON objects for deterministic comparison."""
    if isinstance(obj, dict):
        return {k: _strip_request_ids(v) for k, v in obj.items() if k != "request_id"}
    elif isinstance(obj, list):
        return [_strip_request_ids(item) for item in obj]
    return obj


def test_demo_outputs_fresh_and_identical_to_saved():
    """
    Part D.2: Verifies that in-process execution produces outputs identical to
    backend/reasoning/demo_outputs/ across all 10 scenarios.
    """
    saved_dir = Path(__file__).resolve().parent.parent / "demo_outputs"
    assert saved_dir.exists(), f"Saved demo_outputs directory not found at {saved_dir}"

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        results = regenerate_all(target_dir=tmp_dir)

        assert len(results) == 10, f"Expected 10 scenarios, got {len(results)}"

        for scenario_name, (fresh_status, fresh_data) in results.items():
            saved_json_path = saved_dir / f"{scenario_name}.json"
            saved_status_path = saved_dir / f"{scenario_name}.status"

            assert saved_json_path.exists(), f"Missing saved artifact: {saved_json_path}"
            assert saved_status_path.exists(), f"Missing saved status: {saved_status_path}"

            # 1. Compare status codes
            saved_status_text = saved_status_path.read_text(encoding="utf-8").strip()
            expected_status_text = f"HTTP {fresh_status}"
            assert saved_status_text == expected_status_text, (
                f"Status mismatch for {scenario_name}: saved '{saved_status_text}' vs fresh '{expected_status_text}'"
            )

            # 2. Compare JSON content ignoring request_id
            with open(saved_json_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            clean_saved = _strip_request_ids(saved_data)
            clean_fresh = _strip_request_ids(fresh_data)

            assert clean_saved == clean_fresh, (
                f"Content divergence detected for scenario '{scenario_name}'"
            )
