"""How the commands travel: in a Pyctures scene, to a host, and from a program started with plain Python."""
import json
import os
import subprocess
import sys
import textwrap

import pytest

import synths
from conftest import ROOT

PYCTURES = ROOT.parent / "pyctures" / "src"


@pytest.fixture
def pyctures():
    try:
        import pyctures
    except ImportError:
        if not PYCTURES.exists():
            pytest.skip("Pyctures is not installed, nor beside this repository")
        sys.path.append(str(PYCTURES))
        import pyctures
    yield pyctures
    pyctures.stop()


def sound_calls(reply, handle=10):
    return [c for c in json.loads(reply)["cmds"] if c[0] == "call" and c[3] == handle]


def test_in_a_scene_a_frame_s_sounds_are_one_command_in_the_frame(pyctures):
    scene = textwrap.dedent('''
        from synths import *
        lead = make_synth("lead")
        lead.play("C4")
        play_sound("coin")
        n = 0
        def update(dt):
            global n
            n += 1
            if n == 3:
                play_sound("jump")
                lead.cutoff = 500
        def on_key_down(key):
            play_sound("laser")
        def draw():
            circle(10, 10, 5, "red")
    ''')
    first = sound_calls(pyctures.start(scene, "{}"))
    assert len(first) == 1, "the top of the file is one batch, sent with the first reply"
    kind, line, new, handle, name, args = first[0]
    assert (name, new, line) == ("send", 0, 3), "the batch is one call of send() on the fixed handle, from the scene's line"
    batch = args[0]
    assert [c["op"] for c in batch["cmds"]] == ["synth", "note", "sound"]
    assert batch["synths"] == 1 and batch["now"] >= batch["cmds"][-1]["t"]
    assert sound_calls(pyctures.tick("{}")) == [], "a frame with no sound carries nothing for it"
    second = sound_calls(pyctures.tick("{}"))
    assert [c["op"] for c in second[0][5][0]["cmds"]] == ["sound", "set"]
    # A key press is inside the next call from the page, and its sound goes with that call's reply.
    press = {"events": [{"k": "input", "e": {"type": "keydown", "key": "a", "code": "KeyA"}}]}
    third = sound_calls(pyctures.tick(json.dumps(press)))
    assert [c["name"] for c in third[0][5][0]["cmds"]] == ["laser"]


def test_in_a_scene_that_is_recorded_the_sound_clock_is_the_video_s(pyctures):
    """A recorder gives the scene one frame at a time and says what time it is (vt). Every time the library
    reads or writes is that time, however long the frames really took."""
    scene = textwrap.dedent('''
        from synths import *
        lead = make_synth("lead")
        set_tempo(120)
        seen = []
        def update(dt):
            seen.append((sound_time(), beat()))
            lead.play("C4", after=0.5)
            print(sound_time(), beat())
    ''')
    if not hasattr(pyctures.S, "vt"):
        pytest.skip("this Pyctures has no stepped clock")
    first = json.loads(pyctures.start(scene, json.dumps({"width": 400, "height": 300, "pixel_ratio": 1, "vt": 0.0})))
    assert first["error"] is None, first["error"]
    made = sound_calls(json.dumps(first))[0][5][0]
    assert made["now"] == 0.0 and all(c["t"] in (0.0, 0.5) for c in made["cmds"])
    for n in (1, 2, 3):
        reply = pyctures.tick(json.dumps({"dt": 1 / 30, "vt": n / 30}))
        batch = sound_calls(reply)[0][5][0]
        assert batch["now"] == n / 30
        assert [c["t"] for c in batch["cmds"]] == [n / 30 + 0.5]
        said = json.loads(reply)["out"].split()
        assert float(said[0]) == n / 30 and abs(float(said[1]) - n / 15) < 1e-12


def test_a_synth_s_page_is_the_page_s_object_for_it(pyctures):
    reply = pyctures.start('from synths import *\nlead = make_synth("lead")\nprint(type(lead.page).__name__)\nsame = lead.page', "{}")
    d = json.loads(reply)
    assert d["out"] == "JsRef\n", d
    calls = [c for c in d["cmds"] if c[0] == "call" and c[3] == 10]
    assert [c[4] for c in calls] == ["send", "synth"], "the synth is made before the page is asked for its object"
    assert calls[1][5] == ["s1"] and calls[1][2] > 1000


def test_each_run_starts_with_nothing_made(pyctures):
    scene = 'from synths import *\nplay_note("C4")'
    for _ in range(2):
        batch = sound_calls(pyctures.start(scene, "{}"))[0][5][0]
        assert [c["id"] for c in batch["cmds"]] == ["s1", "s1"]


def test_a_host_is_handed_each_command_at_once():
    got = []
    synths.connect(got.append, ids="a:")
    try:
        synths.play_sound("coin")
        assert len(got) == 1 and got[0]["cmds"][0]["name"] == "coin"
        synths.make_synth("bass")
        assert got[1]["cmds"][0]["id"] == "a:s1"
    finally:
        synths.connect(None)


def run_plainly(tmp_path, with_pyctures, env=None):
    (tmp_path / "tune.py").write_text('from synths import *\nprint("before")\nplay_notes("C4 E4 G4")\nplay_sound("coin")\nprint("after")\n')
    path = [str(ROOT / "src")]
    if with_pyctures:
        # A stand-in for the pyctures command, which says what it was asked to do.
        fake = tmp_path / "lib" / "pyctures"
        fake.mkdir(parents=True)
        (fake / "__init__.py").write_text("")
        (fake / "__main__.py").write_text("import sys, os\nprint('PYCTURES', sys.argv[1], os.path.basename(sys.argv[2]))\n")
        path.append(str(tmp_path / "lib"))
    full = dict(os.environ, PYTHONPATH=os.pathsep.join(path), **(env or {}))
    return subprocess.run([sys.executable, "-S", "tune.py"], cwd=tmp_path, env=full, capture_output=True, text=True, timeout=30)


def test_plain_python_opens_the_program_with_pyctures(tmp_path):
    done = run_plainly(tmp_path, with_pyctures=True)
    assert done.returncode == 0
    assert "PYCTURES run tune.py" in done.stdout, "it was started again with pyctures run"
    assert "after" not in done.stdout, "and did not carry on as well"
    assert "pyctures run tune.py" in done.stderr and "web browser" in done.stderr


def test_plain_python_without_pyctures_says_how_to_run_it_and_carries_on(tmp_path):
    done = run_plainly(tmp_path, with_pyctures=False)
    assert done.returncode == 0 and "after" in done.stdout
    assert done.stderr.count("pip install pyctures") == 1 and "pyctures run tune.py" in done.stderr
    quiet = run_plainly(tmp_path, with_pyctures=True, env={"SYNTHS_NO_BROWSER": "1"})
    assert "after" in quiet.stdout and "PYCTURES" not in quiet.stdout and "pyctures run tune.py" in quiet.stderr
