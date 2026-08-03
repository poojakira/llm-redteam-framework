import pytest

attack_core = pytest.importorskip("attack_core", reason="requires attack-v19-core package")
from attack_core import ATTACKIndex, ATTACKLoader  # noqa: E402

from attack_mapping.enricher import ATTACKEnricher  # noqa: E402


@pytest.fixture
def enricher():
    loader = ATTACKLoader()
    index = ATTACKIndex(loader)
    return ATTACKEnricher(index)


def mapped_ids(mappings):
    return {m.subtechnique_id or m.technique_id for m in mappings}


class TestLLMRedTeamEnricher:
    def test_jailbreak(self, enricher):
        mappings = enricher.enrich("jailbreak_success", {"confidence": 0.9})
        assert "T1059" in mapped_ids(mappings)
        assert "T1685" in mapped_ids(mappings)

    def test_system_prompt_leak(self, enricher):
        mappings = enricher.enrich("system_prompt_leak", {"confidence": 0.8})
        assert "T1552" in mapped_ids(mappings)
        assert "T1083" in mapped_ids(mappings)

    def test_prompt_injection_rce(self, enricher):
        mappings = enricher.enrich("prompt_injection_rce", {"confidence": 0.95})
        assert "T1059.006" in mapped_ids(mappings)
        assert "T1203" in mapped_ids(mappings)
