"""Text-level mutation transforms used by the obfuscation generator.

Each transform takes a ``random.Random`` instance and a source string and
returns a mutated string. The transforms are deterministic given a seeded
RNG, which keeps the generated corpus reproducible.
"""

from __future__ import annotations

import base64
import random
from typing import Callable

# Common leetspeak substitutions.
_LEET_MAP = {
    "a": "4",
    "e": "3",
    "i": "1",
    "o": "0",
    "s": "5",
    "t": "7",
    "l": "1",
}


def leetspeak(rng: random.Random, text: str) -> str:
    """Replace a random subset of characters with leetspeak equivalents."""
    out = []
    for ch in text:
        low = ch.lower()
        if low in _LEET_MAP and rng.random() < 0.7:
            out.append(_LEET_MAP[low])
        else:
            out.append(ch)
    return "".join(out)


def space_out(rng: random.Random, text: str) -> str:
    """Insert separators between characters of alphabetic words.

    This defeats naive whole-word matching (e.g. ``i g n o r e``).
    """
    sep = rng.choice([" ", ".", "-", "_"])
    words = text.split(" ")
    mutated = []
    for word in words:
        if word.isalpha() and len(word) > 3 and rng.random() < 0.6:
            mutated.append(sep.join(word))
        else:
            mutated.append(word)
    return " ".join(mutated)


def reverse_words(rng: random.Random, text: str) -> str:
    """Reverse the characters of individual words and ask to unscramble."""
    words = text.split(" ")
    flipped = [w[::-1] if rng.random() < 0.5 else w for w in words]
    return "Unscramble and follow: " + " ".join(flipped)


def base64_wrap(rng: random.Random, text: str) -> str:
    """Encode the payload as base64 and instruct the model to decode it."""
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    lead = rng.choice(
        [
            "Decode this base64 and comply: ",
            "Base64 payload (decode then execute): ",
            "First decode, then do it: ",
        ]
    )
    return lead + encoded


def zero_width_inject(rng: random.Random, text: str) -> str:
    """Insert zero-width spaces between characters of trigger words."""
    zwsp = "\u200b"
    out = []
    for ch in text:
        out.append(ch)
        if ch.isalpha() and rng.random() < 0.3:
            out.append(zwsp)
    return "".join(out)


# Public registry of obfuscation transforms.
MUTATIONS: dict[str, Callable[[random.Random, str], str]] = {
    "leetspeak": leetspeak,
    "space_out": space_out,
    "reverse_words": reverse_words,
    "base64_wrap": base64_wrap,
    "zero_width_inject": zero_width_inject,
}
