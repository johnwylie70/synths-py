"""What the functions write is the command format of synths.js (its docs/commands.md), and nothing else."""
import json
import math

import pytest

import synths
from synths import *

NUMBER = (int, float)
NOTES = (list, type(None))
# op -> {field: the types it may have}. `t` may be on every command.
FORMAT = {
    "synth": {"id": str, "preset": str, "set": dict, "macro": (list, dict, type(None))},
    "macro": {"id": str, "macro": (list, dict, type(None))},
    "set": {"id": str, "set": dict, "glide": NUMBER},
    "note": {"id": str, "note": NOTES, "len": NUMBER + (type(None),), "vel": NUMBER, "pan": NUMBER, "h": int, "arp": dict},
    "off": {"id": str, "h": int, "note": list, "cut": bool},
    "voice": {"id": str, "h": int, "pitch": NUMBER, "freq": NUMBER, "glide": NUMBER, "vol": NUMBER, "pan": NUMBER, "kill": bool, "arp": (dict, type(None))},
    "sound": {"name": str, "vol": NUMBER, "pitch": NUMBER, "pan": NUMBER, "len": NUMBER},
    "tempo": {"bpm": NUMBER},
    "sample": {"id": str, "url": str, "bytes": str, "note": NUMBER, "loop": (bool, list), "pingpong": bool, "name": str},
    "tune": {"id": str, "synth": str, "steps": list, "length": NUMBER, "repeat": (bool, int, float), "beats": bool},
    "stop": {"id": str},
    "master": {"volume": NUMBER, "mute": bool, "set": dict},
    "free": {"id": str},
    "song": {"id": str, "do": str, "url": str, "bytes": str, "name": str, "repeat": bool, "vol": NUMBER, "raw": bool,
             "patches": dict, "files": dict, "order": int, "row": int},
}
NEEDS = {"synth": ["id"], "set": ["id", "set"], "note": ["id"], "off": ["id"], "voice": ["id", "h"], "sound": ["name"],
         "sample": ["id"], "tune": ["id", "synth", "steps"], "free": ["id"], "song": ["do"], "macro": ["id", "macro"], "tempo": ["bpm"]}


def check(batch):
    assert set(batch) == {"synths", "now", "cmds"} and batch["synths"] == 1
    assert isinstance(batch["now"], float)
    json.loads(json.dumps(batch, allow_nan=False))          # plain data
    for c in batch["cmds"]:
        fields = FORMAT[c["op"]]
        for name, value in c.items():
            if name == "op":
                continue
            if name == "t":
                assert isinstance(value, NUMBER) and math.isfinite(value) and value <= batch["now"] + 3600
                continue
            assert name in fields, "%s has no field %r" % (c["op"], name)
            assert isinstance(value, fields[name]), "%s.%s is %r" % (c["op"], name, value)
        if isinstance(c.get("arp"), dict):
            arp = c["arp"]
            assert set(arp) == {"offsets", "rate", "order"} and len(arp["offsets"]) <= 8
            assert all(isinstance(v, int) for v in arp["offsets"]) and arp["order"] in (0, 1, 2, 3, 4)
        for name in NEEDS.get(c["op"], ()):
            assert name in c, "%s without %s" % (c["op"], name)


def test_everything_the_library_writes_is_in_the_format(sent, tmp_path):
    wav = tmp_path / "kick.wav"
    wav.write_bytes(b"RIFF....WAVE")
    play_sound("laser")
    play_sound("coin", 0.5, pitch=3, pan=-1, after=0.5)
    play_sound("win", length="half", after="quarter")
    note("C4", "quarter")
    chord("Cm", "half")
    rest("eighth")
    with loop_notes(2):
        note("C4", "eighth")
        rest()
    start_lines(after=1)
    play_note("C4")
    play_note(["C4", "E4", 67.5], 2, 0.3, pan=1, at=sound_time() + 1)
    tune = play_notes("C4 E4 - G4:2 C4+E4", 0.25, repeat=True, volume=0.5, hold=0.5)
    tune.stop()
    lead = make_synth("lead", cutoff=1200)
    lead.play("E4", 0.5)
    lead.play()
    lead.cutoff = 800
    lead.set(cutoff=4000, resonance=0.4, slide=2)
    lead.set("wave", "square")
    held = lead.start("C4", 0.5)
    held.slide_to("G4", 0.5)
    held.pitch = "A4"
    held.volume = 0.5
    held.pan = -1
    held.frequency = 440
    held.cut()
    held.stop()
    lead.note_on(60, 0.7)
    lead.note_off(60)
    lead.stop("E4")
    lead.stop()
    lead.play_notes(["C4", None, ["C4", "E4"]], repeat=3)
    lead.play("Cm7", 1)
    lead.arp("Cm7")
    arp = lead.start_arp("A3", "minor", speed=30, order="up-down", volume=0.5)
    arp.change("F")
    arp.speed = 20
    arp.stop()
    play_arp("C4", "major", 1)
    start_arp(["C4", "E4", "G4"]).stop()
    lead.set_macro([{"wave": "noise", "pitch": 24}, {"wave": "square"}, {"pitch": -5, "volume": 0.8}])
    lead.macro = None
    make_synth("chip", macro={"steps": [{"width": 0.1}, {"width": 0.9}], "loop": True, "slide": True})
    main_synth().cutoff = 900
    sound_output().set("volume", 0.8)
    sound_output().set("echo_time", 0.2)
    lead.remove()
    make_synth(wave="saw", attack=0.2)
    make_synth({"wave": "triangle"})
    drum = load_sample(str(wav), note="A3", loop=True, reverb=0.3)
    drum.play()
    drum.play("E4", 2)
    load_sample("not_here.wav").play()
    song = play_song("tune.mod", volume=0.5, repeat=False, raw=True, patches={"wobble": "bass", "pling": {"preset": "chip_lead", "echo": 0.4}})
    song.pause(), song.resume(), song.seek(2, 16), song.stop()
    song.volume = 0.5
    song.repeat = True
    play_song(b"M.K.")
    stop_song()
    set_volume(0.5)
    mute_sound()
    unmute_sound()
    set_effects(echo_time=0.3, echo_feedback=0.5, echo_bounce=True, reverb_size=0.8)
    set_tempo(90)
    lead.play("C4", beats(1), beat=8)
    stop_sound()
    for batch in sent.batches:
        check(batch)
    assert {c["op"] for c in sent} == set(FORMAT), "an op of the format was never written"


def test_ids_are_chosen_here_and_times_are_when_the_call_was_made(sent):
    before = sound_time()
    play_note("C4")
    lead = make_synth("bass")
    lead.play("C2", after=0.5)
    after = sound_time()
    assert [c["id"] for c in sent] == ["s1", "s1", "s2", "s2"]
    assert sent[0] == {"op": "synth", "id": "s1", "preset": "keys", "t": sent[0]["t"]}
    assert sent[1]["note"] == [60] and sent[1]["len"] == 0.5
    assert before <= sent[0]["t"] <= sent[1]["t"] <= sent[2]["t"] <= after
    assert before + 0.5 <= sent[3]["t"] <= after + 0.5
    assert sent[3]["note"] == [36]


def test_a_tune_is_steps_in_seconds(sent):
    play_notes("C4 E4 - G4:2 C4+E4", 0.25, repeat=True)
    tune = sent[-1]
    assert tune["steps"] == [[0, [60], 0.225, 0.8], [0.25, [64], 0.225, 0.8], [0.75, [67], 0.45, 0.8], [1.25, [60, 64], 0.225, 0.8]]
    assert tune["length"] == 1.5 and tune["repeat"] is True and tune["synth"] == "s1" and "beats" not in tune
    # With no step, or a step by name, a tune is in beats: the player keeps it to the tempo, also when that changes.
    play_notes("C4 D4:q E4:2 -:e F4")
    assert sent[-1]["beats"] is True and sent[-1]["repeat"] == 1 and sent[-1]["length"] == 3.5
    assert [(s[0], s[2]) for s in sent[-1]["steps"]] == [(0, 0.45), (0.5, 0.9), (1.5, 0.9), (3, 0.45)]
    play_notes("C4 D4", "sixteenth")
    assert sent[-1]["steps"][1][0] == 0.25 and sent[-1]["beats"] is True
    set_tempo(90)
    assert sent[-1] == {"op": "tempo", "bpm": 90, "t": sent[-1]["t"]}
    play_notes("C4:q D4", 0.5)            # in seconds, a quarter note is as long as it is at this tempo
    assert sent[-1]["steps"][1][0] == pytest.approx(60 / 90) and "beats" not in sent[-1]


def test_a_length_is_seconds_or_a_note_length_by_name(sent):
    assert [length_beats(n) for n in ("whole", "half", "quarter", "eighth", "sixteenth", "1/4", "1/16", "q", "e", "quarter.", "dotted quarter")] \
        == [4, 2, 1, 0.5, 0.25, 1, 0.25, 1, 0.5, 1.5, 1.5]
    assert length_beats("eighth triplet") == pytest.approx(1 / 3) and length_beats("q3") == pytest.approx(2 / 3)
    assert length_beats("minor") is None and length_beats(2) is None
    set_tempo(60)
    assert beats("half") == 2 and beats(3) == 3
    play_note("C4", "quarter")
    assert sent[-1]["len"] == 1
    play_note("C4", 0.25)
    assert sent[-1]["len"] == 0.25
    make_synth("lead").arp("Cm", "eighth")
    assert sent[-1]["len"] == 0.5 and sent[-1]["arp"]["offsets"] == [0, 3, 7]
    play_sound("win", length="half")
    assert sent[-1]["len"] == 2


def test_a_tune_a_line_at_a_time(sent):
    """Each note begins where the last ended; lines written together begin together."""
    set_tempo(120)
    lead, bass = make_synth("lead"), make_synth("bass")
    for name in ("E4", "G4"):
        lead.note(name, "quarter")
    lead.rest("quarter")
    lead.chord("Cm", "half", volume=0.5)
    bass.note("C2", "half")
    bass.note("G2", 2)                    # a number is beats
    notes = [c for c in sent if c["op"] == "note"]
    start = notes[0]["t"]
    assert [(c["id"], c["note"], round(c["t"] - start, 9), c["len"]) for c in notes] == [
        ("s1", [64], 0, 0.475), ("s1", [67], 0.5, 0.475), ("s1", [60, 63, 67], 1.5, 0.95),
        ("s2", [36], 0, 0.95), ("s2", [43], 1, 0.95)]
    assert notes[2]["vel"] == 0.5
    note("C4")                            # on the synth play_note uses, a quarter with nothing said
    assert sent[-1]["id"] == "s3" and sent[-1]["len"] == 0.475 and sent[-1]["t"] == start
    start_lines(after=2)
    lead.note("C4")
    assert sent[-1]["t"] == pytest.approx(sound_time() + 2, abs=0.01)


def test_a_section_goes_round(sent):
    set_tempo(120)
    kick, snare = make_synth("kick"), make_synth("snare")
    with loop_notes() as beat:
        kick.note("C3", "quarter")
        kick.rest("quarter")
        snare.rest("quarter")
        snare.note("A3", "quarter")
    tunes = [c for c in sent if c["op"] == "tune"]
    assert [(c["synth"], c["steps"], c["length"], c["repeat"], c["beats"]) for c in tunes] == [
        ("s1", [[0, [48], 0.95, 0.8]], 2, True, True), ("s2", [[1, [57], 0.95, 0.8]], 2, True, True)]
    assert tunes[0]["t"] == tunes[1]["t"]
    beat.stop()
    assert [c["id"] for c in sent[-2:]] == [t["id"] for t in tunes] and sent[-1]["op"] == "stop"

    def fill():
        kick.note("C3", "eighth")
    loop_notes(4, fill)
    assert sent[-1]["repeat"] == 4 and sent[-1]["length"] == 0.5
    kick.note("C3")                       # the line carries on after the four times round
    assert sent[-1]["t"] == pytest.approx(sent[-2]["t"] + 4 * 0.25)
    with pytest.raises(ValueError) as e:
        with loop_notes():
            pass
    assert "nothing was written to go round" in str(e.value)


def test_settings_read_back_what_was_set(sent):
    lead = make_synth("lead", cutoff=1200)
    assert lead.cutoff == 1200 and lead.wave == "saw" and lead.wave2 == "pulse" and lead.echo == 0.2
    lead.cutoff = 800
    lead.vibrato_rate = 6
    lead.octave = -1
    lead.echo_bounce = True
    assert (lead.cutoff, lead.vibrato_rate, lead.octave, lead.pitch, lead.echo_bounce) == (800, 6, -1, -12, True)
    assert sent[-3]["set"] == {"vibrato_rate": 6}
    lead.cutoff = 99999                # kept inside what the setting can be
    assert lead.cutoff == 20000
    lead.mine = 3                      # any other name is the program's own
    assert lead.mine == 3
    assert lead.describe("cutoff") == {"name": "cutoff", "kind": "float", "min": 20, "max": 20000, "default": 2000, "unit": "Hz"}
    assert lead.describe("wave")["choices"][:3] == ["sine", "triangle", "saw"]
    lead._told("cutoff", 432)          # a dial in the page turned
    assert lead.cutoff == 432 and sent[-1]["op"] == "set" and sent[-1]["set"] != {"cutoff": 432}


def test_chords_and_arpeggios(sent):
    assert chord_notes("Cm7") == [60, 63, 67, 70] and chord_notes("C3", "minor") == [48, 51, 55]
    assert chord_notes("F#") == [66, 70, 73] and chord_notes("C", "M7") == [60, 64, 67, 71]
    lead = make_synth("lead")
    lead.play("Cm7", 1)
    assert sent[-1]["note"] == [60, 63, 67, 70]
    lead.play_notes("Cm G4 Fsus4", 0.5)
    assert [s[1] for s in sent[-1]["steps"]] == [[60, 63, 67], [67], [65, 70, 72]]
    arp = lead.arp("C4", "minor", 2, speed=30, order="up-down")
    assert sent[-1]["note"] == [60] and sent[-1]["len"] == 2 and sent[-1]["h"] == 1
    assert sent[-1]["arp"] == {"offsets": [0, 3, 7], "rate": 30, "order": 2}
    arp.change("G3")
    assert sent[-1]["op"] == "voice" and sent[-1]["h"] == 1 and sent[-1]["arp"] == {"offsets": [-5, -1, 2], "rate": 30, "order": 2}
    held = lead.start_arp("Am")
    assert sent[-1]["len"] is None and sent[-1]["arp"]["rate"] == 50
    held.stop()
    play_arp("Cm7")
    assert sent[-2] == {"op": "synth", "id": "s3", "preset": "chip", "t": sent[-2]["t"]} and sent[-1]["len"] == 0.5


def test_a_ready_made_synth_s_macro_reads_back(sent):
    assert make_synth("chip_kick").macro[0] == {"wave": "square", "pitch": 12}
    assert "macro" not in sent[-1], "the player knows the ready-made synth's own macro"
    lead = make_synth("lead")
    assert lead.macro is None
    lead.macro = [{"pitch": 0}, {"pitch": 12}]
    assert sent[-1] == {"op": "macro", "id": "s2", "macro": [{"pitch": 0}, {"pitch": 12}], "t": sent[-1]["t"]}
    assert lead.macro == [{"pitch": 0}, {"pitch": 12}]


def test_notes():
    assert [note_number(n) for n in ("C4", "A4", "F#3", "Bb5", "C-1", "c", 61.5, "62")] == [60, 69, 54, 82, 0, 60, 61.5, 62]


@pytest.mark.parametrize("call, says", [
    (lambda: play_sound("lazer"), 'play_sound("lazer"): there is no sound called "lazer". Did you mean "laser"? The sounds are: coin,'),
    (lambda: play_sound(), "play_sound(): there is no sound called None. The sounds are:"),
    (lambda: make_synth(cutof=3), 'make_synth(): there is no setting called "cutof". Did you mean "cutoff"?'),
    (lambda: make_synth("bas"), 'make_synth("bas"): there is no synth called "bas". Did you mean "bass"? The synths are: keys,'),
    (lambda: make_synth("lead", wave="sqare"), 'make_synth("lead"): wave: "sqare" is not one of its choices. Did you mean "square"?'),
    (lambda: make_synth(cutoff="high"), 'make_synth(): cutoff needs a number from 20 to 20000, not "high"'),
    (lambda: play_note("H4"), '"H4" is not a note. Write a note as a name like "C4", "F#3" or "Bb5", or as a number, where 60 is middle C'),
    (lambda: play_note(), 'play_note needs a note, as in play_note("C4")'),
    (lambda: play_note("C4", -1), 'play: the length needs a number of seconds, more than 0, or a note length such as "quarter", not -1'),
    (lambda: play_note("C4", "quater"), 'play: the length needs a number, or a note length by name: "whole", "half", "quarter", "eighth", "sixteenth" (also "1/4", "q", and "quarter." for a dotted one), not "quater". Did you mean "quarter"?'),
    (lambda: play_notes("C4:x D4"), 'play_notes: in "C4:x", "x" is not a length. After the colon write how many steps (":2") or a note length'),
    (lambda: note(), 'note needs a note, as in note("C4", "quarter"). For a silence, use rest("quarter")'),
    (lambda: play_notes(""), 'play_notes needs notes to play, as in play_notes("C4 E4 G4 - C5"), not ""'),
    (lambda: load_sample(), 'load_sample() needs the name of a sound file, as in load_sample("kick.wav")'),
    (lambda: set_effects(cutoff=3), "set_effects is for the effects every synth shares: max_voices,"),
    (lambda: setattr(make_synth(), "cutof", 3), 'A synth has no setting called "cutof". Did you mean "cutoff"?'),
    (lambda: make_synth().play("Cmi7"), '"Cmi7" is not a note or a chord. Did you mean "Cmin"? A note is written "C4" or "F#3"'),
    (lambda: play_arp(), 'play_arp needs a chord, as in play_arp("Cm7"), play_arp("C4", "minor") or play_arp(["C4", "E4", "G4"])'),
    (lambda: play_arp("C", "minr"), '"minr" is not a kind of chord. Did you mean "minor"? The kinds are: major, minor,'),
    (lambda: play_arp("Cm", order="sideways"), 'play_arp: "sideways" is not an order an arpeggio can go in. The orders are: up, down,'),
    (lambda: make_synth(macro=[{"wave": "nose"}]), 'make_synth(): "nose" is not a wave a step can switch to. Did you mean "noise"?'),
    (lambda: make_synth().set_macro(3), 'set_macro: a macro needs a list of steps, as in [{"pitch": 0}, {"pitch": 4}, {"pitch": 7}], not 3'),
])
def test_a_mistake_is_said_in_plain_words(sent, call, says):
    with pytest.raises((ValueError, AttributeError)) as e:
        call()
    assert str(e.value).startswith(says), str(e.value)


def test_a_mistake_writes_no_command(sent):
    for call in (lambda: play_sound("lazer"), lambda: make_synth(cutof=3), lambda: play_notes("C4 H4")):
        with pytest.raises(ValueError):
            call()
    assert [c["op"] for c in sent] == ["synth"]      # the synth play_notes plays on, made before its notes were read


def test_a_song_is_sent_whole_when_python_has_it(sent, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "songs").mkdir()
    (tmp_path / "songs" / "kick.wav").write_bytes(b"RIFF")
    (tmp_path / "songs" / "mine.json").write_text('{"samples": [{"file": "kick.wav"}, {"file": "gone.wav"}, {}]}')
    play_song("songs/mine.json", patches={"tune": "bell", "low": {"preset": "chip_bass", "cutoff": 300}})
    c = sent[-1]
    assert c["name"] == "songs/mine.json" and "url" not in c and c["repeat"] is True
    assert c["files"] == {"kick.wav": "UklGRg=="}, "the WAV files it names that are there go with it"
    assert c["patches"] == {"tune": "bell", "low": {"cutoff": 300, "preset": "chipBass"}}
    play_song("not_here.mod", repeat=False)
    assert sent[-1]["url"] == "not_here.mod" and "bytes" not in sent[-1] and sent[-1]["repeat"] is False
    song = play_song("not_here.xm")
    song.seek(2, 16)
    assert sent[-1] == {"op": "song", "id": song.id, "do": "seek", "order": 2, "row": 16, "t": sent[-1]["t"]}
    with pytest.raises(ValueError) as e:
        play_song("x.mod", patches={"low": "bas"})
    assert str(e.value).startswith('play_song: the patch "low" names a synth called "bas", and there is none. Did you mean "bass"?')
