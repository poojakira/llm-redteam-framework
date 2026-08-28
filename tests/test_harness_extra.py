"""Extra tests for the eval harness (redteam.eval.harness)."""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "src")

import pytest

from redteam.eval import harness


def test_evaluate_random_split_returns_report():
    report, detector = harness.evaluate(split_mode="random", test_size=0.3, seed=1)
    assert report.split_mode == "random"
    assert report.n_test_templates == -1  # not meaningful for random split
    assert detector.is_fitted
    assert 0.0 <= report.precision <= 1.0
    assert 0.0 <= report.recall <= 1.0
    assert report.n_total == report.n_train + report.n_test


def test_evaluate_grouped_split():
    report, _ = harness.evaluate(split_mode="grouped", test_size=0.3, seed=42)
    assert report.split_mode == "grouped"
    assert report.n_test_templates >= 1


def test_evaluate_unknown_split_mode_raises():
    with pytest.raises(ValueError, match="unknown split_mode"):
        harness.evaluate(split_mode="bogus")


def test_report_to_dict_and_json():
    report, _ = harness.evaluate(split_mode="random", seed=3)
    d = report.to_dict()
    assert isinstance(d, dict)
    assert "f1" in d
    js = report.to_json()
    parsed = json.loads(js)
    assert parsed["split_mode"] == "random"


def test_main_prints_report(capsys):
    rc = harness.main(["--split-mode", "random", "--seed", "5"])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert "precision" in parsed


def test_main_writes_output_file(tmp_path):
    out = tmp_path / "report.json"
    rc = harness.main(["--split-mode", "grouped", "--output", str(out)])
    assert rc == 0
    assert out.exists()
    parsed = json.loads(out.read_text(encoding="utf-8"))
    assert parsed["split_mode"] == "grouped"
