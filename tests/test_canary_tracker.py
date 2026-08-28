"""Tests for CanaryTokenTracker (redteam.detectors.canary_tracker)."""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "src")

from redteam.detectors.canary_tracker import CanaryRecord, CanaryTokenTracker


def test_embed_appends_canary_and_registers():
    tracker = CanaryTokenTracker()
    instrumented = tracker.embed("doc-1", "secret earnings text")
    assert "<!-- CANARY-" in instrumented
    assert instrumented.startswith("secret earnings text")
    summary = tracker.registry_summary()
    assert summary["total_canaries"] == 1
    assert summary["fired"] == 0
    assert summary["unfired"] == 1
    assert summary["fire_rate"] == 0.0


def test_embed_batch():
    tracker = CanaryTokenTracker()
    out = tracker.embed_batch({"a": "text a", "b": "text b"})
    assert set(out.keys()) == {"a", "b"}
    assert all("<!-- CANARY-" in v for v in out.values())
    assert tracker.registry_summary()["total_canaries"] == 2


def test_check_response_detects_leak():
    tracker = CanaryTokenTracker()
    instrumented = tracker.embed("doc-1", "proprietary")
    canary_id = instrumented.split("<!-- ")[1].split(" -->")[0]
    fired = tracker.check_response(f"the answer includes {canary_id} verbatim", session_id="s1")
    assert canary_id in fired
    rec = fired[canary_id]
    assert rec.fired is True
    assert rec.fired_in_session == "s1"
    assert tracker.registry_summary()["fired"] == 1
    assert tracker.registry_summary()["fire_rate"] == 1.0


def test_check_response_no_leak():
    tracker = CanaryTokenTracker()
    tracker.embed("doc-1", "proprietary")
    fired = tracker.check_response("no canary here")
    assert fired == {}


def test_findings_from_leaks():
    tracker = CanaryTokenTracker()
    instrumented = tracker.embed("doc-42", "content")
    canary_id = instrumented.split("<!-- ")[1].split(" -->")[0]
    fired = tracker.check_response(canary_id, session_id="sess")
    findings = tracker.findings_from_leaks(fired)
    assert len(findings) == 1
    f = findings[0]
    assert f["rule_id"] == "LLM07-CanaryFired"
    assert f["severity"] == "HIGH"
    assert f["detector"] == "canary_tracker"
    assert f["owasp_llm_id"] == "LLM07"
    assert "doc-42" in f["message"]


def test_persistence_roundtrip(tmp_path):
    store = tmp_path / "canaries.ndjson"
    tracker = CanaryTokenTracker(store_path=store)
    instrumented = tracker.embed("doc-1", "persistent content")
    canary_id = instrumented.split("<!-- ")[1].split(" -->")[0]
    assert store.exists()
    # Detecting a leak appends another record
    tracker.check_response(canary_id, session_id="s")

    # A new tracker loading the same store should see the canary
    tracker2 = CanaryTokenTracker(store_path=store)
    assert canary_id in tracker2._registry
    rec = tracker2._registry[canary_id]
    assert isinstance(rec, CanaryRecord)
    assert rec.doc_id == "doc-1"


def test_persisted_ndjson_is_valid_json(tmp_path):
    store = tmp_path / "c.ndjson"
    tracker = CanaryTokenTracker(store_path=store)
    tracker.embed("d", "x")
    lines = [ln for ln in store.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 1
    parsed = json.loads(lines[0])
    assert "canary_id" in parsed and "doc_id" in parsed
