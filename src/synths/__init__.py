"""synths: sounds and music in Python. The sound sibling of Pyctures.

    from synths import *

    play_sound("laser")                    # a ready-made game sound: coin, jump, laser, explosion, hit, powerup, ...
    play_note("C4")                        # a note on a pleasant synth: a name or a number (60 is middle C),
    play_note("C4", 0.5, 0.8)              # then how long in seconds and how loud (0 to 1). A list is a chord
    play_notes("C4 E4 G4 - C5:2", 0.25)    # a tune, a step every quarter of a second; "-" is a rest
    lead = make_synth("lead", cutoff=1200) # a synth of your own, from a ready-made one (bass, lead, pad, pluck, ...)
    lead.play("E4", 0.5)                   # play a note; lead.play(["C4", "E4", "G4"]) is a chord
    lead.cutoff = 800                      # every setting is a plain attribute, and changes notes already sounding
    held = lead.start("C4")                # a note that stays until held.stop(); held.slide_to("G4", 0.5)
    note("C4", "quarter"), rest("eighth")  # a tune a line at a time: each note begins where the last ended
    lead.arp("Cm7")                        # a chord from one voice, as a fast arpeggio (a C64 chord)
    arp = lead.start_arp("Am")             # one that stays: arp.change("F"), arp.stop()
    drum = load_sample("kick.wav")         # a recorded sound from a file; drum.play()
    song = play_song("tune.mod")           # a tracker song (.mod, .xm) or one of synths' own: song.pause(), song.stop()
    set_volume(0.5), mute_sound(), unmute_sound(), stop_sound()
    set_effects(echo_time=0.3, reverb_size=0.8)
    set_tempo(120), beats(2)               # beats(2) is how many seconds two beats last
    lead.play_from_midi()                  # a MIDI keyboard plays a synth; lead.learn("cutoff") ties a knob to a setting
    send_midi_note("C4", 0.8, length="quarter")    # a note out to a synth on the desk; midi_devices()
    mic = use_microphone()                 # the microphone is a synth whose sound comes in: mic.voice = "robot",
    mic.listen()                           # mic.pitch = 7, mic.echo = 0.4. Nothing is heard until listen()
    take = record_sound(3)                 # three seconds of it, as a sample, at once: take.play("E4"), take.done
    save_sound(take, "hello.wav")          # a recording or a sample as a WAV file
    lead.voice = "robot"                   # a voice changer on any synth; lead.pitch_shift, lead.ring_mod, lead.comb
    lead.samples(), lead.level(), lead.notes()     # what it is doing, for your own scope, meter and lit keys

    def on_midi_note(note, velocity, channel):     # in a Pyctures scene: called for every key of a MIDI keyboard
        ...

A length is seconds as a number, or a note length by name, which follows the tempo: "whole", "half",
"quarter", "eighth", "sixteenth" (also "1/4", "q", "quarter." for a dotted one, "eighth triplet").

When something starts: everything that makes a sound takes after=seconds, at=a time read from
sound_time(), or beat=a beat number.

HOW IT IS BUILT. No sound is worked out in Python. Every function here only WRITES A COMMAND:
plain data such as {"op": "note", "id": "s1", "note": [60], "len": 0.5, "t": 12.25}, in the format
of synths.js (its docs/commands.md is the contract). Every id is chosen here, and nothing is ever
answered, so no line of a program waits for the sound. A PLAYER somewhere else (synths.js, in a
web page) owns the sound card and carries the commands out.

TIME. Each command carries the time it was asked for on Python's own clock
(time.perf_counter()), and each batch the clock when it was sent. The player lines that clock up
with the sound card's and plays everything a moment late on the exact sample, so commands that
were called at uneven moments and sent together once a frame keep exactly the spacing they had.

HOW THE COMMANDS TRAVEL (see _sound):

  - In a Pyctures scene they ride the frame's own message: the first sound of a frame adds ONE
    command to the frame, a call of `send(batch)` on the page's sound object (the fixed handle
    H_SOUND, 10), and the rest of that frame's sounds join the same batch. This is so wherever
    the scene's Python runs: in a browser's worker, in your own Python behind `pyctures run`, or
    on another computer. Sound asked for outside draw() and update() (at the top of the file, in
    setup(), in on_key_down()) is inside the same call from the page, so it goes with that
    call's reply and never waits for a frame of its own.
  - A host that plays the commands some other way calls connect(send), and each command is
    handed to it at once.
  - MIDI goes the same way: its functions write `midi` commands into the same batches, and the page, where the
    devices are, plays a synth from a keyboard itself. What was received is handed back as plain data with the
    next frame (see _Midi), or by a host with receive_midi(events).
  - WHAT COMES BACK. Commands are never answered. A few things are said by the player all the same: the
    microphone is on or is not, a recording is over, a file is saved, and what a synth is doing now (its wave,
    its level, its notes) and where a song is, for a program that draws them. In a Pyctures scene the page
    hands them over with the NEXT FRAME, so each is a frame late: take.done turns True the frame after the
    recording ended, and lead.samples() is the wave as it was a frame ago. A host hands them over with
    receive_sound_events(events).
  - A program started with plain Python (`python tune.py`) has no player. If Pyctures is
    installed the program is started again with `pyctures run`, which opens it in a browser;
    otherwise it says how to, once, and carries on in silence.

MIT licence.
"""
import base64
import json
import math
import os
import re
import sys
import time

__version__ = "0.1.0"

__all__ = ["play_sound", "play_note", "play_notes", "make_synth", "load_sample", "play_song", "stop_song",
           "stop_sound", "set_volume", "mute_sound", "unmute_sound", "set_effects", "set_tempo", "beats", "beat", "set_sound_buffer", "sound_buffer",
           "sound_time", "sound_names", "synth_names", "setting_names", "note_number", "chord_notes", "play_arp",
           "start_arp", "main_synth", "sound_output", "note", "chord", "rest", "start_lines", "loop_notes",
           "length_beats",
           "on_midi", "on_midi_note", "on_midi_note_off", "on_midi_control", "on_midi_devices", "use_midi_hooks",
           "send_midi", "send_midi_note", "send_midi_note_off", "send_midi_control", "send_midi_bend",
           "send_midi_program", "send_midi_clock", "midi_devices", "use_midi_input", "use_midi_output", "midi_input", "midi_output",
           "receive_midi", "stop_midi",
           "use_microphone", "stop_microphone", "record_sound", "start_recording", "stop_recording",
           "record_output", "save_sound", "receive_sound_events", "voice_names"]

# The version of the command format: `synths` in every batch.
COMMANDS = 1
# The page's sound object in a Pyctures scene, unless Pyctures says otherwise (its H_SOUND).
H_SOUND = 10

# Every sound, ready-made synth and setting, as synths.js names them. Written here by
# scripts/sync_names.py from synths.js's synths-names.json. Do not edit by hand.
# NAMES:BEGIN
_NAMES = json.loads(r'''
{
 "version": "0.1.0",
 "commands": 1,
 "engine": {"abi": 1, "version": "0.0.0", "parts": 64, "voices": 64, "samples": 1024, "events": ["note_on", "note_off", "all_notes_off", "param", "pitch_bend", "voice_pitch", "voice_freq", "voice_volume", "voice_pan", "voice_position", "voice_kill", "macro_tick", "arp", "arp_more", "song", "record"]},
 "settings": [
  {"id": 0, "name": "volume", "kind": "float", "min": 0, "max": 2, "default": 1, "unit": "gain", "scope": "synth"},
  {"id": 1, "name": "pan", "kind": "float", "min": -1, "max": 1, "default": 0, "unit": "pan", "scope": "synth"},
  {"id": 2, "name": "transpose", "kind": "float", "min": -48, "max": 48, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 3, "name": "tune", "kind": "float", "min": -100, "max": 100, "default": 0, "unit": "cents", "scope": "synth"},
  {"id": 4, "name": "bend", "kind": "float", "min": -1, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 5, "name": "bend_range", "kind": "float", "min": 0, "max": 48, "default": 2, "unit": "semitones", "scope": "synth"},
  {"id": 6, "name": "glide", "kind": "float", "min": 0, "max": 10, "default": 0, "unit": "seconds", "scope": "synth"},
  {"id": 7, "name": "mode", "kind": "choice", "min": 0, "max": 2, "default": 0, "unit": "", "choices": ["poly", "mono", "legato"], "scope": "synth"},
  {"id": 8, "name": "unison.voices", "kind": "int", "min": 1, "max": 8, "default": 1, "unit": "voices", "scope": "synth"},
  {"id": 9, "name": "unison.detune", "kind": "float", "min": 0, "max": 100, "default": 20, "unit": "cents", "scope": "synth"},
  {"id": 10, "name": "unison.spread", "kind": "float", "min": 0, "max": 1, "default": 0.5, "unit": "", "scope": "synth"},
  {"id": 11, "name": "velocity", "kind": "float", "min": 0, "max": 1, "default": 1, "unit": "", "scope": "synth"},
  {"id": 12, "name": "pan.law", "kind": "choice", "min": 0, "max": 1, "default": 0, "unit": "", "choices": ["equal_power", "square_root"], "scope": "synth"},
  {"id": 16, "name": "osc1.wave", "kind": "choice", "min": 0, "max": 4, "default": 1, "unit": "", "choices": ["sine", "triangle", "saw", "pulse", "sample"], "scope": "synth"},
  {"id": 17, "name": "osc1.level", "kind": "float", "min": 0, "max": 1, "default": 1, "unit": "gain", "scope": "synth"},
  {"id": 18, "name": "osc1.coarse", "kind": "float", "min": -48, "max": 48, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 19, "name": "osc1.fine", "kind": "float", "min": -100, "max": 100, "default": 0, "unit": "cents", "scope": "synth"},
  {"id": 20, "name": "osc1.pulse_width", "kind": "float", "min": 0, "max": 1, "default": 0.5, "unit": "", "scope": "synth"},
  {"id": 21, "name": "osc1.sample", "kind": "int", "min": 0, "max": 1023, "default": 0, "unit": "slot", "scope": "synth"},
  {"id": 22, "name": "osc1.start", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 23, "name": "osc1.keytrack", "kind": "bool", "min": 0, "max": 1, "default": 1, "unit": "", "scope": "synth"},
  {"id": 24, "name": "osc2.wave", "kind": "choice", "min": 0, "max": 4, "default": 2, "unit": "", "choices": ["sine", "triangle", "saw", "pulse", "sample"], "scope": "synth"},
  {"id": 25, "name": "osc2.level", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "gain", "scope": "synth"},
  {"id": 26, "name": "osc2.coarse", "kind": "float", "min": -48, "max": 48, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 27, "name": "osc2.fine", "kind": "float", "min": -100, "max": 100, "default": 0, "unit": "cents", "scope": "synth"},
  {"id": 28, "name": "osc2.pulse_width", "kind": "float", "min": 0, "max": 1, "default": 0.5, "unit": "", "scope": "synth"},
  {"id": 29, "name": "osc2.sample", "kind": "int", "min": 0, "max": 1023, "default": 0, "unit": "slot", "scope": "synth"},
  {"id": 30, "name": "osc2.start", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 31, "name": "osc2.keytrack", "kind": "bool", "min": 0, "max": 1, "default": 1, "unit": "", "scope": "synth"},
  {"id": 32, "name": "osc2.sync", "kind": "bool", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 33, "name": "osc2.ring", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 34, "name": "osc1.reverse", "kind": "bool", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 35, "name": "osc2.reverse", "kind": "bool", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 36, "name": "sub.level", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "gain", "scope": "synth"},
  {"id": 37, "name": "sub.wave", "kind": "choice", "min": 0, "max": 2, "default": 0, "unit": "", "choices": ["sine", "square", "triangle"], "scope": "synth"},
  {"id": 38, "name": "sub.octave", "kind": "int", "min": -2, "max": -1, "default": -1, "unit": "octaves", "scope": "synth"},
  {"id": 39, "name": "sample.antialias", "kind": "bool", "min": 0, "max": 1, "default": 1, "unit": "", "scope": "synth"},
  {"id": 40, "name": "noise.level", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "gain", "scope": "synth"},
  {"id": 41, "name": "noise.type", "kind": "choice", "min": 0, "max": 3, "default": 0, "unit": "", "choices": ["white", "pink", "lfsr", "lfsr_short"], "scope": "synth"},
  {"id": 42, "name": "noise.pitch", "kind": "float", "min": -48, "max": 48, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 48, "name": "filter.type", "kind": "choice", "min": 0, "max": 7, "default": 0, "unit": "", "choices": ["off", "lowpass", "highpass", "bandpass", "notch", "low_band", "band_high", "all"], "scope": "synth"},
  {"id": 49, "name": "filter.slope", "kind": "choice", "min": 0, "max": 1, "default": 0, "unit": "", "choices": ["12db", "24db"], "scope": "synth"},
  {"id": 50, "name": "filter.cutoff", "kind": "float", "min": 20, "max": 20000, "default": 2000, "unit": "hz", "scope": "synth"},
  {"id": 51, "name": "filter.resonance", "kind": "float", "min": 0, "max": 1, "default": 0.15, "unit": "", "scope": "synth"},
  {"id": 52, "name": "filter.keytrack", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 53, "name": "filter.env", "kind": "float", "min": -96, "max": 96, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 54, "name": "filter.velocity", "kind": "float", "min": -96, "max": 96, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 56, "name": "amp.attack", "kind": "float", "min": 0, "max": 20, "default": 0.005, "unit": "seconds", "scope": "synth"},
  {"id": 57, "name": "amp.decay", "kind": "float", "min": 0, "max": 20, "default": 0.1, "unit": "seconds", "scope": "synth"},
  {"id": 58, "name": "amp.sustain", "kind": "float", "min": 0, "max": 1, "default": 0.8, "unit": "", "scope": "synth"},
  {"id": 59, "name": "amp.release", "kind": "float", "min": 0, "max": 20, "default": 0.15, "unit": "seconds", "scope": "synth"},
  {"id": 60, "name": "amp.curve", "kind": "float", "min": 0, "max": 1, "default": 0.5, "unit": "", "scope": "synth"},
  {"id": 64, "name": "filter_env.attack", "kind": "float", "min": 0, "max": 20, "default": 0.005, "unit": "seconds", "scope": "synth"},
  {"id": 65, "name": "filter_env.decay", "kind": "float", "min": 0, "max": 20, "default": 0.2, "unit": "seconds", "scope": "synth"},
  {"id": 66, "name": "filter_env.sustain", "kind": "float", "min": 0, "max": 1, "default": 0.3, "unit": "", "scope": "synth"},
  {"id": 67, "name": "filter_env.release", "kind": "float", "min": 0, "max": 20, "default": 0.2, "unit": "seconds", "scope": "synth"},
  {"id": 68, "name": "filter_env.curve", "kind": "float", "min": 0, "max": 1, "default": 0.5, "unit": "", "scope": "synth"},
  {"id": 72, "name": "mod_env.attack", "kind": "float", "min": 0, "max": 20, "default": 0.005, "unit": "seconds", "scope": "synth"},
  {"id": 73, "name": "mod_env.decay", "kind": "float", "min": 0, "max": 20, "default": 0.2, "unit": "seconds", "scope": "synth"},
  {"id": 74, "name": "mod_env.sustain", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 75, "name": "mod_env.release", "kind": "float", "min": 0, "max": 20, "default": 0.2, "unit": "seconds", "scope": "synth"},
  {"id": 76, "name": "mod_env.curve", "kind": "float", "min": 0, "max": 1, "default": 0.5, "unit": "", "scope": "synth"},
  {"id": 77, "name": "mod_env.pitch", "kind": "float", "min": -48, "max": 48, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 78, "name": "mod_env.osc2_pitch", "kind": "float", "min": -48, "max": 48, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 79, "name": "mod_env.pulse_width", "kind": "float", "min": -1, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 80, "name": "lfo1.wave", "kind": "choice", "min": 0, "max": 4, "default": 0, "unit": "", "choices": ["sine", "triangle", "saw", "square", "random"], "scope": "synth"},
  {"id": 81, "name": "lfo1.rate", "kind": "float", "min": 0.01, "max": 50, "default": 5, "unit": "hz", "scope": "synth"},
  {"id": 82, "name": "lfo1.delay", "kind": "float", "min": 0, "max": 10, "default": 0, "unit": "seconds", "scope": "synth"},
  {"id": 83, "name": "lfo1.fade", "kind": "float", "min": 0, "max": 10, "default": 0, "unit": "seconds", "scope": "synth"},
  {"id": 84, "name": "lfo1.sync", "kind": "bool", "min": 0, "max": 1, "default": 1, "unit": "", "scope": "synth"},
  {"id": 85, "name": "lfo1.pitch", "kind": "float", "min": -48, "max": 48, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 86, "name": "lfo1.pulse_width", "kind": "float", "min": -1, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 87, "name": "lfo1.cutoff", "kind": "float", "min": -96, "max": 96, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 88, "name": "lfo1.amp", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 89, "name": "lfo1.pan", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 96, "name": "lfo2.wave", "kind": "choice", "min": 0, "max": 4, "default": 1, "unit": "", "choices": ["sine", "triangle", "saw", "square", "random"], "scope": "synth"},
  {"id": 97, "name": "lfo2.rate", "kind": "float", "min": 0.01, "max": 50, "default": 0.5, "unit": "hz", "scope": "synth"},
  {"id": 98, "name": "lfo2.delay", "kind": "float", "min": 0, "max": 10, "default": 0, "unit": "seconds", "scope": "synth"},
  {"id": 99, "name": "lfo2.fade", "kind": "float", "min": 0, "max": 10, "default": 0, "unit": "seconds", "scope": "synth"},
  {"id": 100, "name": "lfo2.sync", "kind": "bool", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 101, "name": "lfo2.pitch", "kind": "float", "min": -48, "max": 48, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 102, "name": "lfo2.pulse_width", "kind": "float", "min": -1, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 103, "name": "lfo2.cutoff", "kind": "float", "min": -96, "max": 96, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 104, "name": "lfo2.amp", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 105, "name": "lfo2.pan", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 106, "name": "fx.pitch", "kind": "float", "min": -12, "max": 12, "default": 0, "unit": "semitones", "scope": "synth"},
  {"id": 107, "name": "fx.ring", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 108, "name": "fx.ring_freq", "kind": "float", "min": 1, "max": 5000, "default": 30, "unit": "hz", "scope": "synth"},
  {"id": 109, "name": "fx.ring_wave", "kind": "choice", "min": 0, "max": 1, "default": 0, "unit": "", "choices": ["sine", "noise"], "scope": "synth"},
  {"id": 110, "name": "fx.comb", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 111, "name": "fx.comb_freq", "kind": "float", "min": 50, "max": 5000, "default": 200, "unit": "hz", "scope": "synth"},
  {"id": 112, "name": "fx.drive", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 113, "name": "fx.bits", "kind": "float", "min": 1, "max": 16, "default": 16, "unit": "bits", "scope": "synth"},
  {"id": 114, "name": "fx.downsample", "kind": "int", "min": 1, "max": 64, "default": 1, "unit": "", "scope": "synth"},
  {"id": 115, "name": "send.delay", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "gain", "scope": "synth"},
  {"id": 116, "name": "send.reverb", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "gain", "scope": "synth"},
  {"id": 117, "name": "send.chorus", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "gain", "scope": "synth"},
  {"id": 120, "name": "macro.rate", "kind": "float", "min": 1, "max": 1000, "default": 50, "unit": "hz", "scope": "synth"},
  {"id": 121, "name": "macro.sync", "kind": "bool", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 122, "name": "fx.comb_feedback", "kind": "float", "min": -0.97, "max": 0.97, "default": 0.7, "unit": "", "scope": "synth"},
  {"id": 123, "name": "fx.comb_rate", "kind": "float", "min": 0.01, "max": 10, "default": 0.3, "unit": "hz", "scope": "synth"},
  {"id": 124, "name": "fx.comb_depth", "kind": "float", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "synth"},
  {"id": 200, "name": "master.volume", "kind": "float", "min": 0, "max": 2, "default": 0.35, "unit": "gain", "scope": "all"},
  {"id": 201, "name": "master.limiter", "kind": "bool", "min": 0, "max": 1, "default": 1, "unit": "", "scope": "all"},
  {"id": 202, "name": "delay.time", "kind": "float", "min": 0.001, "max": 2, "default": 0.3, "unit": "seconds", "scope": "all"},
  {"id": 203, "name": "delay.feedback", "kind": "float", "min": 0, "max": 0.95, "default": 0.4, "unit": "", "scope": "all"},
  {"id": 204, "name": "delay.tone", "kind": "float", "min": 200, "max": 20000, "default": 6000, "unit": "hz", "scope": "all"},
  {"id": 205, "name": "delay.pingpong", "kind": "bool", "min": 0, "max": 1, "default": 0, "unit": "", "scope": "all"},
  {"id": 208, "name": "reverb.size", "kind": "float", "min": 0, "max": 1, "default": 0.5, "unit": "", "scope": "all"},
  {"id": 209, "name": "reverb.damping", "kind": "float", "min": 0, "max": 1, "default": 0.4, "unit": "", "scope": "all"},
  {"id": 210, "name": "reverb.type", "kind": "choice", "min": 0, "max": 4, "default": 0, "unit": "", "choices": ["room", "hall", "plate", "cathedral", "spring"], "scope": "all"},
  {"id": 211, "name": "reverb.decay", "kind": "float", "min": 0, "max": 30, "default": 0, "unit": "seconds", "labels": {"0": "auto"}, "scope": "all"},
  {"id": 212, "name": "chorus.rate", "kind": "float", "min": 0.05, "max": 10, "default": 0.8, "unit": "hz", "scope": "all"},
  {"id": 213, "name": "chorus.depth", "kind": "float", "min": 0, "max": 1, "default": 0.5, "unit": "", "scope": "all"},
  {"id": 216, "name": "voices", "kind": "int", "min": 1, "max": 64, "default": 64, "unit": "voices", "scope": "all"},
  {"id": 217, "name": "input.part", "kind": "int", "min": 0, "max": 63, "default": 31, "unit": "part", "scope": "all"},
  {"id": 218, "name": "input.gain", "kind": "float", "min": 0, "max": 8, "default": 1, "unit": "gain", "scope": "all"},
  {"id": 219, "name": "input.monitor", "kind": "bool", "min": 0, "max": 1, "default": 1, "unit": "", "scope": "all"},
  {"id": 220, "name": "input.gate", "kind": "float", "min": -100, "max": 0, "default": -100, "unit": "db", "labels": {"-100": "off"}, "scope": "all"},
  {"id": 221, "name": "input.gate_release", "kind": "float", "min": 0.005, "max": 2, "default": 0.15, "unit": "seconds", "scope": "all"},
  {"id": 222, "name": "reverb.predelay", "kind": "float", "min": 0, "max": 0.2, "default": 0, "unit": "seconds", "scope": "all"},
  {"id": 223, "name": "reverb.low_cut", "kind": "float", "min": 20, "max": 1000, "default": 120, "unit": "hz", "scope": "all"}
 ],
 "names": {"wave": {"setting": "osc1.wave", "scale": 1}, "level1": {"setting": "osc1.level", "scale": 1}, "width": {"setting": "osc1.pulse_width", "scale": 1}, "pulseWidth": {"setting": "osc1.pulse_width", "scale": 1}, "sample": {"setting": "osc1.sample", "scale": 1}, "octave": {"setting": "transpose", "scale": 12}, "pitch": {"setting": "transpose", "scale": 1}, "maxVoices": {"setting": "voices", "scale": 1}, "voices": {"setting": "unison.voices", "scale": 1}, "detune": {"setting": "unison.detune", "scale": 1}, "spread": {"setting": "unison.spread", "scale": 1}, "wave2": {"setting": "osc2.wave", "scale": 1}, "level2": {"setting": "osc2.level", "scale": 1}, "pitch2": {"setting": "osc2.coarse", "scale": 1}, "detune2": {"setting": "osc2.fine", "scale": 1}, "width2": {"setting": "osc2.pulse_width", "scale": 1}, "sync": {"setting": "osc2.sync", "scale": 1}, "ring": {"setting": "osc2.ring", "scale": 1}, "sub": {"setting": "sub.level", "scale": 1}, "noise": {"setting": "noise.level", "scale": 1}, "macroRate": {"setting": "macro.rate", "scale": 1}, "macroSync": {"setting": "macro.sync", "scale": 1}, "filter": {"setting": "filter.type", "scale": 1}, "slope": {"setting": "filter.slope", "scale": 1}, "cutoff": {"setting": "filter.cutoff", "scale": 1}, "resonance": {"setting": "filter.resonance", "scale": 1}, "keytrack": {"setting": "filter.keytrack", "scale": 1}, "sweep": {"setting": "filter.env", "scale": 1}, "sweepAttack": {"setting": "filter_env.attack", "scale": 1}, "sweepDecay": {"setting": "filter_env.decay", "scale": 1}, "sweepSustain": {"setting": "filter_env.sustain", "scale": 1}, "sweepRelease": {"setting": "filter_env.release", "scale": 1}, "attack": {"setting": "amp.attack", "scale": 1}, "decay": {"setting": "amp.decay", "scale": 1}, "sustain": {"setting": "amp.sustain", "scale": 1}, "release": {"setting": "amp.release", "scale": 1}, "curve": {"setting": "amp.curve", "scale": 1}, "pitchSweep": {"setting": "mod_env.pitch", "scale": 1}, "pitchSweepAttack": {"setting": "mod_env.attack", "scale": 1}, "pitchSweepDecay": {"setting": "mod_env.decay", "scale": 1}, "vibrato": {"setting": "lfo1.pitch", "scale": 1}, "vibratoRate": {"setting": "lfo1.rate", "scale": 1}, "vibratoDelay": {"setting": "lfo1.delay", "scale": 1}, "tremolo": {"setting": "lfo1.amp", "scale": 1}, "wobble": {"setting": "lfo2.cutoff", "scale": 1}, "wobbleRate": {"setting": "lfo2.rate", "scale": 1}, "autopan": {"setting": "lfo2.pan", "scale": 1}, "pwm": {"setting": "lfo2.pulse_width", "scale": 1}, "pwmRate": {"setting": "lfo2.rate", "scale": 1}, "distortion": {"setting": "fx.drive", "scale": 1}, "drive": {"setting": "fx.drive", "scale": 1}, "crush": {"setting": "fx.bits", "scale": 1}, "bits": {"setting": "fx.bits", "scale": 1}, "downsample": {"setting": "fx.downsample", "scale": 1}, "pitchShift": {"setting": "fx.pitch", "scale": 1}, "ringMod": {"setting": "fx.ring", "scale": 1}, "ringSpeed": {"setting": "fx.ring_freq", "scale": 1}, "ringWave": {"setting": "fx.ring_wave", "scale": 1}, "comb": {"setting": "fx.comb", "scale": 1}, "combTone": {"setting": "fx.comb_freq", "scale": 1}, "combFeedback": {"setting": "fx.comb_feedback", "scale": 1}, "flanger": {"setting": "fx.comb_depth", "scale": 1}, "flangerRate": {"setting": "fx.comb_rate", "scale": 1}, "reverse": {"setting": "osc1.reverse", "scale": 1}, "echo": {"setting": "send.delay", "scale": 1}, "delay": {"setting": "send.delay", "scale": 1}, "reverb": {"setting": "send.reverb", "scale": 1}, "chorus": {"setting": "send.chorus", "scale": 1}, "masterVolume": {"setting": "master.volume", "scale": 1}, "limiter": {"setting": "master.limiter", "scale": 1}, "echoTime": {"setting": "delay.time", "scale": 1}, "echoFeedback": {"setting": "delay.feedback", "scale": 1}, "echoTone": {"setting": "delay.tone", "scale": 1}, "echoBounce": {"setting": "delay.pingpong", "scale": 1}, "reverbSize": {"setting": "reverb.size", "scale": 1}, "reverbDamping": {"setting": "reverb.damping", "scale": 1}, "reverbType": {"setting": "reverb.type", "scale": 1}, "reverbDecay": {"setting": "reverb.decay", "scale": 1}, "reverbPredelay": {"setting": "reverb.predelay", "scale": 1}, "reverbLowCut": {"setting": "reverb.low_cut", "scale": 1}, "chorusRate": {"setting": "chorus.rate", "scale": 1}, "chorusDepth": {"setting": "chorus.depth", "scale": 1}, "micGain": {"setting": "input.gain", "scale": 1}, "micGate": {"setting": "input.gate", "scale": 1}, "micGateRelease": {"setting": "input.gate_release", "scale": 1}},
 "choiceWords": {"square": "pulse", "sawtooth": "saw", "tri": "triangle", "sin": "sine", "low": "lowpass", "high": "highpass", "band": "bandpass", "none": "off", "hiss": "white", "chip": "lfsr", "buzz": "lfsr_short"},
 "plain": {"filter": "lowpass", "cutoff": 20000, "resonance": 0.1},
 "synths": {
  "keys": {"wave": "triangle", "wave2": "sine", "level2": 0.35, "pitch2": 12, "cutoff": 3500, "sweep": 18, "sweepDecay": 0.3, "sweepSustain": 0.2, "keytrack": 0.5, "attack": 0.003, "decay": 0.45, "sustain": 0.3, "release": 0.35, "reverb": 0.12},
  "bass": {"wave": "saw", "sub": 0.6, "cutoff": 320, "resonance": 0.3, "sweep": 30, "sweepDecay": 0.18, "sweepSustain": 0.15, "attack": 0.003, "decay": 0.2, "sustain": 0.75, "release": 0.12, "note": 36},
  "lead": {"wave": "saw", "wave2": "square", "level2": 0.6, "detune2": 9, "cutoff": 2800, "resonance": 0.25, "keytrack": 0.5, "attack": 0.01, "decay": 0.15, "sustain": 0.7, "release": 0.2, "vibrato": 0.15, "vibratoDelay": 0.25, "vibratoRate": 5.5, "echo": 0.2},
  "pad": {"wave": "saw", "voices": 4, "detune": 22, "spread": 0.8, "cutoff": 1600, "attack": 0.5, "decay": 0.5, "sustain": 0.8, "release": 1.2, "chorus": 0.4, "reverb": 0.4},
  "pluck": {"wave": "saw", "cutoff": 500, "resonance": 0.2, "sweep": 48, "sweepDecay": 0.12, "sweepSustain": 0, "keytrack": 0.5, "attack": 0.001, "decay": 0.3, "sustain": 0, "release": 0.25},
  "organ": {"wave": "sine", "wave2": "sine", "level2": 0.6, "pitch2": 12, "sub": 0.5, "attack": 0.008, "decay": 0.01, "sustain": 1, "release": 0.06, "chorus": 0.3},
  "strings": {"wave": "saw", "voices": 3, "detune": 14, "spread": 0.6, "cutoff": 3200, "attack": 0.25, "decay": 0.3, "sustain": 0.85, "release": 0.6, "vibrato": 0.08, "vibratoDelay": 0.4, "reverb": 0.3},
  "bell": {"wave": "sine", "wave2": "sine", "level2": 0.45, "pitch2": 19, "detune2": 2, "attack": 0.001, "decay": 1.4, "sustain": 0, "release": 1.2, "reverb": 0.3},
  "flute": {"wave": "triangle", "noise": 0.03, "cutoff": 3000, "attack": 0.06, "decay": 0.1, "sustain": 0.9, "release": 0.15, "vibrato": 0.1, "vibratoDelay": 0.3},
  "chip": {"wave": "square", "filter": "off", "attack": 0, "decay": 0, "sustain": 1, "release": 0.02},
  "chipLead": {"wave": "pulse", "width": 0.25, "filter": "off", "attack": 0, "decay": 0, "sustain": 1, "release": 0.02, "vibrato": 0.2, "vibratoDelay": 0.15, "vibratoRate": 6},
  "chipBass": {"wave": "pulse", "filter": "off", "attack": 0, "decay": 0, "sustain": 1, "release": 0.02, "note": 36, "macroRate": 4, "macro": {"steps": [{"width": 0.06}, {"width": 0.2}, {"width": 0.5}, {"width": 0.8}, {"width": 0.94}, {"width": 0.8}, {"width": 0.5}, {"width": 0.2}], "loop": true, "slide": true}},
  "chipNoise": {"level1": 0, "noise": 1, "noise.type": "lfsr", "filter": "off", "attack": 0, "decay": 0.12, "sustain": 0, "release": 0.05},
  "chipKick": {"wave": "triangle", "filter": "off", "attack": 0, "decay": 0.16, "sustain": 0, "release": 0.05, "note": 48, "macro": [{"wave": "square", "pitch": 12}, {"wave": "triangle", "pitch": 5}, {"wave": "triangle", "pitch": 0}, {"wave": "triangle", "pitch": -5}, {"wave": "triangle", "pitch": -10, "volume": 0.8}, {"wave": "triangle", "pitch": -14, "volume": 0.6}]},
  "chipSnare": {"wave": "pulse", "noise.type": "lfsr", "filter": "off", "attack": 0, "decay": 0.16, "sustain": 0, "release": 0.05, "note": 57, "macro": [{"wave": "noise", "pitch": 24}, {"wave": "square", "pitch": 0}, {"wave": "square", "pitch": -5, "volume": 0.9}, {"wave": "noise", "pitch": 18, "volume": 0.8}, {"wave": "noise", "pitch": 14, "volume": 0.6}, {"wave": "noise", "pitch": 12, "volume": 0.45}]},
  "chipHat": {"wave": "pulse", "noise.type": "lfsr", "filter": "off", "attack": 0, "decay": 0.05, "sustain": 0, "release": 0.02, "note": 72, "macro": [{"wave": "noise", "pitch": 30}, {"wave": "noise", "pitch": 26, "volume": 0.6}, {"wave": "noise", "pitch": 24, "volume": 0.3}]},
  "kick": {"wave": "sine", "filter": "off", "pitchSweep": 30, "pitchSweepDecay": 0.06, "pitchSweepAttack": 0, "attack": 0, "decay": 0.3, "sustain": 0, "release": 0.1, "note": 36},
  "snare": {"wave": "triangle", "level1": 0.6, "noise": 1, "filter": "highpass", "cutoff": 500, "resonance": 0.05, "pitchSweep": 12, "pitchSweepDecay": 0.04, "pitchSweepAttack": 0, "attack": 0, "decay": 0.17, "sustain": 0, "release": 0.08, "note": 52},
  "hat": {"level1": 0, "noise": 1, "filter": "highpass", "cutoff": 7000, "attack": 0, "decay": 0.05, "sustain": 0, "release": 0.03, "note": 60},
  "sample": {"wave": "sample", "filter": "off", "attack": 0, "decay": 0, "sustain": 1, "release": 0.03}
 },
 "sounds": {
  "coin": {"patch": {"wave": "square", "filter": "off", "attack": 0, "decay": 0.3, "sustain": 0, "release": 0.2}, "notes": [[0, 83, 0.07, 0.8], [0.07, 88, 0.4, 0.8]]},
  "jump": {"patch": {"wave": "square", "width": 0.3, "filter": "off", "attack": 0, "decay": 0.25, "sustain": 0, "release": 0.05}, "notes": [[0, 57, 0.22, 0.8, 78, 0.2]]},
  "laser": {"patch": {"wave": "saw", "cutoff": 6000, "attack": 0, "decay": 0.24, "sustain": 0, "release": 0.05}, "notes": [[0, 98, 0.24, 0.8, 58, 0.22]]},
  "explosion": {"patch": {"wave": "sine", "level1": 0.9, "noise": 1, "cutoff": 180, "sweep": 50, "sweepAttack": 0, "sweepDecay": 0.55, "sweepSustain": 0, "pitchSweep": 24, "pitchSweepDecay": 0.25, "pitchSweepAttack": 0, "distortion": 0.5, "attack": 0, "decay": 0.9, "sustain": 0, "release": 0.3}, "notes": [[0, 30, 0.9, 1]]},
  "hit": {"patch": {"wave": "square", "noise.type": "lfsr", "filter": "off", "attack": 0, "decay": 0.12, "sustain": 0, "release": 0.05, "macro": [{"wave": "noise", "pitch": 12}, {"wave": "square", "pitch": 0}, {"wave": "square", "pitch": -5}, {"wave": "noise", "pitch": 4, "volume": 0.7}, {"wave": "noise", "pitch": 0, "volume": 0.5}, {"wave": "noise", "pitch": -4, "volume": 0.3}]}, "notes": [[0, 50, 0.12, 0.9]]},
  "shoot": {"patch": {"wave": "pulse", "width": 0.25, "filter": "off", "attack": 0, "decay": 0.16, "sustain": 0, "release": 0.03, "macroRate": 60, "macro": [{"wave": "noise", "pitch": 30}, {"wave": "pulse", "pitch": 19}, {"pitch": 14}, {"pitch": 9}, {"pitch": 4}, {"pitch": 0}, {"pitch": -5, "volume": 0.8}, {"pitch": -10, "volume": 0.6}, {"pitch": -15, "volume": 0.4}]}, "notes": [[0, 76, 0.16, 0.8]]},
  "powerup": {"patch": {"wave": "square", "filter": "off", "attack": 0, "decay": 0.2, "sustain": 0.5, "release": 0.15, "macroRate": 16, "macro": {"steps": [{"pitch": 0}, {"pitch": 4}, {"pitch": 7}, {"pitch": 12}, {"pitch": 16}, {"pitch": 19}, {"pitch": 24}, {"pitch": 19}], "loop": [6, 8]}}, "notes": [[0, 60, 0.6, 0.7]]},
  "blip": {"patch": {"wave": "square", "filter": "off", "attack": 0, "decay": 0.06, "sustain": 0, "release": 0.02}, "notes": [[0, 81, 0.06, 0.7]]},
  "click": {"patch": {"wave": "sine", "noise": 0.4, "filter": "off", "attack": 0, "decay": 0.015, "sustain": 0, "release": 0.01}, "notes": [[0, 96, 0.02, 0.8]]},
  "zap": {"patch": {"wave": "saw", "cutoff": 5000, "vibrato": 7, "vibratoRate": 32, "attack": 0, "decay": 0.3, "sustain": 0, "release": 0.05}, "notes": [[0, 84, 0.3, 0.8, 55, 0.3]]},
  "bounce": {"patch": {"wave": "sine", "filter": "off", "attack": 0, "decay": 0.14, "sustain": 0, "release": 0.04}, "notes": [[0, 55, 0.14, 0.9, 69, 0.07]]},
  "pop": {"patch": {"wave": "sine", "filter": "off", "attack": 0, "decay": 0.07, "sustain": 0, "release": 0.02}, "notes": [[0, 70, 0.07, 0.9, 86, 0.04]]},
  "win": {"patch": {"wave": "square", "wave2": "square", "level2": 0.5, "pitch2": 12, "filter": "off", "attack": 0, "decay": 0.3, "sustain": 0.4, "release": 0.2, "echo": 0.2}, "notes": [[0, 72, 0.1, 0.7], [0.11, 76, 0.1, 0.7], [0.22, 79, 0.1, 0.7], [0.33, 84, 0.45, 0.8]]},
  "lose": {"patch": {"wave": "triangle", "wave2": "square", "level2": 0.3, "cutoff": 2500, "attack": 0, "decay": 0.3, "sustain": 0.5, "release": 0.2}, "notes": [[0, 67, 0.16, 0.8], [0.17, 63, 0.16, 0.8], [0.34, 60, 0.16, 0.8], [0.51, 55, 0.5, 0.8, 43, 0.5]]}
 },
 "chords": {"5": [0, 7], "6": [0, 4, 7, 9], "7": [0, 4, 7, 10], "9": [0, 4, 7, 10, 14], "major": [0, 4, 7], "maj": [0, 4, 7], "minor": [0, 3, 7], "min": [0, 3, 7], "m": [0, 3, 7], "dim": [0, 3, 6], "aug": [0, 4, 8], "sus2": [0, 2, 7], "sus4": [0, 5, 7], "sus": [0, 5, 7], "power": [0, 7], "octave": [0, 12], "m6": [0, 3, 7, 9], "dom7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "min7": [0, 3, 7, 10], "dim7": [0, 3, 6, 9], "m7b5": [0, 3, 6, 10], "mmaj7": [0, 3, 7, 11], "add9": [0, 4, 7, 14], "maj9": [0, 4, 7, 11, 14], "m9": [0, 3, 7, 10, 14]},
 "orders": {"up": 0, "down": 1, "updown": 2, "written": 3, "aswritten": 3, "given": 3, "random": 4},
 "macroWaves": {"sine": 0, "triangle": 1, "saw": 2, "pulse": 3, "square": 3, "noise": 4},
 "lengths": {"whole": 4, "half": 2, "quarter": 1, "eighth": 0.5, "sixteenth": 0.25, "thirtysecond": 0.125},
 "lengthLetters": {"w": 4, "h": 2, "q": 1, "e": 0.5, "s": 0.25, "t": 0.125},
 "midi": {"types": ["noteOff", "noteOn", "notePressure", "control", "program", "pressure", "bend", "sysex", "timeCode", "songPosition", "songSelect", "tuneRequest", "clock", "start", "continue", "stop", "sensing", "reset", "other", "devices", "tempo", "learned", "set"], "does": ["devices", "listen", "input", "output", "send", "play", "through", "map", "learn", "unmap", "clock", "stop"], "functions": ["onMidi", "onMidiNote", "onMidiNoteOff", "onMidiControl", "onMidiDevices", "useMidiHooks", "sendMidi", "sendMidiNote", "sendMidiNoteOff", "sendMidiControl", "sendMidiBend", "sendMidiProgram", "sendMidiClock", "midiDevices", "useMidiInput", "useMidiOutput", "midiInput", "midiOutput", "receiveMidi", "stopMidi"], "synthFunctions": ["playFromMidi", "sendToMidi", "mapMidi", "learn", "unmapMidi", "midiInput", "midiOutput"], "choices": {"settings": ["device", "channel"], "all": "all", "none": "no devices", "unavailable": "no MIDI here"}},
 "voices": {"robot": {"help": "A machine: the voice multiplied by a 50 Hz wave, ringing in a metal pipe.", "values": {"fx.ring": 1, "fx.ring_freq": 50, "fx.comb": 0.45, "fx.comb_freq": 110, "fx.comb_feedback": 0.8, "fx.bits": 10}}, "chipmunk": {"help": "Small and squeaky: everything seven semitones higher.", "values": {"fx.pitch": 7}}, "monster": {"help": "Huge and deep: seven semitones lower, with a growl and a little room.", "values": {"fx.pitch": -7, "fx.drive": 0.25, "send.reverb": 0.3, "reverb.size": 0.7, "reverb.damping": 0.6}}, "cave": {"help": "Far inside a cave: long echoes and an enormous, dark space.", "values": {"send.delay": 0.5, "send.reverb": 0.6, "delay.time": 0.38, "delay.feedback": 0.55, "delay.tone": 2500, "reverb.type": 3, "reverb.size": 0.4, "reverb.damping": 0.55}}, "telephone": {"help": "Down an old phone line: only the middle of the voice, coarse and a little crushed.", "values": {"filter.type": 3, "filter.slope": 1, "filter.cutoff": 1200, "filter.resonance": 0.2, "fx.drive": 0.2, "fx.bits": 8, "fx.downsample": 6}}, "alien": {"help": "Not from here: higher, multiplied by a 180 Hz wave, with a slow metallic sweep.", "values": {"fx.pitch": 4, "fx.ring": 0.8, "fx.ring_freq": 180, "fx.comb": 0.4, "fx.comb_freq": 600, "fx.comb_feedback": 0.75, "fx.comb_rate": 0.4, "fx.comb_depth": 0.5, "send.chorus": 0.4}}, "whisper": {"help": "Hoarse and breathy: the voice's pitch blurred into noise, with its low end taken off.", "values": {"filter.type": 2, "filter.cutoff": 500, "filter.resonance": 0, "fx.ring": 1, "fx.ring_wave": 1, "fx.ring_freq": 350}}},
 "buffer": {"functions": ["setSoundBuffer", "soundBuffer"], "words": {"small": 1024, "medium": 2048, "large": 4096, "auto": "auto"}, "least": 256, "most": 16384, "event": "buffer", "reads": ["frames", "delay", "thread", "underruns", "setting"], "threads": ["audio", "page"]},
 "song": {"does": ["play", "resume", "pause", "stop", "seek", "volume", "repeat", "mute", "solo", "loopPattern", "replace"], "functions": ["stop", "pause", "resume", "seek", "mute", "unmute", "solo", "loopPattern", "replace"]},
 "microphone": {"names": {"pitch": "pitchShift", "ring": "ringMod", "gain": "micGain", "gate": "micGate", "gaterelease": "micGateRelease"}, "gate": -50, "states": ["asking", "on", "refused", "none", "busy", "unavailable", "off"], "functions": ["useMicrophone", "stopMicrophone", "recordSound", "startRecording", "stopRecording", "recordOutput", "saveSound", "receiveSoundEvents", "voiceNames"], "micFunctions": ["listen", "mute", "record", "whenReady", "close"], "takeFunctions": ["onDone", "whenDone", "stopRecording"], "events": ["microphone", "recorded", "saved"], "longestRecording": 120, "usualRecording": 30}
}
''')
# NAMES:END


# ---------------------------------------------------------------- names, notes and mistakes

def _key(name):
    """A name without regard to capitals, `_`, `.`, `-` or spaces: vibrato_rate, vibratoRate and "vibrato.rate" are one."""
    return re.sub(r"[_.\s-]", "", str(name).lower())


def _snake(name):
    """A name in Python's spelling: vibratoRate and "filter.cutoff" are vibrato_rate and filter_cutoff."""
    return re.sub(r"[.\s-]+", "_", re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)).lower()


def _shown(v):
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_shown(x) for x in v) + "]"
    return str(v)


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _clamp(v, low, high):
    return min(high, max(low, v))


_SETTINGS = {}      # every way a setting can be written, as _key(name) -> its entry
_SHOWN = []         # the names to show a person: the friendly ones, then the engine's own
_FRIENDLY = []      # the friendly ones alone
_PRESETS = {}       # _key(name) -> the name of a ready-made synth
_SOUNDS = {}        # _key(name) -> the name of a ready-made sound
_DEFAULTS = {}      # engine id -> the engine's own value for a setting
_BY_ID = {}         # engine id -> the engine's name for a setting
_VOICES = {"rows": {}, "all": []}    # the voice changers: name -> {engine id: value}, and every id any of them sets
_MIC_NAMES = {}     # a setting as the microphone says it (_key) -> the name every synth knows it by


def _read_names():
    by_name = {}
    for s in _NAMES.get("settings", ()):
        entry = dict(s, scale=1)
        by_name[s["name"]] = entry
        _SETTINGS[_key(s["name"])] = entry
    friendly = []
    for alias, to in _NAMES.get("names", {}).items():
        entry = by_name.get(to["setting"])
        if entry is None:
            continue
        _SETTINGS[_key(alias)] = entry if to.get("scale", 1) == 1 else dict(entry, scale=to["scale"])
        friendly.append(_snake(alias))
    _FRIENDLY[:] = friendly
    _SHOWN[:] = friendly + [n for n in (_snake(name) for name in by_name) if n not in friendly]
    for name in _NAMES.get("synths", {}):
        _PRESETS[_key(name)] = name
    for name in _NAMES.get("sounds", {}):
        _SOUNDS[_key(name)] = name
    for s in _NAMES.get("settings", ()):
        _DEFAULTS[s["id"]] = s["default"]
        _BY_ID[s["id"]] = s["name"]
    every = []
    for name, voice in _NAMES.get("voices", {}).items():
        row = _VOICES["rows"][name] = _patch_of(voice.get("values"), name, False)
        every.extend(pid for pid in row if pid not in every)
    _VOICES["all"] = every
    _MIC_NAMES.update(_NAMES.get("microphone", {}).get("names", {}))


def _setting(name):
    return _SETTINGS.get(_key(name)) if isinstance(name, str) else None


def _nearest(word, names):
    """The name in `names` nearest to `word`, when one is near enough to be what was meant."""
    a = _key(word)
    best = None
    # A short word has to be very near: one slip in four letters, two in eight, three in anything longer.
    best_cost = (1 if len(a) <= 4 else 2 if len(a) <= 8 else 3) + 1
    for name in names:
        b = _key(name)
        if b.startswith(a) and len(a) >= 4:
            return name
        row = list(range(len(b) + 1))
        for i in range(1, len(a) + 1):
            last, row[0] = row[0], i
            for j in range(1, len(b) + 1):
                keep = row[j]
                row[j] = min(row[j] + 1, row[j - 1] + 1, last + (0 if a[i - 1] == b[j - 1] else 1))
                last = keep
        if row[-1] < best_cost:
            best_cost, best = row[-1], name
    return best


def _meant(word, names):
    near = _nearest(word, names) if isinstance(word, str) else None
    return " Did you mean %s?" % _shown(near) if near else ""


def _setting_value(entry, value, said):
    """A setting's value as the engine's number, from what a person wrote: a number, a choice by name ("saw"), True or False."""
    kind, choices = entry["kind"], entry.get("choices") or []
    if kind == "choice":
        if isinstance(value, str):
            word = value.lower().strip()
            for w in (word, _NAMES.get("choiceWords", {}).get(word), word + "db"):
                if w in choices:
                    return choices.index(w)
            words = [w for w, to in _NAMES.get("choiceWords", {}).items() if to in choices]
            raise ValueError("%s: %s is not one of its choices.%s They are: %s"
                             % (said, _shown(value), _meant(value, choices + words), ", ".join(choices)))
        if _is_number(value) and ("%gdb" % value) in choices:
            return choices.index("%gdb" % value)
    if kind == "bool":
        if value is True or value == "on":
            return 1
        if value is False or value == "off":
            return 0
    if not _is_number(value):
        wants = ("one of " + ", ".join(choices) if kind == "choice" else "True or False" if kind == "bool"
                 else "a number from %g to %g" % (entry["min"] / entry["scale"], entry["max"] / entry["scale"]))
        raise ValueError("%s needs %s, not %s" % (said, wants, _shown(value)))
    return _clamp(value * entry["scale"], entry["min"], entry["max"])


def _patch_of(given, said, strict=True, into=None):
    """Settings as a person wrote them -> {engine id: number}, added to `into`. A mistake is said in plain words."""
    into = {} if into is None else into
    for name, value in (given or {}).items():
        if name in ("note", "preset", "macro"):
            continue
        entry = _setting(name)
        if entry is None:
            if strict:
                raise ValueError("%s: there is no setting called %s.%s" % (said, _shown(name), _meant(name, _SHOWN)))
            continue
        if entry["name"].endswith(".sample"):
            into[entry["id"]] = 0
            continue
        try:
            into[entry["id"]] = _setting_value(entry, value, "%s: %s" % (said, name))
            # "square" is the pulse wave at an even width (the width is four ids after the wave).
            if isinstance(value, str) and value.lower().strip() == "square" and "pulse" in (entry.get("choices") or ()):
                into[entry["id"] + 4] = 0.5
        except ValueError:
            if strict:
                raise
    return into


_NO_VOICE = ("none", "plain", "off", "normal", "")


def _voice_name(name):
    """A voice's name as written -> its name here, "none" for the plain voice, or None for a name that is not a voice."""
    if name is None or name is False:
        return "none"
    k = _key(name)
    return "none" if k in _NO_VOICE else k if k in _VOICES["rows"] else None


def _wear_voice(worn, patch, name):
    """PUT A VOICE ON, as synths.js does (its wearVoice; the rule is in docs/commands.md under `set`). `worn` is
    what is remembered between voices ({"voice", "under"}) and `patch` the settings by engine id. The first voice
    keeps what the settings it may touch were; every voice after starts by putting those back, and "none" is how
    things were before any. A setting of the whole engine (the echo's time, the reverb's size) is touched only if
    this voice or the last names it. The player does the same from the one word sent, so only `patch` changes here."""
    rows, every = _VOICES["rows"], _VOICES["all"]
    row, last = rows.get(name, {}), rows.get(worn["voice"], {})
    if worn["under"] is None:
        worn["under"] = {pid: patch[pid] for pid in every if pid in patch}
    for pid in every:
        if pid >= 200 and pid not in row and pid not in last:
            continue
        patch[pid] = row[pid] if pid in row else worn["under"].get(pid, _DEFAULTS.get(pid))
    worn["voice"] = name
    if name == "none":
        worn["under"] = None


def _sendable(given):
    """Settings as they are sent: as written, with a sample given as its id."""
    return {name: (value._sample or value._id) if isinstance(value, (Synth, _Slot)) else value for name, value in given.items()}


class _Slot:
    """A sample by its id alone, among a synth's settings: one loaded from a file named there."""

    def __init__(self, id):
        self._sample = self._id = id


def _sample_file(s, path, note=None, loop=None):
    """A sound file as a sample: the command that loads it is written, and the id it goes by given back."""
    sid = s.id("w")
    c = {"op": "sample", "id": sid, "name": path}
    if note is not None:
        c["note"] = note_number(note)
    if loop:
        c["loop"] = list(loop) if isinstance(loop, (list, tuple)) else True
    data = _file(path)
    if data is not None:
        c["bytes"] = data       # Python has the file (it may be on another computer than the page)
    else:
        c["url"] = path         # the page fetches it from beside the scene
    s.command(c)
    return sid


def _with_samples(s, given, patch, said, note=None, loop=None):
    """SAMPLES AMONG A SYNTH'S SETTINGS, as synths.js has them. `sample` is a sample from load_sample, a recording,
    or the name of a sound file (which is loaded); giving one turns that oscillator's wave to "sample" unless a
    wave is said too, so lead.sample = load_sample("piano.wav") is all it takes to put a recording under a synth's
    filter and envelope. The wave "sample" with no sample to play is not set: it is said once, and the wave stays."""
    out = dict(given)

    def names(which):
        return [n for n in out if (_setting(n) or {}).get("name") == which]
    for name, value in given.items():
        entry = _setting(name)
        if entry is None or not entry["name"].endswith(".sample"):
            continue
        if isinstance(value, str) and value.strip():
            out[name] = _Slot(_sample_file(s, value, note, loop))
        elif not (isinstance(value, (Synth, _Slot)) and value._sample):
            raise ValueError('%s: sample needs a sample from load_sample, a recording, or the name of a sound file, as in '
                             'lead.sample = load_sample("piano.wav"), not %s' % (said, _shown(value)))
        wave = entry["name"].replace("sample", "wave")
        if not names(wave):
            out[wave] = "sample"
    for which in ("osc1", "osc2"):
        for name in names(which + ".wave"):
            value = out[name]
            if not (value == 4 and not isinstance(value, bool) or (isinstance(value, str) and value.lower().strip() == "sample")):
                continue
            if _setting(which + ".sample")["id"] in patch or names(which + ".sample"):
                continue
            wave = _setting(which + ".wave")
            now = wave["choices"][int(patch.get(wave["id"], wave["default"]))]
            _tell('%s = "sample" needs a sample to play, and this synth has none, so its wave stays %s. Give it one first: '
                  'lead.sample = load_sample("piano.wav"), or make_synth(sample="piano.wav").' % (name, _shown(now)))
            del out[name]
    return out


_SEMITONES = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
_NOTE = re.compile(r"^\s*([a-gA-G])([#b♯♭]*)(-?\d+)?\s*$")


def note_number(note):
    """A note as a number: "C4" is 60, "A4" is 69, "F#3" and "Bb5" work, and a number is itself."""
    if _is_number(note):
        return note
    if isinstance(note, str):
        m = _NOTE.match(note)
        if m:
            n = _SEMITONES[m.group(1).lower()]
            for c in m.group(2):
                n += 1 if c in "#♯" else -1
            return 12 * ((4 if m.group(3) is None else int(m.group(3))) + 1) + n
        try:
            n = float(note)
            if math.isfinite(n):
                return int(n) if n == int(n) else n
        except ValueError:
            pass
    raise ValueError('%s is not a note. Write a note as a name like "C4", "F#3" or "Bb5", or as a number, where 60 is middle C'
                     % _shown(note))


def _note_numbers(note):
    return [note_number(n) for n in note] if isinstance(note, (list, tuple)) else [note_number(note)]


_KINDS_SHOWN = ["major", "minor", "dim", "aug", "sus2", "sus4", "5", "6", "m6", "7", "maj7", "m7", "dim7", "m7b5",
                "mmaj7", "add9", "9", "maj9", "m9", "octave"]
_ROOT = re.compile(r"^\s*([a-gA-G][#b\u266f\u266d]*(?:-?\d+)?)\s*(.*?)\s*$")


def _chord_kind(kind):
    """The kind of chord a person named: "m7", "Maj7", "M7" (a capital M is major), "minor"."""
    k = str(kind).strip()
    if re.match(r"^M(?!aj|in|AJ|IN)", k):
        k = "maj" + k[1:]
    k = re.sub(r"[\s_-]", "", k.lower())
    if k in ("maj", ""):
        k = "major"
    return _NAMES.get("chords", {}).get(k)


def chord_notes(name, kind=None):
    """The notes of a chord, as numbers: chord_notes("Cm7") is [60, 63, 67, 70], chord_notes("C3", "minor") is [48, 51, 55].
    A letter followed by a number is always a note, so "C7" is the note C in octave 7: a seventh chord is "Cdom7",
    or ("C", "7"). With no kind at all, it is a major chord."""
    if isinstance(name, (list, tuple)):
        return [note_number(n) for n in name]
    root = name
    if kind is None and isinstance(name, str):
        m = _ROOT.match(name)
        if m:
            root, kind = m.group(1), m.group(2)
    base = note_number(root)
    steps = _chord_kind("" if kind is None else kind)
    if steps is None:
        raise ValueError("%s is not a kind of chord.%s The kinds are: %s"
                         % (_shown(kind), _meant(str(kind), list(_NAMES.get("chords", {}))), ", ".join(_KINDS_SHOWN)))
    return [base + s for s in steps]


def _notes_of(what):
    """What play() is given -> a list of note numbers: a note, a list of notes, or a chord by name ("Cm7")."""
    if isinstance(what, (list, tuple)):
        return [note_number(n) for n in what]
    if isinstance(what, str) and not _NOTE.match(what) and re.match(r"^\s*[a-gA-G]", what):
        m = _ROOT.match(what)
        if m and _chord_kind(m.group(2)) is not None:
            return chord_notes(what)
        if m:
            near = _nearest(m.group(2), list(_NAMES.get("chords", {})))
            raise ValueError('%s is not a note or a chord.%s A note is written "C4" or "F#3", and a chord "Cm", "Cmaj7" or "Csus4"'
                             % (_shown(what), " Did you mean %s?" % _shown(m.group(1) + near) if near else ""))
    return [note_number(what)]


def _order_of(order, said):
    """The order of an arpeggio as the engine's number, from "up", "down", "up-down", "as written" or "random"."""
    if order is None:
        return 0
    if _is_number(order) and 0 <= order <= 4:
        return int(order)
    found = _NAMES.get("orders", {}).get(_key(order))
    if found is None:
        raise ValueError("%s: %s is not an order an arpeggio can go in.%s The orders are: up, down, up-down, as written, random"
                         % (said, _shown(order), _meant(str(order), ["up", "down", "up-down", "as written", "random"])))
    return found


def _chord_of(chord, kind, said):
    """The chord an arpeggio is given -> its notes as numbers: a list of notes, a chord by name, or a root and a kind."""
    if chord is None:
        raise ValueError('%s needs a chord, as in %s("Cm7"), %s("C4", "minor") or %s(["C4", "E4", "G4"])' % (said, said, said, said))
    notes = chord_notes(chord, kind)
    if len(notes) > 8:
        raise ValueError("%s: an arpeggio has room for 8 notes, and this chord has %d" % (said, len(notes)))
    return notes


def _arp_of(notes, root, speed, order, said):
    """An arpeggio as a command carries it: semitones from the note the voice was started on, a rate and an order."""
    offsets = [n - root for n in notes]
    if any(v != int(v) or not -128 <= v <= 127 for v in offsets):
        raise ValueError("%s: the notes of an arpeggio have to be whole notes within ten octaves of the first one" % said)
    return {"offsets": [int(v) for v in offsets], "rate": 50 if speed is None else _amount(speed, "%s: speed" % said, 0.1, 1000),
            "order": _order_of(order, said)}


def _check_macro(macro, said):
    """A step macro as a person wrote it: a list of steps, or {"steps", "loop", "slide", "release"}. A mistake is said here."""
    if macro is None or macro is False:
        return None
    spec = {"steps": macro} if isinstance(macro, (list, tuple)) else macro
    steps = spec.get("steps") if isinstance(spec, dict) else None
    if not isinstance(steps, (list, tuple)) or not steps:
        raise ValueError('%s: a macro needs a list of steps, as in [{"pitch": 0}, {"pitch": 4}, {"pitch": 7}], not %s' % (said, _shown(macro)))
    if len(steps) > 64:
        raise ValueError("%s: a macro has room for 64 steps, and this has %d" % (said, len(steps)))
    waves = _NAMES.get("macroWaves", {})
    for step in steps:
        o = dict(zip(("wave", "pitch", "width", "cutoff", "volume"), step)) if isinstance(step, (list, tuple)) else step or {}
        wave = o.get("wave")
        if wave is not None and not _is_number(wave) and str(wave).lower() not in waves:
            raise ValueError("%s: %s is not a wave a step can switch to.%s They are: %s"
                             % (said, _shown(wave), _meant(str(wave), list(waves)), ", ".join(waves)))
        for name in ("pitch", "width", "cutoff", "volume"):
            if o.get(name) is not None and not _is_number(o[name]):
                raise ValueError("%s: a step's %s needs a number, not %s" % (said, name, _shown(o[name])))
    return macro


def length_beats(name):
    """A note length by name as a number of beats: "quarter" is 1, "eighth." is 0.75, "1/16" is 0.25, "q3" is two
    thirds. Also by letter (w h q e s t), "dotted quarter" and "eighth triplet". Not a length: None."""
    if not isinstance(name, str):
        return None
    text = re.sub(r"[\s_-]", "", name.lower())
    times = 1
    if text.startswith("dotted"):
        times, text = times * 1.5, text[6:]
    if text.endswith("triplet"):
        times, text = times * 2 / 3, text[:-7]
    if text.endswith("."):
        times, text = times * 1.5, text[:-1]
    if text.endswith("note"):
        text = text[:-4]
    if len(text) > 1 and re.search(r"[a-z]3$", text):
        times, text = times * 2 / 3, text[:-1]
    fraction = re.match(r"^(\d+)/(\d+)$", text)
    if fraction and int(fraction.group(2)) > 0:
        return 4 * int(fraction.group(1)) / int(fraction.group(2)) * times
    beats = _NAMES.get("lengths", {}).get(text, _NAMES.get("lengthLetters", {}).get(text))
    return None if beats is None else beats * times


_NOT_A_LENGTH = ('a number, or a note length by name: "whole", "half", "quarter", "eighth", "sixteenth" '
                 '(also "1/4", "q", and "quarter." for a dotted one)')


def _named_beats(value, said):
    beats = length_beats(value)
    if beats is None:
        raise ValueError("%s needs %s, not %s.%s" % (said, _NOT_A_LENGTH, _shown(value), _meant(value, list(_NAMES.get("lengths", {})))))
    return beats


def _beats_long(value, said):
    """In a line of notes a length is beats as a number, or a note length by name. It gives beats."""
    if value is None:
        return 1
    if isinstance(value, str):
        return _named_beats(value, said)
    if not _is_number(value) or not value > 0:
        raise ValueError('%s needs a number of beats, more than 0, or a note length such as "quarter", not %s' % (said, _shown(value)))
    return value


def _amount(value, said, least=0, most=1):
    if not _is_number(value):
        raise ValueError("%s needs a number from %g to %g, not %s" % (said, least, most, _shown(value)))
    return _clamp(value, least, most)


def _seconds(value, said):
    if not _is_number(value) or not value > 0:
        raise ValueError("%s needs a number of seconds, more than 0, not %s" % (said, _shown(value)))
    return value


_said = set()


def _tell(what):
    """Each thing said once, however often it happens. It does not stop the program."""
    if what in _said:
        return
    _said.add(what)
    print("synths: " + what, file=sys.stderr)


# ---------------------------------------------------------------- how the commands travel

class _Frames:
    """In a Pyctures scene: the commands of one frame are one batch, one command in the frame's own message."""

    def __init__(self, pyctures):
        self.p = pyctures
        self.batch = None
        self.into = None       # the frame's list of commands that the batch was put in
        ending = getattr(pyctures.S, "ending", None)
        if isinstance(ending, list):
            ending.append(self.stamp)    # Pyctures calls it as the frame is sent

    def add(self, c, clock):
        cmds = self.p.S.cmds
        if self.into is not cmds:
            # The first sound of this frame. The batch is in the frame now, and is filled until the frame is sent.
            self.batch = {"synths": COMMANDS, "now": clock(), "cmds": []}
            self.into = cmds
            line = getattr(self.p, "_user_line", lambda: 0)()
            cmds.append(["call", line, 0, getattr(self.p, "H_SOUND", H_SOUND), "send", [self.batch]])
        self.batch["cmds"].append(c)
        # The clock when the batch leaves. A Pyctures that does not call stamp() has the time of the last command.
        self.batch["now"] = clock()

    def turn(self, clock):
        """Which turn of the program this is: a frame, or the call the page made (the top of the file, a key press)."""
        return id(self.p.S.cmds), getattr(self.p.S, "frame_no", 0)

    def stamp(self):
        if self.batch is not None and self.into is self.p.S.cmds:
            self.batch["now"] = time.perf_counter()

    def page(self, id):
        """The page's own object for a synth (or, with no id, for all the sound): what a dial or a keyboard in the page is tied to."""
        p = self.p
        sound = p.JsRef(getattr(p, "H_SOUND", H_SOUND))
        return sound.output() if id is None else sound.synth(id)

    def listen(self, heard):
        """Ask the page for what its MIDI desk says. It comes with the next frame, as a call from the page that
        carries {"midi": the events as JSON text}, with each event's time already on Python's clock."""
        def told(e):
            text = e.get("midi") if hasattr(e, "get") else None
            if text:
                heard(json.loads(text))
        p = self.p
        p.JsRef(getattr(p, "H_SOUND", H_SOUND)).midi(told)

    def hear(self, heard):
        """Ask the page for what its player says back (the microphone, a recording that is over, a saved file) and
        for what was asked to be watched. It comes with the next frame, as {"sound": the events as JSON text}."""
        def told(e):
            text = e.get("sound") if hasattr(e, "get") else None
            if text:
                heard(json.loads(text))
        p = self.p
        p.JsRef(getattr(p, "H_SOUND", H_SOUND)).events(told)

    def watch(self, id, what="reading"):
        """Ask the page to say, with every frame for a while, what a synth is doing (no id: all the sound), or
        where the song is. Asked again twice a second while a program goes on reading."""
        p = self.p
        sound = p.JsRef(getattr(p, "H_SOUND", H_SOUND))
        if what == "position":
            sound.watchSong()
        else:
            sound.watch(id)

    def keeps_files(self):
        """Whether Python has real files beside the scene (`pyctures run`); in a browser the page keeps them."""
        return not getattr(self.p.S, "page_files", False)


class _Direct:
    """For a host that was connected: each command is handed over at once, as a batch of its own."""

    def __init__(self, send):
        self.send = send

    def add(self, c, clock):
        self.send({"synths": COMMANDS, "now": clock(), "cmds": [c]})

    def turn(self, clock):
        return _turn_by_the_clock(self, clock)

    def page(self, id):
        return None

    def listen(self, heard):
        pass        # a host hands over what its player's on_midi gave with receive_midi(events)

    def hear(self, heard):
        pass        # and what its player's on_sound_events gave with receive_sound_events(events)

    def watch(self, id, what="reading"):
        pass

    def keeps_files(self):
        return False


class _Nowhere:
    """No player: the program carries on, in silence."""

    def add(self, c, clock):
        pass

    def turn(self, clock):
        return _turn_by_the_clock(self, clock)

    def page(self, id):
        return None

    def listen(self, heard):
        pass

    def hear(self, heard):
        pass

    def watch(self, id, what="reading"):
        pass

    def keeps_files(self):
        return False


def _turn_by_the_clock(transport, clock):
    """With no frames to count, what is written within a twentieth of a second of the last thing is the same turn."""
    now = clock()
    last = getattr(transport, "_last", None)
    if last is None or now - last[0] > 0.05:
        last = transport._last = [now, (getattr(transport, "_last", None) or [0, 0])[1] + 1]
    last[0] = now
    return last[1]


_host = [None]      # the sound of a host that called connect()
_silent = [None]    # the sound of a program with no player


def connect(send, ids=""):
    """For a host: take every command yourself, as `send(batch)` is called with {"synths": 1, "now", "cmds"}.
    `ids` begins every id made, for two programs that share one player. connect(None) undoes it."""
    _host[0] = _Sound(_Direct(send), ids) if send is not None else None


def _sound():
    """The sound of the program that is running: where its commands go, and what it has made."""
    if _host[0] is not None:
        return _host[0]
    # Looked up each time: in a browser every scene has its own copy of the module.
    p = sys.modules.get("pyctures")
    S = getattr(p, "S", None)
    if S is not None and getattr(S, "ns", None) is not None:
        mine = getattr(S, "_synths", None)
        if mine is None:
            mine = _Sound(_Frames(p))
            S._synths = mine       # kept with the run, so a new run starts with nothing made
        return mine
    if _silent[0] is None:
        _silent[0] = _Sound(_Nowhere())
        if not (S is not None and getattr(S, "started", 0)):   # a scene that has been stopped says nothing
            _no_player()
    return _silent[0]


def _no_player():
    """A program started with plain Python: open it with Pyctures if that can be done, or say how to."""
    main = sys.modules.get("__main__")
    file = getattr(main, "__file__", None)
    name = os.path.basename(file) if file else "your_program.py"
    try:
        import importlib.util
        has_pyctures = importlib.util.find_spec("pyctures") is not None
    except (ImportError, ValueError):
        has_pyctures = False
    started_plainly = bool(
        file and file.endswith(".py") and os.path.isfile(file) and sys.argv
        and os.path.abspath(sys.argv[0]) == os.path.abspath(file)
        and not sys.flags.interactive and sys.platform != "emscripten")
    if started_plainly and has_pyctures and not os.environ.get("SYNTHS_NO_BROWSER"):
        print("synths: the sound is made in a web browser, so %s is being opened in one.\n"
              "        This is the same as:  pyctures run %s\n"
              "        Click the page to turn the sound on. Press Ctrl+C here to stop." % (name, name), file=sys.stderr)
        import subprocess
        try:
            code = subprocess.call([sys.executable, "-m", "pyctures", "run", os.path.abspath(file)])
        except KeyboardInterrupt:
            code = 0
        raise SystemExit(code)
    if has_pyctures:
        _tell("the sound is made in a web browser, so this program plays nothing when it is started with plain Python. "
              "Run it with:  pyctures run %s" % name)
    else:
        _tell("the sound is made in a web browser, by Pyctures, so this program plays nothing when it is started with "
              "plain Python. Install Pyctures (pip install pyctures) and run it with:  pyctures run %s" % name)


# ---------------------------------------------------------------- one program's sound

class _Sound:
    def __init__(self, transport, prefix=""):
        self.transport = transport
        self.prefix = prefix
        self.clock = time.perf_counter
        self.ids = 0
        self.handles = 0
        self.tempo = 120
        self.beat_zero = self.clock()
        self.main = None
        self.chip = None
        self.output = None
        self.lines = {}          # synth id -> the time its line of notes has reached
        self.turn = None         # when the lines begun in this turn of the program begin
        self.turn_of = None      # what told this turn from the last (see _Frames.turn)
        self.writing = None      # inside loop_notes: synth id -> [its steps, the beat it has reached]
        self._midi = None        # MIDI, made the first time it is used (see _Midi)
        self.mic = None          # the microphone, once it has been asked for
        self.takes = {}          # sample id -> a recording that is being made
        self.saves = {}          # the number of a save_sound -> what it gave back
        self.asks = 0
        self.hearing = False     # the page has been asked for what its player says back
        self.readings = {}       # synth id ("" for all the sound) -> what it was doing when the page last said
        self.watched = {}        # what the page was asked to watch -> when it was last asked
        self.position = dict(_NO_SONG)
        self.buffer_set = None   # what set_sound_buffer asked for: "auto" or frames
        self.buffer_asked = False
        self.buffer_said = None  # the buffer as the player last said it
        # THE SETTINGS EVERY SYNTH SHARES (the echo's time, the reverb's type): there is one echo and one reverb,
        # so one value of each, whoever set it. Kept here by engine id, and what every synth and sound_output() read.
        self.for_all = {}

    @property
    def midi(self):
        if self._midi is None:
            self._midi = _Midi(self)
        return self._midi

    def length(self, value, said):
        """A LENGTH is seconds as a number, or a note length by name, which is so many beats at the tempo now."""
        if isinstance(value, str):
            return _named_beats(value, said) * 60 / self.tempo
        if not _is_number(value) or not value > 0:
            raise ValueError('%s needs a number of seconds, more than 0, or a note length such as "quarter", not %s' % (said, _shown(value)))
        return value

    def line_at(self, key):
        """Where a synth's line of notes has reached. Lines begun in the same turn of the program (the same frame
        of a scene) begin on the same instant, so a melody and a bass written one after the other play together."""
        now = self.transport.turn(self.clock)
        if now != self.turn_of or self.turn is None:
            self.turn_of, self.turn = now, self.clock()
        at = self.lines.get(key)
        return self.turn if at is None or at < self.turn else at

    def write(self, synth, what, long, volume, pan, said):
        """The next thing in a synth's line: notes (or None, a rest) that last so many beats."""
        beats = _beats_long(long, said)
        vel = None if volume is None else _amount(volume, "%s: volume" % said)
        if self.writing is not None:
            line = self.writing.setdefault(synth._id, [[], 0])
            if what:
                line[0].append([line[1], what, beats * _HELD, 0.8 if vel is None else vel])
            line[1] += beats
            return
        at = self.line_at(synth._id)
        if what:
            c = {"op": "note", "id": synth._id, "note": what, "len": beats * 60 / self.tempo * _HELD, "t": at}
            if vel is not None:
                c["vel"] = vel
            if pan is not None:
                c["pan"] = _amount(pan, "%s: pan" % said, -1, 1)
            self.command(c)
        self.lines[synth._id] = at + beats * 60 / self.tempo

    def command(self, c):
        self.transport.add(c, self.clock)

    def share(self, patch, names=None):
        """What a patch says of the settings every synth shares is what they are, for everyone: of the settings
        named, or with no names of every one it has."""
        ids = patch if names is None else [(_setting(n) or {}).get("id", -1) for n in names]
        for pid in ids:
            if pid >= 200 and pid in patch:
                self.for_all[pid] = patch[pid]

    def hear_back(self):
        """Make sure this program is handed what the player says back. Asked once, the first time something needs it."""
        if not self.hearing:
            self.hearing = True
            self.transport.hear(self.receive)

    def watch(self, key, id, what="reading"):
        now = self.clock()
        if now - self.watched.get(key, -10) > 0.5:
            self.watched[key] = now
            self.hear_back()
            self.transport.watch(id, what)

    def reading(self, id):
        """What a synth is doing, as the page last said: {"samples", "level", "notes"}. Nothing yet: empty."""
        key = id or ""
        self.watch(key, id)
        return self.readings.get(key, _NO_READING)

    def receive(self, events):
        """What the player says back, as a list of plain dicts (see receive_sound_events)."""
        if isinstance(events, dict):
            events = [events]
        for e in events or ():
            if not isinstance(e, dict):
                continue
            kind = e.get("type")
            if kind == "recorded":
                take = self.takes.pop(e.get("id"), None)
                if take is not None:
                    take._finish(e)
            elif kind == "saved":
                saved = self.saves.pop(e.get("ask"), None)
                if saved is not None:
                    saved._finish(e)
            elif kind == "microphone":
                if self.mic is not None:
                    self.mic._said(e)
            elif kind == "reading":
                self.readings[e.get("id") or ""] = {"samples": list(e.get("samples") or ()), "level": list(e.get("level") or (0, 0)),
                                                    "notes": list(e.get("notes") or ())}
            elif kind == "position":
                self.position = {k: e.get(k, v) for k, v in _NO_SONG.items()}
            elif kind == _NAMES["buffer"]["event"]:
                self.buffer_said = {k: e.get(k) for k in _NAMES["buffer"]["reads"]}

    def id(self, letter):
        self.ids += 1
        return "%s%s%d" % (self.prefix, letter, self.ids)

    def when(self, said, after=None, at=None, beat=None):
        """When a call should happen, on Python's clock."""
        if isinstance(after, str):
            after = self.length(after, "%s: after" % said)      # after="half": a note length from now
        for name, value in (("at", at), ("beat", beat), ("after", after)):
            if value is not None and not _is_number(value):
                raise ValueError("%s: %s needs a number, not %s" % (said, name, _shown(value)))
        if at is not None:
            return at
        if beat is not None:
            return self.beat_zero + beat * 60 / self.tempo
        if after is not None:
            return self.clock() + after
        return self.clock()

    def main_synth(self):
        """The synth play_note and play_notes use."""
        if self.main is None:
            self.main = _make_synth(self, "keys", {})
        return self.main


_HELD = 0.95         # how much of its length a note in a line sounds for
# What is read back before the page has said anything: no wave, no level, no notes; and no song.
_NO_READING = {"samples": [], "level": [0, 0], "notes": []}
_NO_SONG = {"state": "none", "order": 0, "pattern": 0, "row": 0, "tick": 0, "speed": 0, "tempo": 0, "rounds": 0, "rows": 0, "orders": 0}


def _steps_of(tune, step, beat, hold, volume, said):
    """ "C4 E4:q G4 - C5:2", or a list of notes, chords (lists) and rests (None) -> the steps of a tune, in the
    steps' own units. `step` is how long a step is in those units, and `beat` how many of the units a beat is."""
    items = [i for i in re.split(r"[\s,|]+", tune.strip()) if i] if isinstance(tune, str) else tune
    if not isinstance(items, (list, tuple)) or not items:
        raise ValueError('%s needs notes to play, as in play_notes("C4 E4 G4 - C5"), not %s' % (said, _shown(tune)))
    hold = 0.9 if hold is None else _amount(hold, "%s: hold" % said, 0.01, 4)
    vel = 0.8 if volume is None else _amount(volume, "%s: volume" % said)
    steps = []
    at = 0
    for item in items:
        what, long = item, step
        if isinstance(item, str):
            m = re.match(r"^(.*?)(?::([^:]+))?$", item)
            what = m.group(1)
            # After a colon: a number is so many steps, and a note length ("q", "eighth", "1/4") is itself.
            if m.group(2) and re.match(r"^\d*\.?\d+$", m.group(2)):
                long = float(m.group(2)) * step
            elif m.group(2):
                beats = length_beats(m.group(2))
                if beats is None:
                    raise ValueError('%s: in %s, %s is not a length. After the colon write how many steps (":2") or a note '
                                     'length (":q", ":h", ":eighth", ":1/4")' % (said, _shown(item), _shown(m.group(2))))
                long = beats * beat
            if re.match(r"^[-._~]*$", what):
                what = None
            elif "+" in what:
                what = what.split("+")
        if what is not None:
            steps.append([_whole(at), _notes_of(what), _whole(long * hold), vel])
        at += long
    return steps, _whole(at)


def _whole(n):
    """A number without a needless fraction: 2.0 is 2."""
    return int(n) if isinstance(n, float) and n == int(n) else n


class Note:
    """A note that is sounding: what start() gives back."""

    def __init__(self, sound, synth, h):
        object.__setattr__(self, "_sound", sound)
        object.__setattr__(self, "_synth", synth)
        object.__setattr__(self, "_h", h)

    def _voice(self, **change):
        s = self._sound
        s.command(dict({"op": "voice", "id": self._synth, "h": self._h}, t=s.clock(), **change))
        return self

    def stop(self):
        """Let it go: it dies away over the synth's release."""
        s = self._sound
        s.command({"op": "off", "id": self._synth, "h": self._h, "t": s.clock()})
        return self

    def cut(self):
        """Cut it off at once."""
        return self._voice(kill=True)

    def slide_to(self, note, time=0):
        """Slide to another note over that many seconds."""
        return self._voice(pitch=note_number(note), glide=time)

    def __setattr__(self, name, value):
        if name == "pitch":
            self.slide_to(value, 0)
        elif name == "frequency":
            self._voice(freq=_amount(value, "frequency", 1, 20000))
        elif name == "volume":
            self._voice(vol=_amount(value, "volume", 0, 4))
        elif name == "pan":
            self._voice(pan=_amount(value, "pan", -1, 1))
        else:
            object.__setattr__(self, name, value)


class Arp(Note):
    """An arpeggio that is sounding: what arp() and start_arp() give back. Its chord can be changed as it plays."""

    def __init__(self, sound, synth, h, root, speed, order, now):
        Note.__init__(self, sound, synth, h)
        object.__setattr__(self, "_root", root)
        object.__setattr__(self, "_how", [speed, order])
        object.__setattr__(self, "_now", now)

    def change(self, chord, kind=None, *, speed=None, order=None, after=None, at=None, beat=None):
        """Another chord, without starting the note again: arp.change("Fm"), arp.change("F4", "minor"), or a list of notes."""
        how = self._how
        how[0] = how[0] if speed is None else speed
        how[1] = how[1] if order is None else order
        s = self._sound
        s.command({"op": "voice", "id": self._synth, "h": self._h,
                   "arp": _arp_of(_chord_of(chord, kind, "change"), self._root, how[0], how[1], "change"),
                   "t": s.when("change", after, at, beat)})
        object.__setattr__(self, "_now", (chord, kind))
        return self

    def __setattr__(self, name, value):
        if name == "chord":
            self.change(value)
        elif name == "speed":
            self.change(*self._now, speed=value)
        elif name == "order":
            self.change(*self._now, order=value)
        else:
            Note.__setattr__(self, name, value)


class Tune:
    """A tune that is playing: what play_notes() gives back."""

    def __init__(self, sound, id):
        self._sound = sound
        self.id = id

    def stop(self):
        """Stop it. Notes it has started finish by themselves."""
        self._sound.command({"op": "stop", "id": self.id, "t": self._sound.clock()})
        return self


class Song:
    """A song that is playing: what play_song() gives back."""

    def __init__(self, sound, id):
        object.__setattr__(self, "_sound", sound)
        object.__setattr__(self, "id", id)

    def _do(self, what, **more):
        self._sound.command(dict({"op": "song", "id": self.id, "do": what}, t=self._sound.clock(), **more))
        return self

    def stop(self):
        """Stop it, and go back to its start."""
        return self._do("stop")

    def pause(self):
        """Hold it where it is, until resume()."""
        return self._do("pause")

    def resume(self):
        return self._do("resume")

    def seek(self, order, row=0):
        """Go to a place in the song: a part of it (its order list, from 0), then a row of the pattern there."""
        return self._do("seek", order=int(_amount(order, "seek: the order", 0, 65535)), row=int(_amount(row, "seek: the row", 0, 255)))

    def _channel(self, channel, said):
        if channel is None or channel == "all":
            return {}
        if not isinstance(channel, int) or isinstance(channel, bool) or not 0 <= channel <= 31:
            raise ValueError("%s needs the number of a channel, counting from 0, or nothing for every channel, not %s"
                             % (said, _shown(channel)))
        return {"channel": channel}

    def mute(self, channel=None, on=True):
        """Silence one channel of the song (they count from 0), or with no channel all of them: song.mute(2),
        and song.mute(2, False) to hear it again."""
        return self._do("mute", on=bool(on), **self._channel(channel, "mute"))

    def unmute(self, channel=None):
        return self._do("mute", on=False, **self._channel(channel, "unmute"))

    def solo(self, channel=None, on=True):
        """Hear only the channels that are soloed: song.solo(2), and song.solo(2, False) or song.solo("all", False)
        to hear the rest again."""
        return self._do("solo", on=bool(on), **self._channel(channel, "solo"))

    def loop_pattern(self, on=True):
        """Stay on the pattern that is playing, round and round, until loop_pattern(False)."""
        return self._do("loopPattern", on=bool(on))

    def replace(self, song, *, files=None, patches=None):
        """Put an edited song in the place of this one as it plays: its bytes, its JSON as text, or the song as a
        dictionary. When the two have the same shape nothing stops, and the change is heard from the next row."""
        if isinstance(song, (bytes, bytearray)):
            more = {"bytes": base64.b64encode(bytes(song)).decode("ascii")}
        elif isinstance(song, str) and song.strip():
            more = {"text": song}
        elif isinstance(song, dict):
            more = {"text": json.dumps(song)}
        else:
            raise ValueError("replace needs the new song: its bytes, its JSON as text, or the song itself as a "
                             "dictionary, not %s" % _shown(song))
        if files:
            more["files"] = {name: base64.b64encode(bytes(data)).decode("ascii") if isinstance(data, (bytes, bytearray)) else data
                             for name, data in files.items()}
        if patches:
            more["patches"] = _song_patches(patches)
        return self._do("replace", **more)

    def channel(self, n):
        """One channel of the song (the first is 0), for a meter or a scope of its own: song.channel(3).level(),
        .samples(), .notes(). A frame late in a Pyctures scene, as a synth's are."""
        if not isinstance(n, int) or isinstance(n, bool) or not 0 <= n <= 31:
            raise ValueError("channel needs the number of a channel, counting from 0, not %s" % _shown(n))
        return _Reading(self._sound, "song:channel:%d" % n)

    @property
    def position(self):
        """Where the song is, for drawing it: {"state", "order", "pattern", "row", "tick", "speed", "tempo", "rounds",
        "rows", "orders"}, where state is "playing", "paused", "stopped" or "none". In a Pyctures scene it is what
        the page said with this frame, so a frame late; the first time it is read it is not known yet ("none")."""
        s = self._sound
        s.watch("song:position", None, "position")
        return dict(s.position)

    def __setattr__(self, name, value):
        if name == "volume":
            self._do("volume", vol=_amount(value, "volume", 0, 2))
        elif name == "repeat":
            self._do("repeat", repeat=bool(value))
        else:
            object.__setattr__(self, name, value)


class _Reading:
    """What one source of sound is doing, read back: samples(), level() and notes(), as a synth has them."""

    def __init__(self, sound, id):
        self._sound, self._id = sound, id

    def samples(self):
        return self._sound.reading(self._id)["samples"]

    def level(self):
        return self._sound.reading(self._id)["level"]

    def notes(self):
        return self._sound.reading(self._id)["notes"]


# What a setting is measured in, as a dial shows it (a dial in Hz turns evenly by pitch).
_UNITS = {"hz": "Hz", "seconds": "s", "semitones": "st", "cents": "ct", "octaves": "oct"}


class Synth:
    """A synth. Its settings are plain attributes: lead.cutoff = 800, print(lead.cutoff)."""

    def __init__(self, sound, id, patch, note, length):
        put = object.__setattr__
        put(self, "_sound", sound)
        put(self, "_id", id)
        put(self, "_patch", patch)
        put(self, "_note", note)
        put(self, "_length", length)
        put(self, "_sample", None)
        put(self, "_page", None)
        put(self, "_macro", None)
        put(self, "_worn", None)         # a voice changer, once one has been put on: {"voice", "under"}
        put(self, "_plain", None)        # what the voice settings were before sound_like() first changed them
        put(self, "_loop", False)

    # What is this object's own and not a setting of the engine.
    _OWN = ("voice", "loop")

    def _name(self, name):
        """A setting's name as this synth says it -> the name it has everywhere. (The microphone has words of its own.)"""
        return name

    # --- settings as attributes
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name == "macro":
            return self._macro
        entry = _setting(self._name(name))
        if entry is None:
            raise AttributeError("A synth has no setting called %s.%s" % (_shown(name), _meant(name, _SHOWN)))
        shared = entry["id"] >= 200 and self._sound is not None
        value = (self._sound.for_all if shared else self._patch).get(entry["id"], entry["default"])
        if entry["kind"] == "choice":
            return entry["choices"][int(value)]
        if entry["kind"] == "bool":
            return value == 1
        if entry["scale"] != 1:
            value = value / entry["scale"]
        return int(value) if entry["kind"] == "int" and value == int(value) else value

    def __setattr__(self, name, value):
        if name.startswith("_") or name in self._OWN:
            object.__setattr__(self, name, value)
        elif name == "macro":
            self.set_macro(value)
        elif _setting(self._name(name)) is not None:
            self.set({name: value})
        else:
            # A name that is nearly a setting is a slip, and says so; any other name is the program's own to use.
            near = _nearest(name, _SHOWN)
            if near:
                raise AttributeError("A synth has no setting called %s. Did you mean %s?" % (_shown(name), _shown(near)))
            object.__setattr__(self, name, value)

    def __repr__(self):
        return "<synth %s>" % self._id

    # --- notes
    def play(self, note=None, length=None, volume=None, *, pan=None, after=None, at=None, beat=None):
        """A note for a while: lead.play("E4", 0.5). A list of notes is a chord. No note: the synth's own (a drum's)."""
        s = self._sound
        c = {"op": "note", "id": self._id, "note": None if note is None else _notes_of(note),
             "len": self._length if length is None else s.length(length, "play: the length"),
             "t": s.when("play", after, at, beat)}
        if volume is not None:
            c["vel"] = _amount(volume, "play: volume")
        if pan is not None:
            c["pan"] = _amount(pan, "play: pan", -1, 1)
        s.command(c)
        return self

    def start(self, note=None, volume=None, *, pan=None, after=None, at=None, beat=None):
        """Start a note that stays until it is stopped: held = lead.start("C4"), then held.stop()."""
        s = self._sound
        s.handles = 1 if s.handles >= 0x7FFFFFF0 else s.handles + 1
        c = {"op": "note", "id": self._id, "note": None if note is None else _notes_of(note), "len": None,
             "h": s.handles, "t": s.when("start", after, at, beat)}
        if volume is not None:
            c["vel"] = _amount(volume, "start: volume")
        if pan is not None:
            c["pan"] = _amount(pan, "start: pan", -1, 1)
        s.command(c)
        return Note(s, self._id, s.handles)

    def arp(self, chord=None, *more, **how):
        """A chord from one voice, as a fast arpeggio: the sound of a C64 tune. lead.arp("Cm7"), lead.arp("C4", "minor"),
        lead.arp(["C4", "E4", "G4"]), then a length in seconds (half a second unless you say), and speed= (steps a
        second, 50), order= ("up", "down", "up-down", "as written", "random"), volume=, pan=, after=."""
        return self._arp(chord, more, how, "arp", 0.5)

    def start_arp(self, chord=None, *more, **how):
        """The same, staying until it is stopped: arp = lead.start_arp("Am"), arp.change("F"), arp.stop()."""
        return self._arp(chord, more, how, "start_arp", None)

    def _arp(self, chord, more, how, said, usual):
        kind, length = how.pop("kind", None), how.pop("length", None)
        for arg in more:       # a kind of chord (text) and a length (a number, or a note length by name), in either order
            if isinstance(arg, str) and length_beats(arg) is None:
                kind = arg
            elif isinstance(arg, str) or _is_number(arg):
                length = arg
        speed, order = how.pop("speed", None), how.pop("order", None)
        volume, pan = how.pop("volume", None), how.pop("pan", None)
        when = {k: how.pop(k, None) for k in ("after", "at", "beat")}
        if how:
            raise ValueError("%s takes length, kind, speed, order, volume, pan, after, at and beat, not %s" % (said, ", ".join(how)))
        notes = _chord_of(chord, kind, said)
        s = self._sound
        s.handles = 1 if s.handles >= 0x7FFFFFF0 else s.handles + 1
        c = {"op": "note", "id": self._id, "note": [notes[0]],
             "len": usual if length is None else self._sound.length(length, "%s: the length" % said), "h": s.handles,
             "arp": _arp_of(notes, notes[0], speed, order, said), "t": s.when(said, **when)}
        if volume is not None:
            c["vel"] = _amount(volume, "%s: volume" % said)
        if pan is not None:
            c["pan"] = _amount(pan, "%s: pan" % said, -1, 1)
        s.command(c)
        return Arp(s, self._id, s.handles, notes[0], speed, order, (chord, kind))

    def set_macro(self, macro):
        """A step macro: a short list of steps that every note of this synth plays through, fifty a second (the setting
        macro_rate), each changing the wave, pitch, pulse width, cutoff or volume. It is what makes chip drums.
        lead.set_macro([{"wave": "noise", "pitch": 24}, {"wave": "square"}, {"pitch": -5, "volume": 0.8}]); None takes it away.
        {"steps": [...], "loop": True, "slide": True, "release": a step} says more."""
        _check_macro(macro, "set_macro")
        object.__setattr__(self, "_macro", macro or None)
        self._sound.command({"op": "macro", "id": self._id, "macro": macro or None, "t": self._sound.clock()})
        return self

    def stop(self, note=None):
        """Let go of every note of this synth, or of one note: lead.stop("C4")."""
        c = {"op": "off", "id": self._id, "t": self._sound.clock()}
        if note is not None:
            c["note"] = _note_numbers(note)
        self._sound.command(c)
        return self

    def note_on(self, note, velocity=0.8):
        """A key going down: the note stays until note_off(note). What a keyboard calls."""
        s = self._sound
        s.command({"op": "note", "id": self._id, "note": _note_numbers(note), "len": None,
                   "vel": _amount(velocity, "note_on: velocity"), "t": s.clock()})

    def note_off(self, note):
        """A key coming up."""
        self.stop(note)

    def play_notes(self, notes, step=None, *, repeat=None, volume=None, hold=None, after=None, at=None, beat=None):
        """A tune on this synth: lead.play_notes("C4 E4 G4 - C5", 0.25, repeat=True)."""
        s = self._sound
        said = "play_notes"
        # A step given in seconds makes a tune in seconds. A step by name ("eighth"), or none (an eighth), makes
        # a tune in beats, which keeps to the tempo and changes speed when set_tempo is called as it plays.
        in_beats = not _is_number(step)
        if step is None:
            step = 0.5
        elif in_beats:
            if length_beats(step) is None:
                raise ValueError("%s: the time of a step needs %s, not %s" % (said, _NOT_A_LENGTH, _shown(step)))
            step = length_beats(step)
        else:
            step = _seconds(step, "%s: the time of a step" % said)
        steps, length = _steps_of(notes, step, 1 if in_beats else 60 / s.tempo, hold, volume, said)
        id = s.id("t")
        times = True if repeat is True else 1 if repeat in (None, False) else _amount(repeat, "%s: repeat" % said, 1, 1e9)
        c = {"op": "tune", "id": id, "synth": self._id, "steps": steps, "length": length, "repeat": times,
             "t": s.when(said, after, at, beat)}
        if in_beats:
            c["beats"] = True
        s.command(c)
        return Tune(s, id)

    # --- a tune a line at a time
    def note(self, what=None, length=None, *, volume=None, pan=None):
        """The next note of this synth's line: it begins where the last one ended. lead.note("C4", "quarter"), then
        lead.note("E4", "eighth"). The length is a note length by name or a number of beats (a quarter with nothing
        said). A chord's name or a list of notes plays them together."""
        if what is None:
            raise ValueError('note needs a note, as in note("C4", "quarter"). For a silence, use rest("quarter")')
        self._sound.write(self, _notes_of(what), length, volume, pan, "note")
        return self

    def chord(self, name=None, kind=None, length=None, *, volume=None, pan=None):
        """The next thing in the line is a chord: lead.chord("Cm", "whole"), lead.chord("C4", "minor", "half"),
        lead.chord(["C4", "E4", "G4"])."""
        if kind is not None and (not isinstance(kind, str) or length_beats(kind) is not None):
            kind, length = None, kind          # chord("Cm", "whole"): the second thing is the length
        if name is None:
            raise ValueError('chord needs a chord, as in chord("Cm", "whole")')
        self._sound.write(self, chord_notes(name, kind), length, volume, pan, "chord")
        return self

    def rest(self, length=None):
        """A silence in the line: lead.rest("quarter")."""
        self._sound.write(self, None, length, None, None, "rest")
        return self

    def start_line(self, *, after=None, at=None, beat=None):
        """Begin this synth's line again from now (or after=, at=, beat=): what is written next starts there."""
        s = self._sound
        s.line_at(self._id)
        s.lines[self._id] = max(s.when("start_line", after, at, beat), s.turn)
        return self

    # --- settings
    def set(self, settings=None, value=None, *, glide=None, slide=None, after=None, at=None, beat=None, **more):
        """Change several settings at once: lead.set(cutoff=800, resonance=0.4). glide=2 slides there over two seconds
        (slide=2 is the same, an older word for it). lead.set("cutoff", 800) and lead.set({"cutoff": 800}) are the
        same thing written other ways."""
        if isinstance(settings, str):
            given = {settings: value}
        elif isinstance(settings, dict):
            given = dict(settings)
        elif settings is None:
            given = {}
        else:
            raise ValueError("set needs settings, as in set(cutoff=800), not %s" % _shown(settings))
        given.update(more)
        if not given:
            raise ValueError("set needs settings, as in set(cutoff=800)")
        s = self._sound
        t = s.when("set", after, at, beat)
        given = self._given(given, t)
        if not given:
            return self
        _patch_of(given, "set", True, self._patch)
        s.share(self._patch, given)
        c = {"op": "set", "id": self._id, "set": _sendable(given), "t": t}
        if glide is None:
            glide = slide
        if glide is not None:
            c["glide"] = _amount(glide, "set: glide", 0, 60)
        s.command(c)
        return self

    def _given(self, given, at):
        """What set() was given, ready to send: a voice is put on, and the rest go by the names they have everywhere."""
        out = {}
        for name, value in given.items():
            if _key(name) == "voice":
                self._wear(value, at)
            else:
                out[self._name(name)] = value
        return _with_samples(self._sound, out, self._patch, "set")

    def get(self, name):
        """A setting by its name: lead.get("cutoff") is lead.cutoff."""
        return getattr(self, _snake(name) if _key(name) in ("voice", "loop", "listening") else name)

    # --- a voice changer
    @property
    def voice(self):
        """A voice changer on everything this synth plays: lead.voice = "robot". The voices are robot, chipmunk,
        monster, cave, telephone, alien and whisper (voice_names()), and "none" takes it off. Each is a handful of
        settings (the pitch shifter, the ring modulator, the comb, the filter, the echo), which can be turned
        further once the voice is on. Choosing another voice first puts back what the last one changed."""
        return self._worn["voice"] if self._worn else "none"

    @voice.setter
    def voice(self, name):
        self._wear(name, self._sound.clock())

    def _wear(self, name, at=None, send=True):
        # A control that keeps a choice as its number in the list gives the number.
        choices = ["none"] + list(_VOICES["rows"])
        if _is_number(name) and 0 <= name < len(choices) and name == int(name):
            name = choices[int(name)]
        voice = _voice_name(name) if isinstance(name, str) or name is None or name is False else None
        if voice is None:
            names = list(_VOICES["rows"])
            raise ValueError('%s is not a voice.%s The voices are: %s, and "none"' % (_shown(name), _meant(name, names), ", ".join(names)))
        if self._worn is None:
            object.__setattr__(self, "_worn", {"voice": "none", "under": None})
        # A voice may change what every synth shares (the cave's reverb), and takes it back when it is taken off.
        self._patch.update(self._sound.for_all)
        _wear_voice(self._worn, self._patch, voice)
        self._sound.share(self._patch)
        if send:
            self._sound.command({"op": "set", "id": self._id, "voice": voice, "t": self._sound.clock() if at is None else at})

    def sound_like(self, other):
        """Give this the voice and the voice effects of another: take.sound_like(mic) makes a recording sound as the
        microphone does now, whatever voice has been chosen and however its dials have been turned since."""
        if not isinstance(other, Synth):
            raise ValueError("sound_like needs the microphone or a synth to sound like, as in take.sound_like(mic), not %s" % _shown(other))
        _dress_like(self, other)
        return self

    def record(self, length=None, **how):
        """Record what this synth plays into a sample: take = lead.record(4). On the microphone, it records the
        microphone. See record_sound."""
        return _record_from(self._sound, dict(how, length=length, source=self), "record")

    @property
    def loop(self):
        """A sample or a recording that goes round and round while its note is held: drum.loop = True, or
        [first frame, the frame after the last]."""
        return self._loop

    @loop.setter
    def loop(self, on):
        object.__setattr__(self, "_loop", list(on) if isinstance(on, (list, tuple)) else bool(on))
        if self._sample:
            self._sound.command({"op": "sample", "id": self._sample, "loop": self._loop, "t": self._sound.clock()})

    # --- what it is doing now, for a program that draws it
    def samples(self):
        """The wave this synth is making, a list of numbers from -1 to 1: draw it for a scope. In a Pyctures scene
        it is what the page said with this frame, so a frame late, and empty until the page has first said."""
        return self._sound.reading(self._id)["samples"]

    def level(self):
        """How loud this synth is, [left, right], each from 0 to 1: a meter shows it. A frame late, as samples() is."""
        return self._sound.reading(self._id)["level"]

    def notes(self):
        """The notes this synth is sounding, as numbers: a keyboard lights them. A frame late, as samples() is."""
        return self._sound.reading(self._id)["notes"]

    def describe(self, name):
        """What a setting can be: {"min", "max", "default", "kind", "choices", "unit"}. A dial asks this."""
        if _key(name) == "voice":
            return {"name": "voice", "kind": "choice", "min": 0, "max": len(_VOICES["rows"]), "default": "none",
                    "choices": ["none"] + list(_VOICES["rows"])}
        entry = _setting(self._name(name))
        if entry is None:
            return None
        d = {"name": _snake(name), "kind": entry["kind"], "min": entry["min"] / entry["scale"],
             "max": entry["max"] / entry["scale"], "default": entry["default"] / entry["scale"]}
        if entry.get("choices"):
            d["choices"] = list(entry["choices"])
            # "sample" is a wave only for a synth that has been given a sample to play.
            holds = _setting(entry["name"].replace("wave", "sample")) if entry["name"] in ("osc1.wave", "osc2.wave") else None
            if holds is not None and holds["id"] not in getattr(self, "_patch", {}):
                d["choices"] = [c for c in d["choices"] if c != "sample"]
                d["max"] = len(d["choices"]) - 1
        unit = "octaves" if entry["scale"] == 12 else entry.get("unit")
        if _UNITS.get(unit):
            d["unit"] = _UNITS[unit]
        # A time from nothing to twenty seconds is turned evenly by how much longer it gets, from a thousandth of a second.
        if unit == "seconds" and entry["min"] == 0 and entry["max"] >= 1:
            d["min"], d["log"] = 0.001, True
        # Values that mean something else (a reverb_decay of 0 is "auto"), as synths.js describes them. Where nothing
        # is one of them, the dial still starts from nothing: it is turned by ratio from a thousandth just above it.
        if entry.get("labels"):
            d["labels"] = {}
            for at, word in entry["labels"].items():
                at = float(at) / entry["scale"]
                d["labels"][int(at) if at == int(at) else at] = word
            if d.get("log") and 0 in d["labels"]:
                d["min"], d["log_from"] = 0, 0.001
        return d

    def _told(self, name, value):
        """A control in the page changed a setting by hand: remember it, so lead.cutoff reads what the dial says."""
        try:
            if _key(name) == "voice":
                self._wear(value, send=False)
            else:
                _patch_of({self._name(name): value}, "set", False, self._patch)
                self._sound.share(self._patch, [self._name(name)])
        except (ValueError, TypeError):
            pass

    # --- MIDI: a keyboard plays this synth, its notes go out as MIDI, and a knob turns a setting
    def play_from_midi(self, on=True, *, channel=None, vibrato=None):
        """A MIDI keyboard plays this synth: lead.play_from_midi(). It follows the notes, how hard each key is hit,
        the pitch wheel, the modulation wheel and the sustain pedal, where the devices are, so it is as quick with
        Python busy or on another computer. channel=2 listens to one channel alone; lead.play_from_midi(False) stops."""
        self._sound.midi.play(self, on, channel, vibrato)
        return self

    def send_to_midi(self, on=True, *, channel=None, output=None):
        """What this synth plays, tunes and all, also goes out as MIDI: bass.send_to_midi(channel=2).
        bass.send_to_midi(False) stops."""
        self._sound.midi.through(self, on, channel, output)
        return self

    def map_midi(self, control=None, setting=None, on_change=None, *, min=None, max=None, channel=None):
        """Knob or slider number `control` turns a setting, through the setting's whole range: lead.map_midi(74, "cutoff").
        The page changes the synth itself; lead.cutoff reads what the knob set, a frame later. A function given
        third is called with each new value; min= and max= narrow the range."""
        if not isinstance(control, int) or isinstance(control, bool) or not 0 <= control <= 119:
            raise ValueError('map_midi needs the number of a knob or slider, from 0 to 119, and then a setting, as in '
                             'lead.map_midi(74, "cutoff"), not %s' % _shown(control))
        self._sound.midi.turn(self, "map", setting, on_change, min, max, channel, control)
        return self

    def learn(self, setting=None, on_change=None, *, min=None, max=None, channel=None):
        """The next knob or slider that is moved turns this setting from then on: lead.learn("cutoff")."""
        self._sound.midi.turn(self, "learn", setting, on_change, min, max, channel)
        return self

    def midi_input(self):
        """The device and the channel this synth plays from, for a select on the screen: see midi_input()."""
        return _midi_port("input", self)

    def midi_output(self):
        """Where this synth's notes go when it sends them on, for a select on the screen: see midi_output()."""
        return _midi_port("output", self)

    def unmap_midi(self, setting=None):
        """No knob turns this setting any more: lead.unmap_midi("cutoff"). With no name: none of this synth's."""
        self._sound.midi.unmap(self, setting)
        return self

    @property
    def page(self):
        """The page's own object for this synth, in a Pyctures scene: its dials and keys act on it there, at once."""
        if self._page is None:
            object.__setattr__(self, "_page", self._sound.transport.page(self._id))
        return self._page

    def remove(self):
        """Finished with it. It can still be played afterwards: it takes a place again."""
        self._sound.command({"op": "free", "id": self._id, "t": self._sound.clock()})
        return self


_nothing = object()


def _make_synth(s, preset, settings):
    names = [_snake(n) for n in _NAMES["synths"] if n != "sample"]
    if preset is not None:
        found = _PRESETS.get(_key(preset)) if isinstance(preset, str) else None
        if found is None or found == "sample":
            raise ValueError("make_synth(%s): there is no synth called %s.%s The synths are: %s"
                             % (_shown(preset), _shown(preset), _meant(preset, names), ", ".join(names)))
        preset = found
    said = "make_synth(%s)" % (_shown(_snake(preset)) if preset else "")
    macro = settings.pop("macro", _nothing)
    if macro is not _nothing:
        _check_macro(macro, said)
    patch = _patch_of(_NAMES["plain"], said, False)
    made = _NAMES["synths"][preset] if preset else {}
    _patch_of(made, said, False, patch)
    # With a sound file for its sample, `note` and `loop` are the recording's: the note it is at, and whether it goes round.
    file = isinstance(settings.get("sample"), str)
    note, loop = (settings.pop("note", None), settings.pop("loop", None)) if file else (None, None)
    settings = _with_samples(s, settings, patch, said, note, loop)
    _patch_of(settings, said, True, patch)
    s.share(patch, settings)
    id = s.id("s")
    c = {"op": "synth", "id": id, "t": s.clock()}
    if preset:
        c["preset"] = preset
    if settings:
        c["set"] = _sendable(settings)
    if macro is not _nothing:
        c["macro"] = macro or None
    s.command(c)
    synth = Synth(s, id, patch, made.get("note", 60 if note is None else note_number(note)), 0.3)
    object.__setattr__(synth, "_macro", made.get("macro") if macro is _nothing else macro or None)
    return synth


# ---------------------------------------------------------------- what a program calls

def make_synth(preset=None, settings=None, **more):
    """A synth of your own: make_synth("bass"), make_synth("lead", cutoff=900), make_synth(wave="saw", attack=0.2).
    The ready-made ones: synth_names(). The settings: setting_names()."""
    if isinstance(preset, dict):
        preset, settings = None, preset
    given = dict(settings or {})
    given.update(more)
    if isinstance(given.get("preset"), str):
        preset = given["preset"]
    given.pop("preset", None)
    if preset is not None and not isinstance(preset, str):
        raise ValueError('make_synth needs the name of a synth or its settings, as in make_synth("bass") or '
                         'make_synth(wave="saw"), not %s' % _shown(preset))
    return _make_synth(_sound(), preset, given)


def _file(path):
    """A file's bytes as base64, when Python can read it; else None, and the page is asked to fetch it."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return None


def load_sample(path=None, note=None, loop=None, **settings):
    """A recorded sound from a file beside your program: drum = load_sample("kick.wav"), then drum.play().
    It is a synth: drum.play("E4") plays it higher, drum.reverb = 0.3. loop=True goes round while a note lasts,
    and note="A3" says what note the recording is at (C4 unless you say)."""
    if not isinstance(path, str) or not path.strip():
        raise ValueError('load_sample(%s) needs the name of a sound file, as in load_sample("kick.wav")'
                         % ("" if path is None else _shown(path)))
    s = _sound()
    said = "load_sample(%s)" % _shown(path)
    patch = _patch_of(_NAMES["plain"], said, False)
    _patch_of(_NAMES["synths"].get("sample"), said, False, patch)
    _patch_of(settings, said, True, patch)
    s.share(patch, settings)
    patch[_setting("sample")["id"]] = 0
    sid = _sample_file(s, path, note, loop)
    id = s.id("s")
    s.command({"op": "synth", "id": id, "preset": "sample", "set": dict(_sendable(settings), sample=sid), "t": s.clock()})
    synth = Synth(s, id, patch, 60 if note is None else note_number(note), None)
    object.__setattr__(synth, "_sample", sid)
    return synth


def play_note(note=None, length=0.5, volume=None, *, pan=None, after=None, at=None, beat=None):
    """A note on a pleasant synth: play_note("C4"), play_note("C4", 2, 0.3). A list of notes is a chord."""
    if note is None:
        raise ValueError('play_note needs a note, as in play_note("C4")')
    _sound().main_synth().play(note, length, volume, pan=pan, after=after, at=at, beat=beat)


def play_notes(notes=None, step=None, *, repeat=None, volume=None, hold=None, after=None, at=None, beat=None):
    """A tune: play_notes("C4 E4 G4 - C5:2", 0.25). "-" is a rest, ":2" lasts two steps, "C4+E4" is a chord.
    The second thing is the seconds in a step. repeat=True plays it round and round; .stop() ends it."""
    return _sound().main_synth().play_notes(notes, step, repeat=repeat, volume=volume, hold=hold, after=after, at=at, beat=beat)


def note(what=None, length=None, *, volume=None, pan=None):
    """A tune as ordinary lines, each note beginning where the last ended (on the synth play_note uses):
    note("C4", "quarter"), note("E4", "eighth"). A length is a note length by name, or a number of beats."""
    _sound().main_synth().note(what, length, volume=volume, pan=pan)


def chord(name=None, kind=None, length=None, *, volume=None, pan=None):
    """The next thing in the tune is a chord: chord("Cm", "half")."""
    _sound().main_synth().chord(name, kind, length, volume=volume, pan=pan)


def rest(length=None):
    """A silence in the tune: rest("eighth")."""
    _sound().main_synth().rest(length)


def start_lines(*, after=None, at=None, beat=None):
    """Begin every line of notes again together, from now (or after=, at=, beat=)."""
    s = _sound()
    s.lines.clear()
    s.turn_of, s.turn = s.transport.turn(s.clock), s.when("start_lines", after, at, beat)


class Loop:
    """A section of notes that goes round: what loop_notes() gives back. stop() ends it."""

    def __init__(self, sound, times):
        self._sound = sound
        self._times = times
        self._made = []

    def __enter__(self):
        s = self._sound
        if s.writing is not None:
            raise ValueError("loop_notes cannot be used inside another loop_notes")
        s.writing = {}
        return self

    def __exit__(self, kind, error, trace):
        s = self._sound
        written, s.writing = s.writing, None
        if kind is not None:
            return False
        whole = max([line[1] for line in written.values()] or [0])
        if not whole > 0:
            raise ValueError("loop_notes: nothing was written to go round. Use note(), chord() and rest() inside it")
        # Every line of the section starts together, where the latest of those lines has reached.
        start = max(s.line_at(synth) for synth in written)
        for synth, (steps, _) in written.items():
            id = s.id("t")
            self._made.append(id)
            if steps:
                s.command({"op": "tune", "id": id, "synth": synth, "steps": [[_whole(a), n, _whole(l), v] for a, n, l, v in steps],
                           "length": _whole(whole), "repeat": self._times, "beats": True, "t": start})
            s.lines[synth] = start if self._times is True else start + self._times * whole * 60 / s.tempo
        return False

    def stop(self):
        s = self._sound
        for id in self._made:
            s.command({"op": "stop", "id": id, "t": s.clock()})
        return self


def loop_notes(a=None, b=None, *, times=None):
    """Write a section once and have it go round, on any synths, kept in time by the sound engine and following the tempo:

        with loop_notes():
            kick.note("C3", "quarter")
            snare.note("A3", "quarter")

    loop_notes(4) goes round four times, and the lines carry on after it. A function works too: loop_notes(section),
    loop_notes(4, section). What it gives back has stop()."""
    section = a if callable(a) else b if callable(b) else None
    count = times if times is not None else b if callable(a) else a
    if count is not None and count is not True and not callable(count):
        count = _amount(count, "loop_notes: how many times", 1, 1e9)
    loop = Loop(_sound(), True if count is None or count is True or callable(count) else count)
    if section is not None:
        with loop:
            section()
    return loop


def main_synth():
    """The synth that play_note and play_notes use: change it (main_synth().cutoff = 900), or tie a keyboard to it."""
    return _sound().main_synth()


def _chip():
    # Arpeggios with no synth named are played on a plain square wave, as a sound chip would.
    s = _sound()
    if s.chip is None:
        s.chip = _make_synth(s, "chip", {})
    return s.chip


def play_arp(chord=None, *more, **how):
    """A chord as a fast arpeggio on a chip sound: play_arp("Cm7"), play_arp("C4", "minor", 1, speed=30, order="down")."""
    return _chip()._arp(chord, more, how, "play_arp", 0.5)


def start_arp(chord=None, *more, **how):
    """The same, staying until it is stopped, and able to change chord: arp = start_arp("Am"), arp.change("F")."""
    return _chip()._arp(chord, more, how, "start_arp", None)


class _Output:
    """Everything that is sounding, as a thing a scope, a meter and dials can be tied to: what sound_output() gives."""

    def __init__(self, sound):
        self._sound = sound
        self._values = {"volume": 1}
        self._page = None

    def describe(self, name):
        if _key(name) == "volume":
            return {"name": "volume", "kind": "float", "min": 0, "max": 2, "default": 1}
        entry = _setting(name)
        return Synth.describe(self, name) if entry is not None and entry["scope"] == "all" else None

    def get(self, name):
        if _key(name) == "volume":
            return self._values["volume"]
        entry = _setting(name)
        if entry is None or entry["scope"] != "all":
            return None
        value = self._sound.for_all.get(entry["id"], entry["default"])
        if entry["kind"] == "choice":
            return entry["choices"][int(value)]
        if entry["kind"] == "bool":
            return value == 1
        return value / entry["scale"]

    def set(self, name, value):
        if _key(name) == "volume":
            set_volume(value)
            self._values["volume"] = value
        else:
            set_effects({name: value})

    def _told(self, name, value):
        """A control in the page changed it by hand: remember it."""
        if _key(name) == "volume":
            self._values["volume"] = value
        else:
            try:
                self._sound.share(_patch_of({name: value}, "set", False))
            except (ValueError, TypeError):
                pass

    def samples(self):
        """The wave of everything that is sounding, numbers from -1 to 1. A frame late in a Pyctures scene."""
        return self._sound.reading(None)["samples"]

    def level(self):
        """How loud everything is, [left, right], each from 0 to 1."""
        return self._sound.reading(None)["level"]

    def notes(self):
        """The notes that are sounding, as numbers."""
        return self._sound.reading(None)["notes"]

    @property
    def page(self):
        """The page's own object for all the sound, in a Pyctures scene."""
        if self._page is None:
            self._page = self._sound.transport.page(None)
        return self._page


def sound_output():
    """All the sound together: scope(sound_output()) draws it, meter(sound_output()) shows how loud it is, and
    dial("volume", sound_output(), "volume") turns it up and down."""
    s = _sound()
    if s.output is None:
        s.output = _Output(s)
    return s.output


def play_sound(name=None, volume=None, *, pitch=None, pan=None, length=None, after=None, at=None, beat=None):
    """A ready-made game sound: play_sound("coin"). The sounds: sound_names(). length= cuts it short there, or holds
    its last note until then."""
    found = _SOUNDS.get(_key(name)) if isinstance(name, str) else None
    if found is None:
        raise ValueError("play_sound(%s): there is no sound called %s.%s The sounds are: %s"
                         % ("" if name is None else _shown(name), _shown(name), _meant(name, list(_NAMES["sounds"])),
                            ", ".join(_NAMES["sounds"])))
    s = _sound()
    c = {"op": "sound", "name": found, "t": s.when("play_sound", after, at, beat)}
    if volume is not None:
        c["vol"] = _amount(volume, "play_sound: volume", 0, 4)
    if pitch is not None:
        c["pitch"] = _amount(pitch, "play_sound: pitch", -48, 48)
    if pan is not None:
        c["pan"] = _amount(pan, "play_sound: pan", -1, 1)
    if length is not None:
        c["len"] = s.length(length, "play_sound: length")
    s.command(c)


def play_song(file=None, *, repeat=True, loop=None, volume=None, raw=None, patches=None, after=None, at=None, beat=None):
    """Play a song: a tracker's .mod or .xm file, or a song in synths' own format (.json). song = play_song("tune.mod").
    It goes round until it is stopped: song.pause(), song.resume(), song.volume = 0.5, song.seek(2), song.stop().
    repeat=False plays it once. One song plays at a time, and your own notes and game sounds play over it.
    A song whose instruments are synths by name is told what they are with patches={"wobble": "bass",
    "pling": {"preset": "pluck", "echo": 0.4}}; a name that is a ready-made synth's needs no telling."""
    given = isinstance(file, (bytes, bytearray))
    if not given and (not isinstance(file, str) or not file.strip()):
        raise ValueError('play_song(%s) needs the name of a song file, as in play_song("tune.mod")'
                         % ("" if file is None else _shown(file)))
    s = _sound()
    id = s.id("g")
    c = {"op": "song", "id": id, "do": "play", "repeat": (repeat if loop is None else loop) is not False,
         "t": s.when("play_song", after, at, beat)}
    if volume is not None:
        c["vol"] = _amount(volume, "play_song: volume", 0, 2)
    if raw is not None:
        c["raw"] = bool(raw)
    if patches is not None:
        c["patches"] = _song_patches(patches)
    if given:
        c["bytes"] = base64.b64encode(bytes(file)).decode("ascii")
    else:
        c["name"] = file
        data = _file(file)
        if data is None:
            c["url"] = file         # the page fetches it from beside the scene, and the files it names
        else:
            c["bytes"] = data       # Python has the file, and the WAV files one of synths' own songs names
            files = {}
            for name in _song_files(data):
                more = _file(os.path.join(os.path.dirname(file), name))
                if more is not None:
                    files[name] = more
            if files:
                c["files"] = files
    s.command(c)
    return Song(s, id)


def _song_files(data):
    """The WAV files a song in synths' own format names for its samples (it is JSON; a .mod or .xm names none)."""
    try:
        song = json.loads(base64.b64decode(data).decode("utf-8"))
        return sorted({sample["file"] for sample in song.get("samples") or [] if isinstance(sample, dict) and isinstance(sample.get("file"), str)})
    except (ValueError, AttributeError, TypeError):
        return []


def _song_patches(patches):
    """What a song's instruments that are synths by name are, checked: {"wobble": "bass", "pling": {"preset": "pluck", "echo": 0.4}}."""
    if not isinstance(patches, dict):
        raise ValueError('play_song: patches needs names and what each is, as in patches={"wobble": "bass"}, not %s' % _shown(patches))
    names = [_snake(n) for n in _NAMES["synths"] if n != "sample"]
    out = {}
    for name, what in patches.items():
        said = "play_song: the patch %s" % _shown(name)
        if not isinstance(what, (str, dict)):
            raise ValueError("%s needs the name of a synth or settings, not %s" % (said, _shown(what)))
        preset = what if isinstance(what, str) else what.get("preset")
        found = None
        if preset is not None:
            found = _PRESETS.get(_key(preset)) if isinstance(preset, str) else None
            if found is None or found == "sample":
                raise ValueError("%s names a synth called %s, and there is none.%s The synths are: %s"
                                 % (said, _shown(preset), _meant(preset, names), ", ".join(names)))
        if isinstance(what, str):
            out[name] = found
        else:
            _patch_of(what, said, True)
            _check_macro(what.get("macro"), said)
            out[name] = dict(_sendable({k: v for k, v in what.items() if k != "preset"}), **({"preset": found} if found else {}))
    return out


def stop_song():
    """Stop every song."""
    s = _sound()
    s.command({"op": "song", "do": "stop", "t": s.clock()})


def stop_sound():
    """Stop everything that is sounding or waiting to sound. Synths and their settings stay."""
    s = _sound()
    s.command({"op": "stop", "t": s.clock()})


def set_volume(volume):
    """How loud everything is: 1 is normal, 0 is silent, 2 is twice as loud."""
    s = _sound()
    s.command({"op": "master", "volume": _amount(volume, "set_volume", 0, 4), "t": s.clock()})


def mute_sound(on=True):
    """Silence, until unmute_sound()."""
    s = _sound()
    s.command({"op": "master", "mute": bool(on), "t": s.clock()})


def unmute_sound():
    mute_sound(False)


def set_effects(settings=None, **more):
    """The effects every synth shares: set_effects(echo_time=0.3, echo_feedback=0.5, reverb_size=0.8)."""
    if settings is not None and not isinstance(settings, dict):
        raise ValueError("set_effects needs settings, as in set_effects(echo_time=0.3), not %s" % _shown(settings))
    given = dict(settings or {})
    given.update(more)
    shared = [n for n in _FRIENDLY if _setting(n)["scope"] == "all"]
    if not given:
        raise ValueError("set_effects needs settings, as in set_effects(echo_time=0.3). They are: %s" % ", ".join(shared))
    patch = _patch_of(given, "set_effects", True)
    scope = {e["id"]: e["scope"] for e in _SETTINGS.values()}
    if any(scope[i] != "all" for i in patch):
        raise ValueError("set_effects is for the effects every synth shares: %s. A synth's own settings are set on "
                         "the synth, as in lead.echo = 0.4" % ", ".join(shared))
    s = _sound()
    s.share(patch)
    s.command({"op": "master", "set": given, "t": s.clock()})


def set_tempo(bpm):
    """How fast the beat is, in beats a minute. Beat 0 is now."""
    s = _sound()
    s.tempo = _amount(bpm, "set_tempo", 20, 400)
    s.beat_zero = s.clock()
    s.command({"op": "tempo", "bpm": s.tempo, "t": s.beat_zero})     # tunes written in beats change speed from here on
    if s._midi is not None and s._midi.clock_on:
        s._midi.command({"do": "clock", "bpm": s.tempo, "t": s.clock()})     # a MIDI clock being sent keeps up


def beats(n=1):
    """How many seconds that many beats last: beats(2), or a note length by name, beats("half")."""
    return (_beats_long(n, "beats") if isinstance(n, str) else n) * 60 / _sound().tempo


def beat():
    """Which beat it is now (a fraction between beats)."""
    s = _sound()
    return (s.clock() - s.beat_zero) * s.tempo / 60


def _buffer_size(asked):
    """A sound buffer as it may be asked for, as synths.js reads it: "auto", a word (small, medium, large) or a
    number of frames, brought to the nearest power of two from 256 to 16384. (size, exact), or None."""
    b = _NAMES["buffer"]
    if asked is None:
        return "auto", True
    if isinstance(asked, str):
        word = asked.lower().strip()
        if word in b["words"]:
            return b["words"][word], True
        try:
            asked = float(word)
        except ValueError:
            return None
    if not _is_number(asked) or not asked > 0 or asked == float("inf"):
        return None
    low, high = int(math.log2(b["least"])), int(math.log2(b["most"]))
    size = 2 ** min(high, max(low, int(math.floor(math.log2(asked) + 0.5))))
    return size, size == asked


def set_sound_buffer(size="auto"):
    """How much sound is made at a time: set_sound_buffer("large") or set_sound_buffer(4096) for fewer clicks on a
    slow device, "small" (1024) for a keyboard that feels late, "medium" (2048), and "auto" to let the page choose
    and change it again. A number is frames: a power of two from 256 to 16384. It matters on a page with no https
    address, where sound is made on the page's thread; on the audio thread it sets how far ahead everything is
    scheduled instead. It gives what sound_buffer() does."""
    got = _buffer_size(size)
    if got is None:
        raise ValueError('set_sound_buffer needs "small", "medium", "large", "auto" or a number of frames from 256 to '
                         '16384, as in set_sound_buffer("large"), not %s' % _shown(size))
    if not got[1]:
        _tell("a sound buffer is a power of two from 256 to 16384, so %s is taken as %d." % (_shown(size), got[0]))
    s = _sound()
    s.buffer_set = got[0]
    s.hear_back()
    s.buffer_asked = True
    s.command({"op": "buffer", "size": got[0], "t": s.clock()})
    return sound_buffer()


def sound_buffer():
    """The buffer as the page last said it: {"frames", "delay", "thread", "underruns", "setting"}. `delay` is the
    milliseconds from a key to its note, `thread` is "audio" (the audio thread: nothing to worry about), "page" (the
    page's thread, which a busy page makes click) or None before the page has said, `underruns` how many times the
    sound came too late, and `setting` what was asked for ("auto" or frames). It is a frame late."""
    s = _sound()
    if not s.buffer_asked:
        s.hear_back()
        s.buffer_asked = True
        s.command({"op": "buffer", "t": s.clock()})
    if s.buffer_said:
        return dict(s.buffer_said)
    return {"frames": 0, "delay": 0, "thread": None, "underruns": 0, "setting": "auto" if s.buffer_set is None else s.buffer_set}


def sound_time():
    """The sound clock now, in seconds: the time that at= is read against."""
    return _sound().clock()


def sound_names():
    """The names of the ready-made game sounds."""
    return list(_NAMES["sounds"])


def synth_names():
    """The names of the ready-made synths."""
    return [_snake(n) for n in _NAMES["synths"] if n != "sample"]


def setting_names():
    """The name of every setting a synth has."""
    return list(_SHOWN)


# ---------------------------------------------------------------- MIDI
#
# MIDI is how music keyboards, drum pads, boxes of knobs and synths talk to each other and to a computer.
# The devices are where the page is, so that is where MIDI is done (synths.js's docs/midi.md is the contract):
#
#   - Every function here writes a command, {"op": "midi", "do": "send", "bytes": [144, 60, 102], "t": 12.25},
#     into the same batches as the sound's.
#   - A keyboard plays a synth ON THE PAGE (lead.play_from_midi()), and a knob turns a setting there
#     (lead.learn("cutoff")), without Python in between: so it feels immediate however slow or far away Python is.
#   - What was received is handed to Python as plain data with the next frame, each message with the time it
#     happened (on the clock that sound_time() reads), and the program's functions are called then.

# ---------------------------------------------------------------- the microphone, recording and saving
#
# The microphone is where the player is, so the page opens it, when the first `mic` command arrives and not
# before; that is when the browser asks the person. From then on it is a synth by its id whose sound comes in
# instead of being made, so `set` and a voice work on it. It is all commands (mic, record, save: synths.js's
# docs/commands.md), and what the player says back (the microphone is on or is not, a recording is over, a file
# is saved) arrives as plain data: with the next frame in a Pyctures scene, or from a host through
# receive_sound_events(events). So `mic.state`, `take.done` and `take.seconds` are A FRAME LATE at the soonest,
# and nothing here ever waits for them.

class _Until:
    """Something to `await` in a scene that can wait: it looks again every frame, and never holds the program."""

    def __init__(self, over, value):
        self.over, self.value = over, value

    def __await__(self):
        while not self.over():
            p = sys.modules.get("pyctures")
            frame = getattr(p, "frame", None) if getattr(getattr(p, "S", None), "ns", None) is not None else None
            if frame is not None:
                yield from frame().__await__()
            else:
                yield
        return self.value()


def _dress_like(synth, other):
    """One synth is given the voice and the voice effects of another, as ordinary commands: what the other had
    before any voice, its voice, and what was turned after that (synths.js's dressLike). So a recording of the
    plain microphone plays back as the microphone sounds, and "none" still puts back the plain voice."""
    part = [pid for pid in _VOICES["all"] if pid < 200]
    now = lambda pid: synth._patch.get(pid, _DEFAULTS.get(pid))
    if synth.voice != "none":
        synth.voice = "none"
    if synth._plain is None:
        object.__setattr__(synth, "_plain", {pid: now(pid) for pid in part})

    def send(pairs):
        changed = {_BY_ID[pid]: value for pid, value in pairs if value != now(pid)}
        if changed:
            Synth.set(synth, changed)
    under = other._worn["under"] if other._worn else None
    if under is not None:
        send([(pid, under[pid] if pid in under else synth._plain[pid]) for pid in part])
        synth.voice = other._worn["voice"]
        send([(pid, other._patch[pid]) for pid in part if pid in other._patch])
    else:
        send([(pid, other._patch[pid] if pid in other._patch else synth._plain[pid]) for pid in part])


class Mic(Synth):
    """The microphone: what use_microphone() gives. It is a synth whose sound comes in instead of being made, so it
    has a synth's settings (mic.echo = 0.4, mic.cutoff = 900), the voice changers (mic.voice = "robot") and what a
    dial, a scope and a meter look for. Its own words: `pitch` is the pitch shifter (-12 to 12 semitones), `ring`
    the ring modulator, `gain` how much the microphone is turned up, and `gate` the level in dB below which it is
    taken as silence ("off" for none). Nothing is heard until listen().

    mic.state is "asking" until the page has said, then "on", or why not: "refused", "none", "busy" or
    "unavailable"; "off" once closed. It is told with a frame, so it is a frame late at the soonest."""

    _OWN = Synth._OWN + ("listening", "state", "message")

    def __init__(self, sound, id):
        Synth.__init__(self, sound, id, {}, 60, 0.3)
        put = object.__setattr__
        put(self, "_listening", False)
        put(self, "_waiting", [])
        put(self, "state", "asking")
        put(self, "message", "")

    def __repr__(self):
        return "<the microphone: %s>" % self.state

    def _name(self, name):
        return _MIC_NAMES.get(_key(name), name) if isinstance(name, str) else name

    def _given(self, given, at):
        out = {}
        for name, value in given.items():
            k = _key(name)
            if k == "listening":
                self.listening = value
            elif k == "gate" and (value is False or value is None or value == "off"):
                out["micGate"] = -100
            else:
                out[name] = value
        # The microphone starts with no filter, so that it comes through untouched. Turning the cutoff asks for one.
        names = [(_setting(self._name(n)) or {}).get("name") for n in out]
        if ("filter.cutoff" in names or "filter.resonance" in names) and "filter.type" not in names and self.filter == "off":
            out["filter"] = "lowpass"
        return Synth._given(self, out, at)

    def describe(self, name):
        if _key(name) == "listening":
            return {"name": "listening", "kind": "bool", "min": 0, "max": 1, "default": False}
        return Synth.describe(self, name)

    def _told(self, name, value):
        if _key(name) == "listening":
            object.__setattr__(self, "_listening", bool(value))
        else:
            Synth._told(self, name, value)

    def listen(self, on=True):
        """Hear the microphone, through its voice and effects. With loudspeakers this can howl: headphones are best."""
        object.__setattr__(self, "_listening", bool(on))
        self._sound.command({"op": "mic", "id": self._id, "listen": self._listening, "t": self._sound.clock()})
        return self

    def mute(self):
        """Stop hearing it. It can still be recorded, and a scope and a meter still show it."""
        return self.listen(False)

    @property
    def listening(self):
        return self._listening

    @listening.setter
    def listening(self, on):
        self.listen(on is True or on == 1 or on == "on")

    @property
    def ready(self):
        """Whether there is a microphone: None while the person is still being asked, then True or False."""
        return None if self.state == "asking" else self.state == "on"

    def on_ready(self, fn):
        """Call a function when it is known whether there is a microphone: mic.on_ready(lambda there: ...)."""
        if not callable(fn):
            raise ValueError("on_ready needs a function to call, as in mic.on_ready(started), not %s" % _shown(fn))
        if self.state == "asking":
            self._waiting.append(fn)
        else:
            _call(fn, self.state == "on")
        return self

    def when_ready(self):
        """For a scene that can wait: `there = await mic.when_ready()` is True once the microphone is on, False
        if there is none. It looks again each frame and holds nothing up."""
        return _Until(lambda: self.state != "asking", lambda: self.state == "on")

    def _said(self, e):
        if self.state == "off":
            return
        put = object.__setattr__
        put(self, "state", e.get("state") or "unavailable")
        put(self, "message", e.get("message") or "")
        if self.state != "asking":
            waiting, self._waiting[:] = list(self._waiting), []
            for fn in waiting:
                _call(fn, self.state == "on")

    def close(self):
        """Let the microphone go: the browser's recording light goes out. use_microphone() opens it again."""
        if self.state == "off":
            return self
        put = object.__setattr__
        put(self, "state", "off")
        put(self, "_listening", False)
        waiting, self._waiting[:] = list(self._waiting), []
        for fn in waiting:
            _call(fn, False)
        s = self._sound
        s.command({"op": "mic", "id": self._id, "do": "close", "t": s.clock()})
        if s.mic is self:
            s.mic = None
        return self

    def remove(self):
        return self.close()


def use_microphone(voice=None, *, listen=None, raw=None, **settings):
    """The microphone: mic = use_microphone(). The first call has the page ask for it, and the browser asks the
    person; until then, and if the answer is no, everything still works and there is simply no sound from it.
    use_microphone("robot", listen=True) sets it up in one line; raw=False asks for the browser's own tidying
    (echo cancelling, noise removal, automatic level), which suits loudspeakers and spoils a voice changer.

    It is a synth: mic.voice = "robot", mic.pitch = 7, mic.echo = 0.4, mic.gain = 2, mic.gate = -40. Nothing is
    heard until mic.listen(); wear headphones when you do. Recording does not need it."""
    if isinstance(voice, dict):
        settings = dict(voice, **settings)
        voice = settings.pop("voice", None)
        listen = settings.pop("listen", listen)
        raw = settings.pop("raw", raw)
    elif voice is not None and not isinstance(voice, str):
        raise ValueError('use_microphone takes a voice and settings, as in use_microphone("robot", echo=0.4), not %s' % _shown(voice))
    s = _sound()
    if s.mic is None:
        mic = Mic(s, s.id("m"))
        gate = _NAMES.get("microphone", {}).get("gate", -50)
        _patch_of({"micGate": gate}, "use_microphone", False, mic._patch)
        s.share(mic._patch, ["micGate"])
        c = {"op": "mic", "id": mic._id, "set": {"micGate": gate}, "t": s.clock()}
        if raw is False:
            c["raw"] = False
        s.hear_back()
        s.command(c)
        s.mic = mic
        if isinstance(s.transport, _Nowhere):
            mic._said({"state": "unavailable"})
    mic = s.mic
    if voice is not None:
        settings["voice"] = voice
    if settings:
        mic.set(settings)
    if listen is not None:
        mic.listen(bool(listen))
    return mic


def stop_microphone():
    """Let the microphone go, if it was asked for."""
    s = _sound()
    if s.mic is not None:
        s.mic.close()


class Take(Synth):
    """A recording, while it is being made and afterwards: what record_sound() gives back at once. It is a sample
    like one from load_sample, so take.play(), take.play("E4"), take.reverse = True and take.loop = True all work,
    and they work while it is still recording (it plays what there is so far).

    take.done turns True and take.seconds says how long it is when it is over. In a Pyctures scene the page says
    so with a frame, so both change the frame AFTER the recording ended. take.on_done(fn) calls a function then,
    and `await take.when_done()` waits in a scene that can wait."""

    _OWN = Synth._OWN + ("done", "recording", "seconds", "frames")

    def __init__(self, sound, id, patch, sample):
        Synth.__init__(self, sound, id, patch, 60, None)
        put = object.__setattr__
        put(self, "_sample", sample)
        put(self, "_after", [])
        put(self, "done", False)
        put(self, "recording", True)
        put(self, "seconds", 0)
        put(self, "frames", 0)

    def __repr__(self):
        return "<a recording, %s>" % ("%.2f seconds" % self.seconds if self.done else "still being made")

    def on_done(self, fn):
        """Call a function when the recording is over: take.on_done(lambda: take.play()). It is given the take, if
        it takes anything. One that is already over is called at once."""
        if not callable(fn):
            raise ValueError("on_done needs a function to call when the recording is over, as in "
                             "take.on_done(lambda: take.play()), not %s" % _shown(fn))
        if self.done:
            _call(fn, self)
        else:
            self._after.append(fn)
        return self

    def when_done(self):
        """For a scene that can wait: `await take.when_done()` carries on when the recording is over. It looks
        again each frame and holds nothing up."""
        return _Until(lambda: self.done, lambda: self)

    def stop_recording(self):
        """End this recording now."""
        if not self.done:
            self._sound.command({"op": "record", "do": "stop", "id": self._sample, "t": self._sound.clock()})
        return self

    def _finish(self, e):
        if self.done:
            return
        put = object.__setattr__
        put(self, "done", True)
        put(self, "recording", False)
        put(self, "seconds", e.get("seconds") or 0)
        put(self, "frames", e.get("frames") or 0)
        after, self._after[:] = list(self._after), []
        for fn in after:
            _call(fn, self)


def _record_from(s, o, said):
    """What record_sound, record_output, start_recording and a synth's record() all do."""
    names = _NAMES.get("microphone", {})
    longest = names.get("longestRecording", 120)
    source = o.pop("from", None) if o.get("source") is None else o.get("source")
    wid = s.id("w")
    c = {"op": "record", "id": wid}
    mic = None
    if source is None or source in ("mic", "microphone") or isinstance(source, Mic):
        c["from"] = "mic"
        mic = use_microphone()
    elif source == "output" or isinstance(source, _Output):
        c["from"] = "output"
    elif isinstance(source, Synth):
        c["from"], c["synth"] = "synth", source._id
    else:
        raise ValueError('%s: source needs the microphone, a synth or "output", not %s' % (said, _shown(source)))
    if o.get("length") is not None:
        c["len"] = s.length(o["length"], "%s: the length" % said)
        if c["len"] > longest:
            raise ValueError("%s: a recording can be up to %d seconds long, not %d" % (said, longest, round(c["len"])))
    elif o.get("max") is not None:
        c["max"] = _amount(o["max"], "%s: max" % said, 0.1, longest)
    if o.get("effects"):
        c["effects"] = True
    loop = o.get("loop")
    if loop:
        c["loop"] = list(loop) if isinstance(loop, (list, tuple)) else True
    c["t"] = s.when(said, o.get("after"), o.get("at"), o.get("beat"))
    sid = s.id("s")
    s.hear_back()
    s.command(c)
    s.command({"op": "synth", "id": sid, "preset": "sample", "set": {"sample": wid}, "t": s.clock()})
    patch = _patch_of(_NAMES["plain"], said, False)
    _patch_of(_NAMES["synths"].get("sample"), said, False, patch)
    patch[_setting("sample")["id"]] = 0
    take = Take(s, sid, patch, wid)
    if loop:
        object.__setattr__(take, "_loop", c["loop"])
    s.takes[wid] = take
    if mic is not None and not c.get("effects"):
        _dress_like(take, mic)
    if isinstance(s.transport, _Nowhere):
        s.takes.pop(wid, None)
        take._finish({})       # no player: it is over at once, and empty
    return take


def record_sound(length=None, *, effects=False, source=None, max=None, loop=None, after=None, at=None, beat=None, **more):
    """Record the microphone into a sample: take = record_sound(3) is three seconds (a note length by name works
    too). It gives the sample back at once and does not wait: your program carries on and the take fills up behind
    it (see Take: take.done, take.seconds, take.on_done(fn), take.play("E4")).

    What is recorded is the plain voice, whether or not the microphone is being listened to, and the take is
    given the microphone's voice and effects, so it plays back as the microphone sounds and can be changed
    afterwards (take.voice = "monster"). effects=True records the voice after its effects instead, which needs
    listen(). source=lead records a synth, source="output" everything. With no microphone the take is empty,
    and done as soon as the page says so."""
    return _record_from(_sound(), dict(more, length=length, effects=effects, source=source, max=max, loop=loop,
                                       after=after, at=at, beat=beat), "record_sound")


def start_recording(*, max=None, effects=False, source=None, loop=None, after=None, at=None, beat=None, **more):
    """A recording with no set length: it runs until stop_recording(), or for 30 seconds, or max=seconds up to 120."""
    return _record_from(_sound(), dict(more, length=None, effects=effects, source=source, max=max, loop=loop,
                                       after=after, at=at, beat=beat), "start_recording")


def stop_recording():
    """End the recording that is being made."""
    s = _sound()
    s.command({"op": "record", "do": "stop", "t": s.clock()})


def record_output(length=None, *, max=None, loop=None, after=None, at=None, beat=None):
    """Record everything that is played, in stereo, for "save my tune": tune = record_output(10), then
    save_sound(tune, "tune.wav")."""
    return _record_from(_sound(), dict(length=length, source="output", max=max, loop=loop, after=after, at=at, beat=beat),
                        "record_output")


class Saved:
    """What save_sound() gives back: saved.done turns True when the file has been made (a frame late in a Pyctures
    scene), saved.name is the file's name, saved.path where Python wrote it (None when the page kept or
    downloaded it), saved.bytes the WAV file itself when Python was given it, and saved.seconds how long it is.
    saved.on_done(fn) calls a function then, and `await saved.when_done()` waits in a scene that can wait."""

    def __init__(self, name, write):
        self.name, self.path, self.bytes, self.seconds, self.done = name, None, None, 0, False
        self._write, self._after = write, []

    def __repr__(self):
        return "<%s, %s>" % (self.name, "saved" if self.done else "being saved")

    def on_done(self, fn):
        if not callable(fn):
            raise ValueError("on_done needs a function to call when the file is saved, not %s" % _shown(fn))
        if self.done:
            _call(fn, self)
        else:
            self._after.append(fn)
        return self

    def when_done(self):
        return _Until(lambda: self.done, lambda: self)

    def _finish(self, e):
        if self.done:
            return
        data = e.get("bytes")
        if isinstance(data, str):
            try:
                data = base64.b64decode(data)
            except ValueError:
                data = None
        elif isinstance(data, (list, tuple)):
            data = bytes(bytearray(data))
        self.bytes = bytes(data) if isinstance(data, (bytes, bytearray)) else None
        self.seconds = e.get("seconds") or 0
        if self._write and self.bytes is not None:
            try:
                folder = os.path.dirname(self.name)
                if folder:
                    os.makedirs(folder, exist_ok=True)
                with open(self.name, "wb") as f:
                    f.write(self.bytes)
                self.path = os.path.abspath(self.name)
            except OSError as err:
                _tell("save_sound(%s): the file could not be written (%s)." % (_shown(self.name), getattr(err, "strerror", None) or err))
        self.done = True
        after, self._after[:] = list(self._after), []
        for fn in after:
            _call(fn, self)


def save_sound(what=None, name=None, *, download=None):
    """A recording or a sample as a WAV file: save_sound(take, "hello.wav"). A recording that is still being made
    is saved when it is over.

    WHERE IT GOES. Run by your own Python (`pyctures run`), the file is written beside your program, a frame or two
    after the recording is over (the page hands Python the file). In a web page it is downloaded, or kept by the
    app that shows the page. download=False saves nothing anywhere and hands Python the bytes: saved.bytes.
    It gives back a Saved at once (saved.done, saved.on_done(fn)) and never waits."""
    if not isinstance(what, Synth) or not what._sample:
        raise ValueError('save_sound needs a recording or a sample to save, as in save_sound(take, "hello.wav")')
    if name is not None and (not isinstance(name, str) or not name.strip()):
        raise ValueError('save_sound needs a name for the file, as in save_sound(take, "hello.wav"), not %s' % _shown(name))
    name = "sound.wav" if name is None else name.strip()
    if not name.lower().endswith(".wav"):
        name += ".wav"
    # A path from the program's folder, and never out of it.
    name = "/".join(p for p in name.replace("\\", "/").split("/") if p not in ("", ".", "..") and not p.endswith(":")) or "sound.wav"
    s = _sound()
    s.asks += 1
    c = {"op": "save", "id": what._sample, "name": name, "ask": s.asks, "t": s.clock()}
    write = download is not False and s.transport.keeps_files()
    if write or download is False:
        c["download"] = False      # Python is given the bytes, and writes the file itself or keeps them
    saved = Saved(name, write)
    s.saves[s.asks] = saved
    s.hear_back()
    s.command(c)
    if isinstance(s.transport, _Nowhere):
        s.saves.pop(s.asks, None)
        saved._finish({})
    return saved


def receive_sound_events(events):
    """Hand the program what a player said back, just as the page would: a dict or a list of them, as synths.js's
    player.onSoundEvents gives them. {"type": "microphone", "state": "on"}, {"type": "recorded", "id", "frames",
    "seconds"}, {"type": "saved", "id", "ask", "name", "seconds", "bytes"} (bytes, or base64 text). Two more are
    understood, for a program that draws its sound: {"type": "reading", "id", "samples", "level", "notes"} (no
    id: all the sound) and {"type": "position", ...a song's place}."""
    _sound().receive(events)


def voice_names():
    """The voice changers a microphone, a recording or a synth can be given: mic.voice = "robot"."""
    return list(_VOICES["rows"])


_MIDI_HOOKS = ("on_midi", "on_midi_note", "on_midi_note_off", "on_midi_control", "on_midi_devices")


class MidiMessage(dict):
    """What arrived, decoded: message.type ("noteOn", "noteOff", "control", "bend", "program", ...), message.note,
    message.velocity, message.control, message.value, message.channel, message.time, message.device and
    message.data (the bytes). Also message["note"]. What a kind of message does not have reads as None."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return self.get(name)


def _call(fn, *args):
    """Call a function of the program's with as many of `args` as it takes: on_midi_note(note, velocity) and
    on_midi_note(note, velocity, channel) are both right."""
    code = getattr(fn, "__code__", None)
    if code is not None and not code.co_flags & 0x04:        # no *args of its own
        takes = code.co_argcount - (1 if getattr(fn, "__self__", None) is not None else 0)
        if takes < len(args):
            args = args[:takes]
    return fn(*args)


class _Midi:
    """One program's MIDI: the functions it gave, the devices it has been told of, and the settings tied to knobs."""

    def __init__(self, sound):
        self.sound = sound
        self.on = {"all": [], "note": [], "note_off": [], "control": [], "devices": []}
        self.devices = {"inputs": [], "outputs": [], "available": None}
        self.listening = False
        self.joined = False
        self.asked = False
        self.clock_on = False
        self.bound = {}          # synth id -> setting -> [the synth, a function to call with each new value]
        self.hooked = set()      # the scene's own functions already taken by use_midi_hooks
        self.ports = {}          # (which, a synth's id or None) -> what midi_input() and midi_output() gave
        self.held = {}           # an input's notes held down now: note -> how hard
        self.last = [0, 0]       # how hard the last note was hit, and when

    # Every MIDI call sends a command (which is what has the page ask for permission) and makes sure this
    # program is handed what the page's desk says.
    def command(self, c):
        s = self.sound
        s.command(dict({"op": "midi"}, **c))
        if not self.joined:
            self.joined = True
            s.transport.listen(self.receive)

    def ask(self):
        if not self.asked:
            self.asked = True
            self.command({"do": "devices"})

    def listen(self):
        if not self.listening:
            self.listening = True
            self.command({"do": "listen"})

    def add(self, which, fn, said, example):
        if not callable(fn):
            raise ValueError("%s needs a function to call, as in %s(%s), not %s" % (said, said, example, _shown(fn)))
        if fn not in self.on[which]:
            self.on[which].append(fn)
        return fn

    def receive(self, events):
        """What the page's desk says happened, as a list of plain dicts: the program's functions are called with it."""
        if isinstance(events, dict):
            events = [events]
        for m in events or ():
            if not isinstance(m, dict):
                continue
            m = MidiMessage(m)
            kind = m.get("type")
            if kind == "devices":
                self.devices = {"inputs": list(m.get("inputs") or ()), "outputs": list(m.get("outputs") or ()),
                                "available": bool(m.get("available"))}
                # With no MIDI (`available` False) the page has said why, once, in its console; nothing more is said here.
                for fn in list(self.on["devices"]):
                    _call(fn, self.devices_now())
                for port in list(self.ports.values()):
                    port._devices_changed()
            elif kind == "set":
                # A knob turned a setting on the page: the synth here is told, so that reading it back gives what it is.
                b = self.bound.get(m.get("id"), {}).get(_key(m.get("setting")))
                if b is not None:
                    b[0]._told(m.get("setting"), m.get("value"))
                    if b[1] is not None:
                        _call(b[1], b[0].get(m.get("setting")), m.get("setting"))
            elif kind == "noteOn":
                self.held[m.get("note")] = m.get("velocity") or 0
                self.last = [m.get("velocity") or 0, self.sound.clock()]
                for fn in list(self.on["note"]):
                    _call(fn, m.get("note"), m.get("velocity"), m.get("channel"))
            elif kind == "noteOff":
                self.held.pop(m.get("note"), None)
                if self.on["note_off"]:
                    for fn in list(self.on["note_off"]):
                        _call(fn, m.get("note"), m.get("channel"))
                else:
                    for fn in list(self.on["note"]):
                        _call(fn, m.get("note"), 0, m.get("channel"))
            elif kind == "control":
                for fn in list(self.on["control"]):
                    _call(fn, m.get("control"), m.get("value"), m.get("channel"))
            for fn in list(self.on["all"]):
                _call(fn, m)

    def devices_now(self):
        d = self.devices
        return {"inputs": list(d["inputs"]), "outputs": list(d["outputs"]), "available": d["available"]}

    # --- what is written
    def channel(self, channel, said):
        if channel is None:
            return 0
        if not isinstance(channel, int) or isinstance(channel, bool) or not 1 <= channel <= 16:
            raise ValueError("%s: channel needs a whole number from 1 to 16, not %s" % (said, _shown(channel)))
        return channel - 1

    def whole(self, value, said, what, most=127):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= most:
            raise ValueError("%s needs %s, a whole number from 0 to %d, not %s" % (said, what, most, _shown(value)))
        return value

    def notes(self, what, said):
        """Notes as MIDI has them: whole numbers from 0 to 127."""
        out = []
        for n in _notes_of(what):
            n = int(math.floor(n + 0.5))
            if not 0 <= n <= 127:
                raise ValueError('%s: MIDI has the notes 0 to 127 ("C-1" to "G9"), and %s is outside them' % (said, _shown(what)))
            out.append(n)
        return out

    def out(self, data, t, output):
        c = {"do": "send", "bytes": data, "t": t}
        if output is not None:
            c["output"] = str(output)
        self.command(c)

    # --- a synth's
    def play(self, synth, on, channel, vibrato):
        if on is False:
            self.command({"do": "play", "id": synth._id, "on": False})
            return
        c = {"do": "play", "id": synth._id,
             "vibrato": [synth.get("vibrato") or 0, 0.5 if vibrato is None else _amount(vibrato, "play_from_midi: vibrato", 0, 12)]}
        if channel is not None:
            c["channel"] = self.channel(channel, "play_from_midi") + 1
        self.command(c)

    def through(self, synth, on, channel, output):
        if on is False:
            self.command({"do": "through", "id": synth._id, "on": False})
            return
        c = {"do": "through", "id": synth._id, "channel": self.channel(channel, "send_to_midi") + 1, "note": synth._note}
        if output is not None:
            c["output"] = str(output)
        self.command(c)

    def turn(self, synth, do, setting, on_change, low, high, channel, control=None):
        """A setting of a synth that a knob turns: its range, and whether it moves by ratio (a pitch in Hz) or by amount."""
        said = "learn" if do == "learn" else "map_midi"
        if not isinstance(setting, str):
            raise ValueError("%s needs the name of a setting, as in %s, not %s"
                             % (said, 'lead.learn("cutoff")' if do == "learn" else 'lead.map_midi(74, "cutoff")', _shown(setting)))
        entry = _setting(setting)
        if entry is None:
            raise ValueError("%s: there is no setting called %s.%s" % (said, _shown(setting), _meant(setting, _SHOWN)))
        if on_change is not None and not callable(on_change):
            raise ValueError("%s: what comes after the setting is a function to call with each new value, not %s" % (said, _shown(on_change)))
        low = entry["min"] / entry["scale"] if low is None else low
        high = entry["max"] / entry["scale"] if high is None else high
        if not _is_number(low) or not _is_number(high):
            raise ValueError("%s: min and max need numbers, not %s and %s" % (said, _shown(low), _shown(high)))
        self.bound.setdefault(synth._id, {})[_key(setting)] = [synth, on_change]
        ratio = entry.get("unit") == "hz" and entry["scale"] == 1 and low > 0 and high / low >= 100
        c = {"do": do, "id": synth._id, "setting": setting, "min": low, "max": high, "kind": entry["kind"],
             "curve": "exp" if ratio else "lin"}
        if control is not None:
            c["control"] = control
        if channel is not None:
            c["channel"] = self.channel(channel, said) + 1
        self.command(c)

    def unmap(self, synth, setting):
        if setting is None:
            self.bound.pop(synth._id, None)
            self.command({"do": "unmap", "id": synth._id})
        else:
            self.bound.get(synth._id, {}).pop(_key(setting), None)
            self.command({"do": "unmap", "id": synth._id, "setting": setting})

    def choose(self, which, name, said):
        many = which == "input" and isinstance(name, (list, tuple)) and all(isinstance(n, str) for n in name)
        if name is not None and not isinstance(name, str) and not many:
            raise ValueError('%s needs the name of a MIDI device, as in %s(midi_devices()["%ss"][0]), not %s'
                             % (said, said, which, _shown(name)))
        known = self.devices[which + "s"]
        for n in ([] if name is None else [name] if isinstance(name, str) else name):
            if self.devices["available"] and n not in known:
                _tell("%s(%s): there is no MIDI %s called %s at the moment. %s. It will be used if it appears."
                      % (said, _shown(n), which, _shown(n),
                         "The %ss are: %s" % (which, ", ".join(_shown(k) for k in known)) if known else "No MIDI %s is plugged in" % which))
        self.command({"do": which, "name": list(name) if many else name})
        port = self.ports.get((which, None))
        if port is not None:
            port._chosen(name if isinstance(name, str) else None)

    def stop(self):
        for fns in self.on.values():
            del fns[:]
        self.bound.clear()
        self.hooked.clear()
        self.listening = self.clock_on = False
        self.command({"do": "stop", "t": self.sound.clock()})


def on_midi(fn=None):
    """Everything that arrives, decoded: on_midi(heard), where heard(message) reads message.type, message.note,
    message.velocity, message.control, message.value, message.channel, message.time and message.device.
    In a Pyctures scene a function of your own called on_midi is called without this."""
    m = _sound().midi
    m.add("all", fn, "on_midi", "heard")
    m.listen()
    return fn


def on_midi_note(fn=None):
    """A key went down: on_midi_note(played), where played(note, velocity, channel) is given the note as a number
    (60 is middle C) and how hard it was hit, from 0 to 1. A key coming up calls it with velocity 0, unless
    on_midi_note_off is used. In a Pyctures scene a function of your own called on_midi_note is called without this."""
    m = _sound().midi
    m.add("note", fn, "on_midi_note", "played")
    m.listen()
    return fn


def on_midi_note_off(fn=None):
    """A key came up: on_midi_note_off(let_go), where let_go(note, channel)."""
    m = _sound().midi
    m.add("note_off", fn, "on_midi_note_off", "let_go")
    m.listen()
    return fn


def on_midi_control(fn=None):
    """A knob, slider or pedal moved: on_midi_control(turned), where turned(number, value, channel) is given which
    one (0 to 127; the sustain pedal is 64) and its value, from 0 to 1."""
    m = _sound().midi
    m.add("control", fn, "on_midi_control", "turned")
    m.listen()
    return fn


def on_midi_devices(fn=None):
    """The devices are known, or one was plugged in or pulled out: on_midi_devices(found), where found(devices)
    is given {"inputs": [names], "outputs": [names], "available": True or False}."""
    m = _sound().midi
    m.add("devices", fn, "on_midi_devices", "found")
    if m.devices["available"] is not None:
        _call(fn, m.devices_now())
    else:
        m.ask()
    return fn


def use_midi_hooks(scene):
    """For an app that runs scenes: the scene's own functions called on_midi_note, on_midi_note_off, on_midi_control,
    on_midi and on_midi_devices are called with what arrives. Give it the scene's names (a dict, a module or an
    object). Pyctures does this for every scene, so `def on_midi_note(note, velocity, channel):` is enough.
    Nothing is asked of the page unless the scene has at least one."""
    if scene is None or isinstance(scene, (str, int, float)):
        raise ValueError("use_midi_hooks needs the scene's names, with functions such as on_midi_note among them, not %s" % _shown(scene))
    get = scene.get if isinstance(scene, dict) else lambda name: getattr(scene, name, None)
    for name in _MIDI_HOOKS:
        fn = get(name)
        if not callable(fn) or fn is globals()[name]:      # `from synths import *` gave the scene this module's own
            continue
        m = _sound().midi
        if (name, fn) not in m.hooked:
            m.hooked.add((name, fn))
            globals()[name](fn)


def send_midi(data=None, *, output=None, after=None, at=None, beat=None):
    """Any MIDI message at all, as its bytes: send_midi([0x90, 60, 100])."""
    try:
        listed = list(data) if isinstance(data, (list, tuple, bytes, bytearray)) else None
    except TypeError:
        listed = None
    if not listed or any(not isinstance(b, int) or isinstance(b, bool) or not 0 <= b <= 255 for b in listed) or listed[0] < 0x80:
        raise ValueError("send_midi needs the bytes of a MIDI message, beginning with its status byte, as in "
                         "send_midi([0x90, 60, 100]), not %s" % _shown(data))
    s = _sound()
    s.midi.out(listed, s.when("send_midi", after, at, beat), output)


def send_midi_note(note=None, velocity=0.8, length=0.5, *, channel=None, output=None, after=None, at=None, beat=None):
    """A note out to another device: send_midi_note("C4", 0.8, length="quarter"). Velocity is how hard, from 0 to 1.
    It is let go after `length` (seconds, or a note length by name); length=None holds it until send_midi_note_off.
    A list of notes, or a chord by name, is a chord."""
    said = "send_midi_note"
    if note is None:
        raise ValueError('send_midi_note needs a note, as in send_midi_note("C4")')
    s = _sound()
    m = s.midi
    notes = m.notes(note, said)
    velocity = _amount(velocity, "%s: velocity" % said)
    long = None if length is None else s.length(length, "%s: the length" % said)
    ch = m.channel(channel, said)
    t = s.when(said, after, at, beat)
    for n in notes:
        if velocity > 0:
            m.out([0x90 | ch, n, max(1, _seven(velocity))], t, output)
        if long is not None or not velocity > 0:
            m.out([0x80 | ch, n, 0], t + (long if velocity > 0 else 0), output)


def send_midi_note_off(note=None, *, channel=None, output=None, after=None, at=None, beat=None):
    """Let go of a note that send_midi_note is holding: send_midi_note_off("C4")."""
    if note is None:
        raise ValueError('send_midi_note_off needs a note, as in send_midi_note_off("C4")')
    s = _sound()
    m = s.midi
    ch = m.channel(channel, "send_midi_note_off")
    t = s.when("send_midi_note_off", after, at, beat)
    for n in m.notes(note, "send_midi_note_off"):
        m.out([0x80 | ch, n, 0], t, output)


def send_midi_control(number=None, value=None, *, channel=None, output=None, after=None, at=None, beat=None):
    """Turn a knob on the other device: send_midi_control(74, 0.5). The number is the control's, 0 to 127; the
    value is from 0 to 1."""
    said = "send_midi_control"
    s = _sound()
    m = s.midi
    data = [0xb0 | m.channel(channel, said), m.whole(number, said, "the number of a control"), _seven(_amount(value, "%s: the value" % said))]
    m.out(data, s.when(said, after, at, beat), output)


def send_midi_bend(bend=None, *, channel=None, output=None, after=None, at=None, beat=None):
    """Bend the pitch on the other device: send_midi_bend(0.5), from -1 to 1, and 0 to let it go back."""
    s = _sound()
    m = s.midi
    b = _amount(bend, "send_midi_bend", -1, 1)
    v = int(_clamp(math.floor(8192 + b * (8192 if b < 0 else 8191) + 0.5), 0, 16383))
    m.out([0xe0 | m.channel(channel, "send_midi_bend"), v & 127, v >> 7], s.when("send_midi_bend", after, at, beat), output)


def send_midi_program(number=None, *, channel=None, output=None, after=None, at=None, beat=None):
    """Choose a sound on the other device by its number: send_midi_program(5)."""
    s = _sound()
    m = s.midi
    data = [0xc0 | m.channel(channel, "send_midi_program"), m.whole(number, "send_midi_program", "the number of a sound")]
    m.out(data, s.when("send_midi_program", after, at, beat), output)


def send_midi_clock(on=True):
    """Send the beat to other devices, so that their own sequencers keep time with set_tempo: send_midi_clock(),
    and send_midi_clock(False) to stop."""
    s = _sound()
    s.midi.clock_on = on is not False
    s.midi.command({"do": "clock", "on": s.midi.clock_on, "bpm": s.tempo, "t": s.clock()})


def midi_devices():
    """The devices there are: {"inputs": [names], "outputs": [names], "available": True, False or None}.
    The page is asked and answers with a later frame, so the first call gives empty lists and available None:
    use on_midi_devices(found) to be called when they are known, or ask again in update()."""
    m = _sound().midi
    m.ask()
    return m.devices_now()


def use_midi_input(name=None):
    """Listen to one input by its name (or a list of names), instead of all of them: use_midi_input("Keystation 49").
    No name: all again."""
    _sound().midi.choose("input", name, "use_midi_input")


def use_midi_output(name=None):
    """Send to one output by its name, instead of the first: use_midi_output("Minilogue"). No name: the first again."""
    _sound().midi.choose("output", name, "use_midi_output")


class MidiPort:
    """The MIDI device and the channel as a TARGET, which a select on the screen is tied to as a dial is tied to
    a synth: what midi_input(), lead.midi_input() and midi_output() give. It has two settings, "device" and
    "channel": port.get("device"), port.set("channel", 2), port.describe("device")["choices"], and port.device
    and port.channel as attributes. The choices follow what is plugged in, which the page says a frame late: until
    it has, a device reads "no devices". port.on_change(fn) calls fn(name) when a value or the choices change."""

    def __init__(self, midi, which, synth):
        self._midi, self._which, self._synth = midi, which, synth
        self._device, self._channel, self._heard = None, None, []
        self._told = None        # the name the page was last told, which is None while the chosen device is away
        self.names = list(_NAMES["midi"].get("choices", {}).get("settings", ("device", "channel")))

    def _words(self):
        w = _NAMES["midi"].get("choices", {})
        return w.get("all", "all"), w.get("none", "no devices"), w.get("unavailable", "no MIDI here")

    def _devices(self):
        d = self._midi.devices
        return list(d[self._which + "s"]), d["available"]

    def get(self, setting):
        every, none, unavailable = self._words()
        if _key(setting) == "channel":
            return str(self._channel) if self._channel else every if self._which == "input" else "1"
        if _key(setting) != "device":
            return None
        known, available = self._devices()
        if available is False:
            return unavailable
        if not known:
            return none
        if self._device in known:
            return self._device
        return every if self._which == "input" else known[0]       # (a chosen device that is away reads as what is used meanwhile)

    def describe(self, setting):
        every, none, unavailable = self._words()
        numbers = [str(n) for n in range(1, 17)]
        if _key(setting) == "channel":
            return {"name": "channel", "kind": "text", "choices": [every] + numbers if self._which == "input" else numbers,
                    "default": every if self._which == "input" else "1"}
        if _key(setting) != "device":
            return None
        known, available = self._devices()
        choices = [unavailable] if available is False else [none] if not known else ([every] + known if self._which == "input" else known)
        return {"name": "device", "kind": "text", "choices": choices, "default": choices[0]}

    def set(self, setting, value):
        every, none, unavailable = self._words()
        c = {"do": self._which}
        if _key(setting) == "channel":
            if value is None or value == every:
                self._channel = None
            else:
                number = int(value) if isinstance(value, str) and value.strip().isdigit() else value
                self._midi.channel(number, "midi_%s: channel" % self._which)      # 1 to 16, or it says so
                self._channel = number
            c["channel"] = self._channel
        elif _key(setting) == "device":
            if value is not None and not isinstance(value, str):
                raise ValueError("midi_%s: device needs the name of a MIDI device, not %s" % (self._which, _shown(value)))
            self._device = None if value in (None, every, none, unavailable) else value
            known, available = self._devices()
            # The page is told a name only while that device is there (or before it has said what is there).
            self._told = self._device if self._device in known or available is None else None
            c["name"] = self._told
        else:
            raise ValueError('midi_%s has "device" and "channel", and no %s' % (self._which, _shown(setting)))
        if self._synth is not None:
            c["id"] = self._synth._id
        self._midi.command(c)
        self._changed(_key(setting))
        return self

    def on_change(self, fn):
        if not callable(fn):
            raise ValueError("on_change needs a function to call, as in on_change(lambda name: ...), not %s" % _shown(fn))
        self._heard.append(fn)
        return lambda: self._heard.remove(fn) if fn in self._heard else None

    def _chosen(self, name):
        self._device = self._told = name
        self._changed("device")

    def _changed(self, name):
        for fn in list(self._heard):
            _call(fn, name)

    def _devices_changed(self):
        """The devices came or went. A chosen device that is pulled out falls back, which is said once, and is
        chosen again when it returns: falling back is the sender's work (synths.js's docs/midi.md)."""
        known, available = self._devices()
        want = self._device if self._device in known else None
        if want != self._told:
            if want is None:
                _tell("the MIDI %s %s is not there any more, so %s is used. It will be chosen again if it comes back."
                      % (self._which, _shown(self._device), "every input" if self._which == "input" else "the first output"))
            self._told = want
            c = {"do": self._which, "name": want}
            if self._synth is not None:
                c["id"] = self._synth._id
            self._midi.command(c)
        self._changed("device")

    device = property(lambda self: self.get("device"), lambda self, value: self.set("device", value))
    channel = property(lambda self: self._channel or (self._words()[0] if self._which == "input" else 1),
                       lambda self, value: self.set("channel", value))

    def level(self):
        """How hard the last note was hit, fading away: from 0 to 1, for a meter that is an activity light. It
        follows the notes Python has been handed, so only while the program listens (on_midi_note, on_midi)."""
        if self._which != "input":
            return 0
        self._midi.listen()
        hit, when = self._midi.last
        return hit * 0.5 ** ((self._midi.sound.clock() - when) / 0.09)       # halving every 90 ms

    def notes(self):
        """The keys held down now, as numbers, from the notes Python has been handed."""
        if self._which != "input":
            return []
        self._midi.listen()
        return sorted(self._midi.held)


def _midi_port(which, synth):
    m = _sound().midi if synth is None else synth._sound.midi
    key = (which, synth._id if synth is not None else None)
    if key not in m.ports:
        m.ports[key] = MidiPort(m, which, synth)
        m.ask()
    return m.ports[key]


def midi_input():
    """The MIDI device and channel listened to, as something a control is tied to: select("device", midi_input(),
    "device") and select("channel", midi_input(), "channel"). It is the choice use_midi_input makes in code.
    lead.midi_input() is the same for what plays one synth alone. See MidiPort."""
    return _midi_port("input", None)


def midi_output():
    """The MIDI device and channel sent to, as something a control is tied to: select("device", midi_output(), "device")."""
    return _midi_port("output", None)


def receive_midi(events):
    """Hand the program a message just as the page would: receive_midi({"type": "noteOn", "note": 60, "velocity": 0.8,
    "channel": 1}), or a list of them. A host whose player is elsewhere gives this what the player's on_midi gave;
    a scene uses it to pretend a keyboard is there."""
    _sound().midi.receive(events)


def stop_midi():
    """Finished with MIDI: every function forgotten, nothing played from a keyboard, sent on or tied to a knob,
    and the notes sent out let go."""
    s = _sound()
    if s._midi is not None:
        s._midi.stop()


def _seven(v):
    return int(_clamp(math.floor(v * 127 + 0.5), 0, 127))


_read_names()
