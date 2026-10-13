"""The names are those of synths.js: its synths-names.json is carried inside the module."""
import json
import re

import pytest

import synths
from conftest import ROOT, of_synths_js


def test_the_names_are_those_of_synths_js():
    """Fails while the two differ: run scripts/sync_names.py."""
    names = of_synths_js("synths-names.json")
    if names is None:
        pytest.skip("synths.js is not beside this repository")
    assert synths._NAMES == json.loads(names), "run: python scripts/sync_names.py"


def test_every_function_of_synths_js_has_its_python_spelling():
    text = of_synths_js("synths.js")
    if text is None:
        pytest.skip("synths.js is not beside this repository")
    # The Python spellings synths.js itself exports: `playSound as play_sound, …`.
    spelled = set(re.findall(r"\b\w+ as ([a-z_]+)\b", text[text.rindex("export {"):]))
    hosts = {"create_sound", "render_sound", "pack_song", "create_stepped_player"}        # for a host's page: Python has connect()
    missing = sorted(n for n in spelled - hosts if not callable(getattr(synths, n, None)))
    assert not missing, "synths.js has these and Python does not: %s" % missing
    for name in ("beats", "beat"):
        assert callable(getattr(synths, name))


def test_every_name_in_the_table_is_understood():
    names = synths._NAMES
    lead = synths.Synth(None, "s", {}, 60, 0.3)
    friendly = {synths._key(alias) for alias in names["names"]}
    for s in names["settings"]:
        if synths._key(s["name"]) in friendly:
            continue       # a friendly name that is also the engine's name for something else is the friendly one
        assert synths._setting(s["name"])["id"] == s["id"]
        assert lead.describe(s["name"])["kind"] == s["kind"]
    for alias, to in names["names"].items():
        entry = synths._setting(synths._snake(alias))
        assert entry is not None and entry["name"] == to["setting"] and entry["scale"] == to["scale"]
    # Every ready-made synth and sound is made of settings that exist, with values they can take.
    for name, patch in list(names["synths"].items()) + [(n, s["patch"]) for n, s in names["sounds"].items()]:
        synths._patch_of(patch, name, strict=True)
        synths._check_macro(patch.get("macro"), name)
    assert synths.sound_names() == list(names["sounds"])
    assert "sample" not in synths.synth_names() and "chip_lead" in synths.synth_names()
    assert "vibrato_rate" in synths.setting_names() and "cutoff" in synths.setting_names()


def test_a_setting_is_one_name_however_it_is_written():
    for written in ("vibrato_rate", "vibratoRate", "lfo1.rate", "lfo1_rate", "LFO1Rate"):
        assert synths._setting(written)["name"] == "lfo1.rate"


def test_the_version_is_the_package_s():
    toml = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^version = "([^"]+)"', toml, re.M).group(1) == synths.__version__
