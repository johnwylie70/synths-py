"""Every Python program in the README runs, and writes commands."""
import re

import pytest

import synths
from conftest import ROOT

README = (ROOT / "README.md").read_text(encoding="utf-8")
BLOCKS = [re.sub(r"(?m)^  ", "", b) if b.startswith("  ") else b for b in re.findall(r"```python\n(.*?)\s*```", README, re.S)]
# These are parts of a Pyctures scene: they are run there, in Pyctures' own tests.
SCENES = ("Sprite(", "from pydials", "star.touches")


@pytest.mark.parametrize("code", [b for b in BLOCKS if not any(s in b for s in SCENES)],
                         ids=lambda b: b.strip().splitlines()[-1][:40])
def test_a_program_in_the_readme_runs(sent, code, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    synths._said.clear()
    names = {}
    exec("from synths import *\nlead = make_synth('lead')\n", names)
    before = len(sent)
    exec(code, names)
    assert len(sent) > before, "it wrote no command"


def test_the_readme_names_every_sound_and_synth():
    for name in synths.sound_names() + synths.synth_names():
        assert "`%s`" % name in README, "%s is not in the README" % name
