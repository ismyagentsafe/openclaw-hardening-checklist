#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wording lint: the checklist never promises that a setup is safe/secure/protected/unhackable.
Usage: python3 scripts/wording_lint.py [files...]   (default: every *.md in the repo). Exit 1 on any finding.

Rules (same spirit as Is My Agent Safe's site lint):
- a claim like "is/are/you're/it's/makes it/keeps you ... safe|secure|protected" is an error unless the same
  sentence negates it ("doesn't make any setup safe", "not a guarantee");
- absolute words are errors anywhere: unhackable, bulletproof, hack-proof, 100% secure, fully secure, guaranteed safe;
- the bare word "safe" (outside the brand name "Is My Agent Safe", negations, quotes like "safe", and code) is an error,
  so wording such as "safe repairs" gets reworded.
"""
import re
import sys
from pathlib import Path

CLAIM = re.compile(r"\b(?:is|are|was|be|been|being|stays?|remains?|now|it'?s|you'?re|they'?re|keeps?\s+(?:it|you|your\s+\w+)|"
                   r"makes?\s+(?:it|you|your\s+\w+|any\s+\w+))\s+(?:(?:now|fully|completely|totally|perfectly|truly|still|very|100%)\s+)*"
                   r"[\"“']?(safe|secure|protected)\b", re.I)
ABSOLUTE = re.compile(r"\b(unhackable|bullet-?proof|hack-?proof|100%\s+secure|fully\s+secure|guaranteed\s+(?:safe|secure))\b", re.I)
NEGATION = re.compile(r"\b(?:not|never|no|can'?t|cannot|won'?t|isn'?t|aren'?t|doesn'?t|don'?t|without|whether|nor|neither|promis(?:e|es|ed|ing)|guarantee[sd]?)\b|n't\b", re.I)
BRAND = re.compile(r"is\s+my\s+agent\s+safe", re.I)
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
QUOTED = re.compile(r"[\"“]\s*(?:safe|secure|unhackable)\s*[\"”]", re.I)


def sentences(text):
    return re.split(r"(?<=[.!?])\s+|\n\s*\n|\n\s*[-*]\s", text)


def lint(text: str) -> list[str]:
    text = BRAND.sub("BRAND", CODE.sub(" CODE ", text))
    bad = []
    for s in sentences(text):
        one = " ".join(s.split())
        if ABSOLUTE.search(one) and not NEGATION.search(one):
            bad.append(one)
            continue
        if CLAIM.search(one) and not NEGATION.search(one):
            bad.append(one)
            continue
        bare = QUOTED.sub(" ", one)
        if re.search(r"\bsafe\b", bare, re.I) and not NEGATION.search(bare):
            bad.append(one)
    return bad


def main(argv):
    root = Path(__file__).resolve().parent.parent
    files = [Path(a) for a in argv] or sorted(p for p in root.rglob("*.md") if "node_modules" not in p.parts)
    errors = 0
    for f in files:
        for b in lint(f.read_text(encoding="utf-8")):
            errors += 1
            print(f"{f.relative_to(root) if f.is_absolute() else f}: wording: {b[:160]}")
    print(f"wording lint: {errors} problem(s) in {len(files)} file(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
