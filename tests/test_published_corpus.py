"""Benchmark the EmbeddingSimilarityDetector against REAL published injection corpus.

This is the first external benchmark for the detector — using actual published
prompt injections from academic papers and security research, not synthetic data.

Sources tested:
- HackAPrompt (Schulhoff et al. 2023, NeurIPS)
- Gandalf (Lakera 2023)
- Willison (2023) indirect injection research
- Greshake et al. (2023) "Not what you've signed up for"
- OWASP LLM Top 10 (2025) LLM01

Metrics reported:
- Detection rate (recall) on real injections
- False positive rate on real benign prompts
- Per-source detection breakdown
- Per-category detection breakdown
"""

from __future__ import annotations

import pytest

from redteam.data.published_injections import (
    PUBLISHED_BENIGN,
    PUBLISHED_CORPUS,
    PUBLISHED_INJECTIONS,
    get_benign_count,
    get_corpus_by_category,
    get_corpus_by_source,
    get_injection_count,
)
from redteam.detectors.embedding_similarity import EmbeddingSimilarityDetector


@pytest.fixture(scope="module")
def detector() -> EmbeddingSimilarityDetector:
    """Initialize the EmbeddingSimilarityDetector (TF-IDF fallback mode)."""
    return EmbeddingSimilarityDetector(use_dense=False)


class TestCorpusIntegrity:
    """Validate the published corpus meets minimum requirements."""

    def test_minimum_injection_count(self) -> None:
        """Corpus must have at least 50 real injection examples."""
        count = get_injection_count()
        assert count >= 50, f"Need >= 50 injections, got {count}"

    def test_minimum_benign_count(self) -> None:
        """Corpus must have at least 50 real benign examples."""
        count = get_benign_count()
        assert count >= 50, f"Need >= 50 benign examples, got {count}"

    def test_all_injections_labeled_1(self) -> None:
        """All injection entries must have label=1."""
        for text, label, _source, _category in PUBLISHED_INJECTIONS:
            assert label == 1, f"Injection has wrong label: {text[:60]}..."

    def test_all_benign_labeled_0(self) -> None:
        """All benign entries must have label=0."""
        for text, label, _source, _category in PUBLISHED_BENIGN:
            assert label == 0, f"Benign has wrong label: {text[:60]}..."

    def test_all_entries_have_source(self) -> None:
        """Every entry must have a non-empty source citation."""
        for text, _label, source, _category in PUBLISHED_CORPUS:
            assert source.strip(), f"Missing source for: {text[:60]}..."

    def test_all_entries_have_category(self) -> None:
        """Every entry must have a non-empty category."""
        for text, _label, _source, category in PUBLISHED_CORPUS:
            assert category.strip(), f"Missing category for: {text[:60]}..."

    def test_no_empty_texts(self) -> None:
        """No entry should have empty text."""
        for text, _label, source, _category in PUBLISHED_CORPUS:
            assert text.strip(), f"Empty text with source={source}"

    def test_no_exact_duplicates(self) -> None:
        """No duplicate texts in the corpus."""
        texts = [t for t, _, _, _ in PUBLISHED_CORPUS]
        assert len(texts) == len(set(texts)), "Duplicate entries found in corpus"

    def test_source_coverage(self) -> None:
        """Corpus must include examples from all 5 required research sources."""
        sources_found = set()
        for _, _, source, _ in PUBLISHED_CORPUS:
            if "Schulhoff" in source or "HackAPrompt" in source:
                sources_found.add("HackAPrompt")
            elif "Lakera" in source or "Gandalf" in source:
                sources_found.add("Gandalf")
            elif "Willison" in source:
                sources_found.add("Willison")
            elif "Greshake" in source:
                sources_found.add("Greshake")
            elif "OWASP" in source:
                sources_found.add("OWASP")

        expected = {"HackAPrompt", "Gandalf", "Willison", "Greshake", "OWASP"}
        missing = expected - sources_found
        assert not missing, f"Missing sources: {missing}"


class TestDetectionRate:
    """Benchmark the EmbeddingSimilarityDetector on real published injections."""

    def test_overall_detection_rate(self, detector: EmbeddingSimilarityDetector) -> None:
        """Report overall detection rate on real injection corpus."""
        detected = 0
        missed = []

        for text, _label, source, category in PUBLISHED_INJECTIONS:
            findings = detector.scan(text)
            if findings:
                detected += 1
            else:
                missed.append((text[:80], source, category))

        total = len(PUBLISHED_INJECTIONS)
        detection_rate = detected / total

        print(f"\n{'='*70}")
        print("EXTERNAL BENCHMARK: EmbeddingSimilarityDetector vs Published Corpus")
        print(f"{'='*70}")
        print(f"Total injections tested: {total}")
        print(f"Detected: {detected}")
        print(f"Missed: {total - detected}")
        print(f"Detection rate (recall): {detection_rate:.2%}")
        print(f"{'='*70}")

        if missed:
            print(f"\nMissed injections ({len(missed)}):")
            for text, source, cat in missed[:10]:  # Show first 10
                print(f"  [{cat}] ({source}): {text}...")

        # This is primarily an informational benchmark. The TF-IDF sparse mode
        # has limited semantic understanding — this benchmark documents that gap
        # honestly. The key value is tracking improvements over time.
        # Threshold is intentionally low: we're documenting baseline performance,
        # not asserting production readiness.
        assert detection_rate > 0.0, (
            "Detection rate is 0% — detector catches NONE of the real-world "
            "published injections. Something is fundamentally broken."
        )

    def test_false_positive_rate(self, detector: EmbeddingSimilarityDetector) -> None:
        """Report false positive rate on real benign prompts."""
        false_positives = 0
        fp_examples = []

        for text, _label, _source, _category in PUBLISHED_BENIGN:
            findings = detector.scan(text)
            if findings:
                false_positives += 1
                fp_examples.append((text[:80], findings[0]["severity"]))

        total = len(PUBLISHED_BENIGN)
        fp_rate = false_positives / total

        print(f"\nFalse positive rate on real benign: {fp_rate:.2%} ({false_positives}/{total})")

        if fp_examples:
            print(f"\nFalse positives ({len(fp_examples)}):")
            for text, severity in fp_examples[:10]:
                print(f"  [{severity}] {text}...")

        # FP rate on real benign should be reasonable
        assert fp_rate < 0.40, (
            f"False positive rate {fp_rate:.2%} is too high. "
            f"Detector flags too many legitimate prompts."
        )

    def test_detection_by_source(self, detector: EmbeddingSimilarityDetector) -> None:
        """Break down detection rate by research source."""
        source_prefixes = {
            "HackAPrompt": "Schulhoff",
            "Gandalf": "Lakera",
            "Willison": "Willison",
            "Greshake": "Greshake",
            "OWASP": "OWASP",
        }

        print(f"\n{'='*70}")
        print("DETECTION RATE BY SOURCE")
        print(f"{'='*70}")

        for name, prefix in source_prefixes.items():
            entries = get_corpus_by_source(prefix)
            injections = [(t, l, s, c) for t, l, s, c in entries if l == 1]

            if not injections:
                print(f"  {name}: No injection examples found")
                continue

            detected = sum(1 for t, _, _, _ in injections if detector.scan(t))
            rate = detected / len(injections)
            print(f"  {name}: {detected}/{len(injections)} = {rate:.2%}")

    def test_detection_by_category(self, detector: EmbeddingSimilarityDetector) -> None:
        """Break down detection rate by attack category."""
        categories = set(cat for _, _, _, cat in PUBLISHED_INJECTIONS)

        print(f"\n{'='*70}")
        print("DETECTION RATE BY CATEGORY")
        print(f"{'='*70}")

        for category in sorted(categories):
            entries = get_corpus_by_category(category)
            injections = [(t, l, s, c) for t, l, s, c in entries if l == 1]

            if not injections:
                continue

            detected = sum(1 for t, _, _, _ in injections if detector.scan(t))
            rate = detected / len(injections)
            print(f"  {category}: {detected}/{len(injections)} = {rate:.2%}")

    def test_severity_distribution(self, detector: EmbeddingSimilarityDetector) -> None:
        """Report severity distribution of detected injections."""
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "NOT_DETECTED": 0}

        for text, _, _, _ in PUBLISHED_INJECTIONS:
            findings = detector.scan(text)
            if findings:
                severity_counts[findings[0]["severity"]] += 1
            else:
                severity_counts["NOT_DETECTED"] += 1

        total = len(PUBLISHED_INJECTIONS)
        print(f"\n{'='*70}")
        print("SEVERITY DISTRIBUTION")
        print(f"{'='*70}")
        print(f"  HIGH:         {severity_counts['HIGH']:>3} ({severity_counts['HIGH']/total:.1%})")
        print(
            f"  MEDIUM:       {severity_counts['MEDIUM']:>3} ({severity_counts['MEDIUM']/total:.1%})"
        )
        print(
            f"  NOT_DETECTED: {severity_counts['NOT_DETECTED']:>3} ({severity_counts['NOT_DETECTED']/total:.1%})"
        )
