"""Tests for validation false-positive budget reporting."""

from redteam.eval import evaluate
from redteam.eval.harness import main


def test_false_positive_budget_exceeded_is_reported(monkeypatch):
    monkeypatch.setenv("FALSE_POSITIVE_BUDGET", "0.05")
    report, _ = evaluate(split_mode="grouped", test_size=0.3, seed=42)

    assert report.false_positive_rate > report.false_positive_budget
    assert report.false_positive_budget_exceeded is True


def test_false_positive_budget_can_be_relaxed(monkeypatch):
    monkeypatch.setenv("FALSE_POSITIVE_BUDGET", "0.10")
    report, _ = evaluate(split_mode="grouped", test_size=0.3, seed=42)

    assert report.false_positive_budget == 0.10
    assert report.false_positive_budget_exceeded is False

def test_cli_fails_when_fp_budget_exceeded(monkeypatch):
    monkeypatch.setenv("FALSE_POSITIVE_BUDGET", "0.05")
    monkeypatch.delenv("ALLOW_HIGH_FP", raising=False)

    assert main(["--split-mode", "grouped"]) == 2


def test_cli_allows_explicit_high_fp_override(monkeypatch):
    monkeypatch.setenv("FALSE_POSITIVE_BUDGET", "0.05")
    monkeypatch.setenv("ALLOW_HIGH_FP", "true")

    assert main(["--split-mode", "grouped"]) == 0