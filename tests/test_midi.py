"""MIDI: the functions write the `midi` command of synths.js (its docs/midi.md), and what the page hands back
calls the program's functions. No device is involved: a host takes the commands, and the events are handed in."""
import json
import sys
import textwrap

import pytest

import synths
from synths import *
from conftest import ROOT, of_synths_js

PYCTURES = ROOT.parent / "pyctures" / "src"


def midi(sent):
    return [{k: v for k, v in c.items() if k != "op"} for c in sent if c["op"] == "midi"]


def test_every_midi_name_of_synths_js_has_its_python_spelling():
    names = synths._NAMES["midi"]
    for name in names["functions"]:
        assert callable(getattr(synths, synths._snake(name), None)), name
        assert synths._snake(name) in synths.__all__, name
    for name in names["synthFunctions"]:
        assert callable(getattr(synths.Synth, synths._snake(name), None)), name
    assert [synths._snake(n) for n in names["functions"] if n.startswith("onMidi")] == list(synths._MIDI_HOOKS)


def test_what_is_written_is_the_midi_command(sent):
    does = set(synths._NAMES["midi"]["does"])
    lead = make_synth("lead")
    lead.play_from_midi()
    lead.play_from_midi(channel=2, vibrato=1)
    lead.play_from_midi(False)
    lead.send_to_midi(channel=10, output="Minilogue")
    lead.send_to_midi(False)
    lead.map_midi(74, "cutoff")
    lead.learn("resonance", min=0.1, max=0.5, channel=3)
    lead.unmap_midi("cutoff")
    lead.unmap_midi()
    send_midi_note("C4")
    send_midi_clock()
    set_tempo(90)
    send_midi_clock(False)
    use_midi_input("Keystation 49")
    use_midi_input(["a", "b"])
    use_midi_input()
    use_midi_output("Minilogue")
    midi_devices()
    on_midi(lambda m: None)
    stop_midi()
    got = midi(sent)
    assert {c["do"] for c in got} == does, "every `do` there is, and no other"
    json.loads(json.dumps(sent.batches, allow_nan=False))
    by = lambda do: [c for c in got if c["do"] == do]
    assert by("play") == [{"do": "play", "id": "s1", "vibrato": [0.15, 0.5]}, {"do": "play", "id": "s1", "vibrato": [0.15, 1], "channel": 2},
                          {"do": "play", "id": "s1", "on": False}]
    assert by("through") == [{"do": "through", "id": "s1", "channel": 10, "note": 60, "output": "Minilogue"}, {"do": "through", "id": "s1", "on": False}]
    # A knob goes through the setting's whole range; one in Hz that spans a hundred times or more moves by ratio.
    assert by("map") == [{"do": "map", "id": "s1", "setting": "cutoff", "min": 20, "max": 20000, "kind": "float", "curve": "exp", "control": 74}]
    assert by("learn") == [{"do": "learn", "id": "s1", "setting": "resonance", "min": 0.1, "max": 0.5, "kind": "float", "curve": "lin", "channel": 3}]
    assert by("unmap") == [{"do": "unmap", "id": "s1", "setting": "cutoff"}, {"do": "unmap", "id": "s1"}]
    clocks = by("clock")
    assert [(c.get("on"), c["bpm"]) for c in clocks] == [(True, 120), (None, 90), (False, 90)], "a clock being sent follows set_tempo"
    assert [c["name"] for c in by("input")] == ["Keystation 49", ["a", "b"], None] and by("output")[0]["name"] == "Minilogue"
    assert len(by("devices")) == 1 and len(by("listen")) == 1 and len(by("stop")) == 1


def test_sends_carry_the_right_bytes_at_the_right_times(sent):
    t0 = sound_time()
    send_midi_note("C4", 0.8, length=0.5, at=t0 + 1)
    send_midi_note("E4", 1, "quarter", channel=10, output="Drums", at=t0)
    send_midi_note(["C4", "E4"], 0.001, None, at=t0)
    send_midi_note("G9", 0, at=t0)
    send_midi_note_off("C4", channel=2, at=t0 + 3)
    send_midi_control(74, 0.5, at=t0)
    send_midi_bend(-1, at=t0)
    send_midi_bend(1, channel=16, at=t0)
    send_midi_bend(0, at=t0)
    send_midi_program(5, after=2)
    send_midi([0xF0, 1, 2, 0xF7], beat=4)
    got = midi(sent)
    assert all(c["do"] == "send" for c in got)
    what = [(c["bytes"], round(c["t"] - t0, 6)) for c in got]
    assert what[:10] == [
        ([0x90, 60, 102], 1), ([0x80, 60, 0], 1.5),              # a note-on, and its note-off `length` later
        ([0x99, 64, 127], 0), ([0x89, 64, 0], 0.5),              # a quarter at 120 beats a minute, on channel 10
        ([0x90, 60, 1], 0), ([0x90, 64, 1], 0),                  # a chord held: velocity never 0, and no note-off
        ([0x80, 127, 0], 0),                                     # velocity 0 is a note-off, now
        ([0x81, 60, 0], 3),
        ([0xB0, 74, 64], 0),
        ([0xE0, 0, 0], 0)]
    assert what[10][0] == [0xEF, 127, 127] and what[11][0] == [0xE0, 0, 64]
    assert what[12][0] == [0xC0, 5] and 1.99 < what[12][1] < 2.1
    assert what[13][0] == [0xF0, 1, 2, 0xF7]
    assert [c.get("output") for c in got[:4]] == [None, None, "Drums", "Drums"]


def test_the_bytes_are_the_ones_synths_js_writes():
    """The examples in synths.js's docs/midi.md, byte for byte."""
    text = of_synths_js("docs/midi.md")
    if text is None:
        pytest.skip("synths.js is not beside this repository")
    assert '{ op: "midi", do: "send", bytes: [144, 60, 102]' in text and "bytes: [128, 60, 0]" in text
    got = []
    synths.connect(got.append)
    try:
        send_midi_note("C4")
    finally:
        synths.connect(None)
    assert [c["bytes"] for b in got for c in b["cmds"]] == [[144, 60, 102], [128, 60, 0]]


def test_the_program_s_functions_are_called_with_decoded_values(sent):
    heard = []
    on_midi_note(lambda note, velocity, channel: heard.append(("note", note, velocity, channel)))
    on_midi_control(lambda number, value: heard.append(("control", number, value)))       # fewer arguments is right too
    on_midi(lambda m: heard.append(("all", m.type, m.note, m.time, m.device, m["data"] if "data" in m else None)))
    on_midi_devices(lambda d: heard.append(("devices", d)))
    assert [c["do"] for c in midi(sent)] == ["listen", "devices"], "listening is asked for once, and the devices once"
    assert midi_devices() == {"inputs": [], "outputs": [], "available": None}, "nothing is known until the page has answered"
    receive_midi([
        {"type": "devices", "inputs": ["Keys"], "outputs": ["Box"], "available": True},
        {"type": "noteOn", "channel": 2, "note": 60, "velocity": 0.5, "time": 12.5, "device": "Keys", "data": [0x91, 60, 64]},
        {"type": "noteOff", "channel": 2, "note": 60, "velocity": 0, "release": 0.25, "time": 12.75},
        {"type": "control", "channel": 1, "control": 74, "value": 0.25},
    ])
    assert heard == [
        ("devices", {"inputs": ["Keys"], "outputs": ["Box"], "available": True}), ("all", "devices", None, None, None, None),
        ("note", 60, 0.5, 2), ("all", "noteOn", 60, 12.5, "Keys", [0x91, 60, 64]),
        ("note", 60, 0, 2), ("all", "noteOff", 60, 12.75, None, None),          # a key coming up is velocity 0
        ("control", 74, 0.25), ("all", "control", None, None, None, None)]
    assert midi_devices() == {"inputs": ["Keys"], "outputs": ["Box"], "available": True}
    late = []
    on_midi_devices(late.append)
    assert late == [midi_devices()], "one who asks after they are known is told at once"
    del heard[:]
    ups = []
    on_midi_note_off(lambda note, channel: ups.append((note, channel)))
    receive_midi({"type": "noteOff", "channel": 3, "note": 62, "velocity": 0})
    assert ups == [(62, 3)] and [h[0] for h in heard] == ["all"], "with on_midi_note_off, a key coming up goes there instead"
    stop_midi()
    receive_midi({"type": "noteOn", "channel": 1, "note": 60, "velocity": 1})
    assert [h[0] for h in heard] == ["all"] and midi(sent)[-1]["do"] == "stop", "stop_midi forgets every function"


def test_a_knob_that_turned_a_setting_on_the_page_is_remembered_here(sent):
    lead = make_synth("lead", wave="saw")
    turned = []
    lead.learn("cutoff", lambda value, setting: turned.append((value, setting)))
    lead.map_midi(1, "wave")
    lead.map_midi(2, "vibrato_rate")
    receive_midi([{"type": "learned", "id": "s1", "setting": "cutoff", "control": 21, "channel": 1},
                  {"type": "set", "id": "s1", "setting": "cutoff", "value": 632.5, "control": 21},
                  {"type": "set", "id": "s1", "setting": "wave", "value": 2, "control": 1},       # a choice arrives as its number
                  {"type": "set", "id": "s1", "setting": "vibrato_rate", "value": 7.5, "control": 2},
                  {"type": "set", "id": "s9", "setting": "cutoff", "value": 1, "control": 21}])   # another program's: not ours
    assert lead.cutoff == 632.5 and turned == [(632.5, "cutoff")]
    assert lead.wave == synths._setting("wave")["choices"][2] and lead.vibrato_rate == 7.5
    assert not [c for c in sent if c["op"] == "set"], "the page has already set it: Python writes nothing back"
    lead.unmap_midi("cutoff")
    receive_midi({"type": "set", "id": "s1", "setting": "cutoff", "value": 100, "control": 21})
    assert lead.cutoff == 632.5


def test_no_midi_is_said_once_and_nothing_is_raised(sent, capsys):
    synths._said.clear()
    seen = []
    on_midi_devices(seen.append)
    lead = make_synth("lead")
    lead.play_from_midi()
    for _ in range(3):
        receive_midi({"type": "devices", "inputs": [], "outputs": [], "available": False})
        send_midi_note("C4")
        use_midi_output("Minilogue")
    err = capsys.readouterr().err
    assert err.count("there is no MIDI here") == 1 and "\n" == err[-1] and err.count("\n") == 1, err
    assert seen[-1] == {"inputs": [], "outputs": [], "available": False} and midi_devices()["available"] is False


MISTAKES = [
    (lambda: send_midi_note(), 'send_midi_note needs a note, as in send_midi_note("C4")'),
    (lambda: send_midi_note("C4", channel=17), "send_midi_note: channel needs a whole number from 1 to 16, not 17"),
    (lambda: send_midi_note("C12"), 'MIDI has the notes 0 to 127 ("C-1" to "G9")'),
    (lambda: send_midi_note("C4", length="long"), "send_midi_note: the length needs a number, or a note length by name"),
    (lambda: send_midi_control(128, 0.5), "send_midi_control needs the number of a control, a whole number from 0 to 127, not 128"),
    (lambda: send_midi_control(7, "loud"), "send_midi_control: the value needs a number from 0 to 1"),
    (lambda: send_midi([60, 100]), "send_midi needs the bytes of a MIDI message, beginning with its status byte"),
    (lambda: on_midi_note("C4"), "on_midi_note needs a function to call"),
    (lambda: make_synth().learn("cutof"), 'learn: there is no setting called "cutof". Did you mean "cutoff"?'),
    (lambda: make_synth().learn(74), 'learn needs the name of a setting, as in lead.learn("cutoff"), not 74'),
    (lambda: make_synth().map_midi("cutoff", 74), 'map_midi needs the number of a knob or slider, from 0 to 119'),
    (lambda: make_synth().play_from_midi(channel=0), "play_from_midi: channel needs a whole number from 1 to 16, not 0"),
    (lambda: use_midi_output(3), "use_midi_output needs the name of a MIDI device"),
]


@pytest.mark.parametrize("call, said", MISTAKES, ids=[m[1][:40] for m in MISTAKES])
def test_a_mistake_is_said_in_plain_words(sent, call, said):
    with pytest.raises(ValueError) as e:
        call()
    assert said in str(e.value)
    assert not midi(sent), "and nothing was written"


# ---------------------------------------------------------------- in a Pyctures scene

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


def calls(reply, handle=10):
    return [c for c in json.loads(reply)["cmds"] if c[0] == "call" and c[3] == handle]


def test_in_a_scene_midi_rides_the_frame_and_comes_back_with_the_next(pyctures):
    scene = textwrap.dedent('''
        from synths import *
        lead = make_synth("lead")
        lead.play_from_midi()
        lead.learn("cutoff")
        got = []
        on_midi_note(lambda note, velocity, channel: got.append((note, velocity, channel)))
        def update(dt):
            if got:
                print(got.pop(0), lead.cutoff)
    ''')
    first = calls(pyctures.start(scene, "{}"))
    assert [c[4] for c in first] == ["send", "midi"], "one batch, and one call that asks the page for what its desk says"
    batch = first[0][5][0]
    assert [(c["op"], c.get("do")) for c in batch["cmds"]] == [("synth", None), ("midi", "play"), ("midi", "learn"), ("midi", "listen")]
    listener = first[1][5][0]["$cb"]
    events = [{"type": "set", "id": "s1", "setting": "cutoff", "value": 440, "control": 21},
              {"type": "noteOn", "channel": 1, "note": 64, "velocity": 0.5, "time": 3.25}]
    reply = json.loads(pyctures.tick(json.dumps({"events": [{"k": "cb", "id": listener, "e": {"midi": json.dumps(events)}}]})))
    assert reply["out"] == "(64, 0.5, 1) 440\n" and not reply["error"], reply
    assert calls(json.dumps(reply)) == [], "nothing is written back for what the page has already done"
