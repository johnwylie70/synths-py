"""The microphone, recording, saving, the voices, a song's controls and reading the sound back.

No microphone is ever opened: where a test listens, synths.js's offline player renders Python's commands in node
with a tone in a microphone's place (the `studio` fixture), and what the player says back is handed to Python as
a page hands it over with a frame.
"""
import json
import shutil
import struct
import subprocess

import pytest

import synths
from synths import *
from conftest import JS_REPO, ROOT

TONE = {"hz": 440, "seconds": 12}


def no_time(cmds):
    return [{k: v for k, v in c.items() if k != "t"} for c in cmds]


# ---------------------------------------------------------------- the names

def test_the_microphone_s_names_are_those_of_synths_js():
    names = synths._NAMES["microphone"]
    for name in names["functions"]:
        assert callable(getattr(synths, synths._snake(name))), name
        assert synths._snake(name) in synths.__all__, name
    assert [n for n in names["micFunctions"] if not callable(getattr(synths.Mic, synths._snake(n), None))] == []
    assert [n for n in names["takeFunctions"] if not callable(getattr(synths.Take, synths._snake(n), None))] == []
    assert voice_names() == list(synths._NAMES["voices"])
    # Every word of the microphone's own is a setting every synth has.
    for said, to in names["names"].items():
        assert synths._setting(to) is not None, to
    for name in synths._NAMES["song"]["functions"]:
        assert callable(getattr(synths.Song, synths._snake(name))), name


def test_every_voice_is_made_of_settings_that_exist():
    for name, voice in synths._NAMES["voices"].items():
        assert synths._patch_of(voice["values"], name, strict=True)


def test_the_same_program_writes_the_same_commands_as_synths_js(sent, tmp_path):
    """One program in both languages, command for command."""
    if not shutil.which("node") or not (JS_REPO / "synths.js").exists():
        pytest.skip("node or synths.js is not here")
    from sync_names import committed
    for name in ("synths.js", "synths_core.wasm"):
        (tmp_path / name).write_bytes(committed(JS_REPO, name))
    theirs = json.loads(subprocess.run(["node", str(ROOT / "tests" / "same_program.mjs"), str(tmp_path / "synths.js")],
                                       capture_output=True, text=True, check=True, timeout=60).stdout)
    synths._sound().clock = lambda: 0
    mic = use_microphone()
    mic.voice = "robot"
    mic.listen()
    mic.pitch = 7
    mic.gain = 2
    mic.gate = -40
    mic.set(gate="off")
    mic.cutoff = 900
    mic.voice = "cave"
    mic.echo = 0.4
    take = record_sound(3)
    take.voice = "monster"
    take.reverse = True
    take.loop = True
    take.play("E4")
    take.sound_like(mic)
    mic.mute()
    going = start_recording(max=60)
    stop_recording()
    going.stop_recording()
    lead = make_synth("lead")
    lead.voice = "alien"
    lead.pitch_shift = 12
    lead.ring_mod = 0.6
    lead.set(comb=0.5, voice="none", glide=2)
    part = lead.record(4)
    record_output(10)
    song = play_song("tune.mod")
    song.mute(2)
    song.mute(2, False)
    song.unmute()
    song.solo(0)
    song.solo("all", False)
    song.loop_pattern()
    song.loop_pattern(False)
    song.replace({"title": "x"})
    song.replace('{"title":"y"}')
    stop_microphone()

    def same(c):
        c = {k: v for k, v in c.items() if k != "t"}
        if isinstance(c.get("set"), dict):
            c["set"] = {synths._key(k): v for k, v in c["set"].items()}       # pitch_shift and pitchShift are one name
        if "text" in c:
            c["text"] = json.loads(c["text"])
        return c
    ours = [same(c) for c in sent]
    theirs = [same(c) for c in theirs if c["op"] != "save"]      # synths.js saves a recording when it is over
    assert ours == theirs
    assert part._sample == "w7"


# ---------------------------------------------------------------- what is written

def test_use_microphone_asks_once_and_is_a_synth(sent):
    mic = use_microphone()
    assert use_microphone() is mic
    assert no_time(sent) == [{"op": "mic", "id": "m1", "set": {"micGate": -50}}]
    assert mic.state == "asking" and mic.ready is None and not mic.listening
    assert mic.gate == -50 and mic.voice == "none" and mic.pitch == 0
    mic.pitch = 5
    assert mic.pitch == 5 and mic.pitch_shift == 5
    assert mic.describe("pitch")["min"] == -12 and mic.describe("listening")["kind"] == "bool"
    assert mic.describe("voice")["choices"] == ["none"] + voice_names()
    assert no_time(sent)[-1] == {"op": "set", "id": "m1", "set": {"pitchShift": 5}}


def test_use_microphone_in_one_line(sent):
    mic = use_microphone("robot", listen=True, raw=False, echo=0.3)
    assert no_time(sent) == [{"op": "mic", "id": "m1", "set": {"micGate": -50}, "raw": False},
                             {"op": "set", "id": "m1", "voice": "robot"},
                             {"op": "set", "id": "m1", "set": {"echo": 0.3}},
                             {"op": "mic", "id": "m1", "listen": True}]
    assert mic.voice == "robot" and mic.listening and mic.ring == 1 and mic.ring_speed == 50
    mic.listening = False
    assert no_time(sent)[-1] == {"op": "mic", "id": "m1", "listen": False}


def test_a_voice_puts_back_what_the_last_one_changed(sent):
    lead = make_synth("lead", echo=0.2)
    every = lambda: {pid: lead._patch.get(pid, default) for pid, default in synths._DEFAULTS.items()}
    before = every()
    lead.voice = "robot"
    assert lead.ring_mod == 1 and lead.comb == 0.45
    lead.voice = "chipmunk"
    assert lead.ring_mod == 0 and lead.pitch_shift == 7 and lead.voice == "chipmunk"
    lead.voice = "none"
    assert every() == before and lead.voice == "none" and lead.echo == 0.2
    assert [c["voice"] for c in sent if "voice" in c] == ["robot", "chipmunk", "none"]


def test_a_control_gives_a_voice_as_its_number_in_the_list(sent):
    lead = make_synth("lead")
    assert lead.describe("voice")["choices"][2] == "chipmunk"
    lead.set("voice", 2)                 # what a picker tied to a synth in Python writes
    assert lead.voice == "chipmunk" and lead.get("voice") == "chipmunk" and sent[-1]["voice"] == "chipmunk"
    lead._told("voice", 1)               # and what the page reports of one tied to it there: nothing is sent again
    assert lead.voice == "robot" and len([c for c in sent if "voice" in c]) == 1


def test_a_voice_that_is_not_one_is_said_in_plain_words(sent):
    lead = make_synth("lead")
    with pytest.raises(ValueError, match=r'"robt" is not a voice. Did you mean "robot"\? The voices are: robot, chipmunk, .*and "none"'):
        lead.voice = "robt"
    with pytest.raises(ValueError, match="needs a recording or a sample to save"):
        save_sound(lead, "x.wav")
    with pytest.raises(ValueError, match="up to 120 seconds"):
        record_sound(500)
    with pytest.raises(ValueError, match='source needs the microphone, a synth or "output"'):
        record_sound(1, source=3)
    with pytest.raises(ValueError, match="needs a function"):
        record_sound(1).on_done(3)


def test_glide_is_the_word_for_sliding_a_setting_and_slide_still_works(sent):
    lead = make_synth("lead")
    lead.set(cutoff=800, glide=2)
    lead.set(cutoff=900, slide=1.5)
    assert [c.get("glide") for c in sent[1:]] == [2, 1.5]


def test_a_song_s_controls(sent):
    song = play_song(b"MOD")
    song.mute(3)
    song.unmute(3)
    song.solo(1)
    song.loop_pattern()
    song.replace(b"\x00\x01", patches={"wobble": "bass"})
    assert no_time(sent)[1:] == [
        {"op": "song", "id": "g1", "do": "mute", "on": True, "channel": 3},
        {"op": "song", "id": "g1", "do": "mute", "on": False, "channel": 3},
        {"op": "song", "id": "g1", "do": "solo", "on": True, "channel": 1},
        {"op": "song", "id": "g1", "do": "loopPattern", "on": True},
        {"op": "song", "id": "g1", "do": "replace", "bytes": "AAE=", "patches": {"wobble": "bass"}}]
    assert set(c["do"] for c in sent) <= set(synths._NAMES["song"]["does"])
    with pytest.raises(ValueError, match="counting from 0"):
        song.mute(40)
    with pytest.raises(ValueError, match="replace needs the new song"):
        song.replace(7)


# ---------------------------------------------------------------- what comes back

def test_what_the_player_says_reaches_the_program(sent):
    mic = use_microphone()
    heard = []
    mic.on_ready(heard.append)
    take = record_sound(2)
    take.on_done(lambda t: heard.append(("done", t.seconds)))
    take.on_done(lambda: heard.append("no arguments"))
    assert not take.done and take.recording and take.seconds == 0
    receive_sound_events([{"type": "microphone", "state": "asking"}, {"type": "microphone", "state": "on"}])
    assert mic.state == "on" and mic.ready is True and heard == [True]
    receive_sound_events({"type": "recorded", "id": take._sample, "frames": 96000, "seconds": 2})
    assert take.done and not take.recording and take.seconds == 2 and take.frames == 96000
    assert heard[1:] == [("done", 2), "no arguments"]
    take.on_done(lambda: heard.append("at once"))
    assert heard[-1] == "at once"
    for kind in synths._NAMES["microphone"]["events"]:
        receive_sound_events({"type": kind})        # every kind is understood, and one with nothing in it changes nothing
    assert mic.state == "unavailable" or mic.state == "on"


def test_no_microphone_is_a_state_and_nothing_is_raised(sent):
    mic = use_microphone()
    take = record_sound(1)
    receive_sound_events([{"type": "microphone", "state": "refused", "message": "the microphone was not allowed."},
                          {"type": "recorded", "id": take._sample, "frames": 0, "seconds": 0}])
    assert mic.state == "refused" and mic.ready is False and "not allowed" in mic.message
    assert take.done and take.seconds == 0
    take.play()
    mic.listen()
    mic.close()
    assert mic.state == "off" and use_microphone() is not mic


def test_readings_and_a_song_s_place_are_what_was_last_said(sent):
    lead = make_synth("lead")
    assert lead.samples() == [] and lead.level() == [0, 0] and lead.notes() == []
    receive_sound_events([{"type": "reading", "id": lead._id, "samples": [0, 0.5, -0.5], "level": [0.4, 0.3], "notes": [60]},
                          {"type": "reading", "samples": [0.1], "level": [1, 1], "notes": [60, 64]}])
    assert lead.samples() == [0, 0.5, -0.5] and lead.level() == [0.4, 0.3] and lead.notes() == [60]
    assert sound_output().samples() == [0.1] and sound_output().notes() == [60, 64]
    song = play_song(b"MOD")
    receive_sound_events({"type": "reading", "id": "song:channel:3", "samples": [0.2], "level": [0.5, 0.5], "notes": []})
    assert song.channel(3).level() == [0.5, 0.5] and song.channel(3).samples() == [0.2] and song.channel(0).level() == [0, 0]
    assert song.position["state"] == "none"
    receive_sound_events({"type": "position", "state": "playing", "order": 2, "row": 16, "rows": 64})
    assert song.position["state"] == "playing" and song.position["row"] == 16 and song.position["tick"] == 0


def test_with_no_player_a_recording_is_over_at_once(monkeypatch):
    synths.connect(None)
    monkeypatch.setattr(synths, "_silent", [synths._Sound(synths._Nowhere())])
    mic = use_microphone()
    take = record_sound(1)
    saved = save_sound(take, "x.wav")
    assert mic.state == "unavailable" and take.done and take.seconds == 0 and saved.done and saved.path is None


def test_awaiting_a_take_looks_again_and_never_holds_the_program(sent):
    take = record_sound(1)

    async def scene():
        return (await take.when_done()).seconds
    running = scene()
    assert running.send(None) is None and running.send(None) is None      # still waiting, a turn at a time
    receive_sound_events({"type": "recorded", "id": take._sample, "seconds": 1, "frames": 48000})
    with pytest.raises(StopIteration) as over:
        running.send(None)
    assert over.value.value == 1


# ---------------------------------------------------------------- listening to it, with a tone for a microphone

def test_the_microphone_is_heard_only_while_it_is_listened_to(studio):
    st = studio(TONE)
    mic = use_microphone(gate="off")
    assert st.go(0.5)["peak"] == 0 and mic.state == "on"       # the page said so with that stretch: a frame late
    mic.listen()
    out = st.go(0.5, hz=[100, 2000])
    assert out["peak"] > 0.1 and abs(out["loudest"] - 440) < 3
    mic.mute()
    st.go(0.2)
    assert st.go(0.5)["peak"] < 0.001
    assert st.said == []


def test_a_voice_changes_the_sound_the_way_its_name_says(studio):
    st = studio(TONE)
    mic = use_microphone(gate="off", listen=True)
    st.go(0.3)
    mic.voice = "chipmunk"
    st.go(0.3)
    up = st.go(0.5, hz=[100, 2000])["loudest"]
    mic.voice = "monster"
    st.go(0.3)
    down = st.go(0.5, hz=[100, 2000])["loudest"]
    mic.voice = "none"
    st.go(0.3)
    plain = st.go(0.5, hz=[100, 2000])["loudest"]
    assert abs(up - 440 * 2 ** (7 / 12)) < 6 and abs(down - 440 * 2 ** (-7 / 12)) < 6 and abs(plain - 440) < 3
    mic.pitch = 12
    st.go(0.3)
    assert abs(st.go(0.5, hz=[100, 2000])["loudest"] - 880) < 8


def test_a_second_of_recording_is_a_take_a_second_long_that_plays(studio):
    st = studio(TONE)
    take = record_sound(1)
    assert st.go(0.5)["peak"] == 0 and not take.done       # recording is not listening
    st.go(0.6)
    assert take.done and take.seconds == pytest.approx(1, abs=0.01) and take.frames == 48000
    take.play()
    out = st.go(0.5, hz=[100, 2000])
    assert out["peak"] > 0.05 and abs(out["loudest"] - 440) < 3
    st.go(1)
    take.play("C5")                                          # an octave above its own pitch
    assert abs(st.go(0.4, hz=[100, 2000])["loudest"] - 880) < 6


def test_save_sound_gives_a_wav_file_of_the_right_length(studio, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    st = studio(TONE)
    take = record_sound(1)
    # Run by your own Python, the file is written beside the program: the page is asked for the bytes.
    monkeypatch.setattr(synths._Direct, "keeps_files", lambda self: True)
    saved = save_sound(take, "takes/hello")
    told = []
    saved.on_done(lambda s: told.append(s.name))
    kept = save_sound(take, download=False)
    assert not saved.done                                    # asked while it is still recording: saved when it is over
    st.go(1.2)
    assert saved.done and told == ["takes/hello.wav"] and saved.seconds == pytest.approx(1, abs=0.01)
    data = (tmp_path / "takes" / "hello.wav").read_bytes()
    assert saved.path == str((tmp_path / "takes" / "hello.wav").resolve()) or saved.path.endswith("takes/hello.wav")
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE" and struct.unpack("<I", data[4:8])[0] == len(data) - 8
    channels, rate, _, _, bits = struct.unpack("<HIIHH", data[22:36])
    assert (channels, rate, bits) == (1, 48000, 16) and len(data) == 44 + 48000 * 2
    loudest = max(abs(v) for v in struct.unpack("<%dh" % 48000, data[44:]))
    assert 0.4 * 32767 < loudest < 0.6 * 32767               # the tone, at the level it came in
    # download=False keeps the bytes and writes no file.
    assert kept.done and kept.bytes == data and kept.path is None and not (tmp_path / "sound.wav").exists()
    assert [c.get("download") for c in st.all_cmds if c["op"] == "save"] == [False, False]


def test_in_a_page_the_file_is_the_page_s_to_save(sent):
    take = record_sound(1)
    saved = save_sound(take, "hello.wav")
    assert no_time(sent)[-1] == {"op": "save", "id": take._sample, "name": "hello.wav", "ask": 1}
    receive_sound_events({"type": "saved", "ask": 1, "name": "hello.wav", "seconds": 1})
    assert saved.done and saved.bytes is None and saved.path is None


def test_what_is_played_can_be_recorded_and_a_synth_alone(studio):
    st = studio()
    lead = make_synth("lead")
    tune = record_output(0.5)
    part = lead.record(0.5)        # one recording is made at a time: this one ends the first
    lead.play("A4", 0.4)
    st.go(0.7)
    assert tune.done and part.done and part.seconds == pytest.approx(0.5, abs=0.01)
    part.play()
    out = st.go(0.3, hz=[200, 1000])
    assert out["peak"] > 0.02 and abs(out["loudest"] - 440) < 4


def test_with_no_microphone_one_thing_is_said_and_everything_else_plays(studio):
    st = studio(None)
    mic = use_microphone("robot", listen=True)
    take = record_sound(1)
    take.on_done(lambda t: t.play())
    play_note("A4", 0.3)
    out = st.go(0.5, hz=[200, 1000])
    assert mic.state == "unavailable" and mic.ready is False
    assert take.done and take.seconds == 0
    assert out["peak"] > 0.05 and abs(out["loudest"] - 440) < 4
    record_sound(1)
    mic.voice = "monster"
    st.go(0.3)
    assert len(st.said) == 1 and "microphone" in st.said[0]


def test_reading_back_what_a_synth_does_and_where_a_song_is(studio):
    st = studio()
    lead = make_synth("lead")
    lead.play("A4", 1)
    out = st.go(0.3, read=lead._id)
    receive_sound_events({"type": "reading", "id": lead._id, **out["read"]})
    assert len(lead.samples()) == 1024 and max(lead.samples()) > 0.05 and lead.notes() == [69] and lead.level()[0] > 0.05
    receive_sound_events({"type": "position", **out["position"]})
    assert play_song(b"x").position["state"] == "none"
