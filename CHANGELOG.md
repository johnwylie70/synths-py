# Changes

## Unreleased

- The library: `play_sound`, `play_note`, `play_notes`, `make_synth`, `load_sample`, `play_song`, `stop_sound`, `stop_song`, `set_volume`, `mute_sound`, `unmute_sound`, `set_effects`, `set_tempo`, `beats`, `beat` and `sound_time`. The same names as synths.js, in Python's spelling.
- A synth's settings are plain attributes (`lead.cutoff = 800`, `lead.vibrato_rate = 6`) that read back what was set. `lead.play`, `lead.start` (a note that stays, and can slide), `lead.stop`, `lead.play_notes`, `lead.set(cutoff=4000, slide=2)` and `lead.remove`.
- Chords by name (`lead.play("Cm7")`, `chord_notes("C3", "minor")`), arpeggios (`lead.arp("Cm7")`, `lead.start_arp("Am")` with `chord.change("F")`, `play_arp`, `start_arp`) and step macros (`make_synth("chip", macro=[…])`, `lead.macro = …`).
- Songs: `song = play_song("tune.mod")` plays a `.mod`, an `.xm` or a song in synths' own format, with `pause`, `resume`, `seek`, `stop`, `song.volume` and `song.repeat`, and `patches=` for a song's instruments that are synths by name.
- `after=`, `at=` and `beat=` on everything that makes a sound.
- Mistakes are said in plain words, with what was probably meant: a sound, synth, setting, choice, note, chord or order that does not exist.
- The names of every sound, ready-made synth and setting are those of synths.js, carried inside the one module by `scripts/sync_names.py`.
- In a Pyctures scene a frame's sounds travel as one command in the frame's own message, timed on Python's clock. A synth's `page` is the page's own object for it, so dials and piano keys made with pydials act on it at once. `main_synth()` and `sound_output()` can be tied to dials too.
- `synths.connect(send)` hands every command to a host.
- A program started with plain Python is started again with `pyctures run` when Pyctures is installed, and otherwise says how to run it and carries on in silence.
