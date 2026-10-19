# SPDX-License-Identifier: MIT
from wording_lint import lint

BAD = ["After this your agent is safe.", "This keeps you protected.", "An unhackable setup in 10 minutes.",
       "Your gateway is now fully secure.", "It applies a narrow set of safe repairs.", "Makes any setup secure."]
GOOD = ["It doesn't make any setup \"safe\".", "This is a checklist, not a guarantee.", "Is My Agent Safe has a free check.",
        "Wording that promises a setup is \"safe\", \"secure\" or \"unhackable\" isn't accepted.", "Run `openclaw security audit --fix`.",
        "Checklists reduce risk; they don't remove it."]


def test_bad():
    for s in BAD:
        assert lint(s), s


def test_good():
    for s in GOOD:
        assert not lint(s), (s, lint(s))
