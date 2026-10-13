# synths

[![MIT licence](https://img.shields.io/badge/licence-MIT-green)](LICENSE)

synths is for making sounds and music in Python, and for enjoying it: game sounds in one line, notes and tunes, synths you shape yourself, arpeggios, recorded samples, effects, tracker songs, MIDI, and your own voice through a microphone, changed, recorded and saved. It is for any age and any level. You type a line and hear something. It is the sound sibling of [Pyctures](https://github.com/johnwylie70/pyctures), designed for projects made in [Circuitry Studio](https://www.circuitry.dev).

Prefer JavaScript? [synths.js](https://github.com/johnwylie70/synths.js) is the same library for JavaScript, with the same names. The sound engine itself is [synths-core](https://github.com/johnwylie70/synths-core).

## Install

**synths is not published yet.** It is not on PyPI, and the Pyctures that `pip install pyctures` gives today (0.2.0) has no sound in it. Until the release that has, sound runs from a checkout of Pyctures that carries it (Pyctures keeps a copy of synths inside itself):

```bash
pip install -e path/to/pyctures
```

From that release on, this is all there will be to it:

```bash
pip install pyctures
```

Pyctures comes with synths, and plays its sound in your web browser. Python 3.9 or newer. Nothing else is installed: no sound drivers, no other library.

## Start with four small programs

Each one is a whole program. [How to run one](#run-it) is just below.

**1. A sound.** Save this as `hello.py`:

```python
from synths import *

play_sound("coin")
```

There are fourteen ready-made game sounds: `coin`, `jump`, `laser`, `shoot`, `explosion`, `hit`, `powerup`, `blip`, `click`, `zap`, `bounce`, `pop`, `win` and `lose` (`sound_names()` lists them). In a game it is one line where the thing happens:

```python
if star.touches(basket):
    play_sound("coin")
```

**2. A note, and a tune.**

```python
from synths import *

play_note("C4")                              # middle C, for half a second
play_notes("E4 G4 C5 - G4 C5:2", 0.25, after=1)
```

A note is a letter and a number: `"C4"` is middle C, `"A4"` is the A above it, `"F#3"` is F sharp and `"Bb5"` is B flat. `play_notes` plays a tune a step at a time, here a step every quarter of a second: `-` is a rest and `:2` makes a note last two steps. `after=1` starts it a second from now.

**3. A synth of your own.**

```python
from synths import *

lead = make_synth(wave="saw", cutoff=1200, attack=0.01, release=0.3)

lead.play("E4", 0.5)                 # a note, for half a second
lead.play(["C4", "E4", "G4"], 1)     # three notes at once: a chord
lead.play("Cm7", 1)                  # or a chord by its name
lead.cutoff = 800                    # every setting is a plain attribute
lead.echo = 0.4
```

`wave` is the raw sound (`"sine"`, `"triangle"`, `"saw"`, `"square"`), `cutoff` is how bright it is, `attack` is how quickly a note begins and `release` is how long it takes to die away. Change the numbers and run it again. Or start from a ready-made synth: `make_synth("bass")`.

**4. A beat that keeps going.**

```python
from synths import *

make_synth("kick").play_notes("C2 - - - C2 - - -", 0.125, repeat=True)
make_synth("hat").play_notes("C4 C4", 0.125, repeat=True, volume=0.4)
make_synth("bass").play_notes("C2 - C2 C3 - C2 - Eb2", 0.125, repeat=True)
```

`repeat=True` plays a tune round and round. The parts stay together, however busy your program is, because the sound engine keeps the time and not Python.

## Run it

```bash
pyctures run hello.py
```

Your browser opens and the program runs, in your own Python. Save the file and it runs again. `pyctures build hello.py -o site/` writes a folder that plays in any browser, on any website, with nothing to install there.

Plain `python hello.py` works too, when Pyctures is installed: synths starts the program again with `pyctures run` for you, and says so. Without Pyctures it tells you what to type and carries on in silence, so a program with sound in it never stops because of the sound.

### The first tap

Browsers keep a page silent until the person using it has clicked, tapped or pressed a key. Pyctures says so over the scene ("Click, tap or press a key to turn the sound on"), and the first touch turns the sound on. Until then a tune you started waits, and begins at that touch; a single note or sound effect from long before it is let go, because played late it would be wrong.

## In a Pyctures scene

Sound goes with drawing in the same program, with the same `update(dt)` and `draw()`:

```python
from synths import *

ball = Sprite("⚽", 200, 100, size=48)
ball.vy = 0

def update(dt):
    ball.vy += 900 * dt
    ball.update(dt)
    if ball.y > height - 24:
        ball.y = height - 24
        ball.vy = -ball.vy * 0.9
        play_sound("bounce")

def draw():
    background("seagreen")
    ball.draw()
```

With [pydials](https://github.com/johnwylie70/pydials), dials and a piano keyboard on the screen play a synth and shape it:

```python
from pyctures import *
from synths import *
from pydials import *

lead = make_synth("lead")
dial("cutoff", lead, "cutoff")
dial("resonance", lead, "resonance")
slider("attack", lead, "attack")
scope(lead)
keyboard(lead, octave=4)
```

A key sounds the moment it is touched and a dial is heard as it turns, because the page plays the synth itself; Python is told afterwards, so `lead.cutoff` reads what the dial says.

## Notes

A note is a name (`"C4"`, `"F#3"`, `"Bb5"`) or a number, where 60 is middle C and each whole number is one key of a piano (61 is C sharp, 72 is the C above). A number with a fraction is between two keys. `note_number("A4")` gives 69.

```python
play_note("C4")                       # half a second
play_note("C4", 2)                    # two seconds
play_note("C4", 2, 0.3)               # and quiet: loudness goes from 0 to 1
play_note(["C4", "E4", "G4"])         # a chord
play_note("C4", length=2, volume=0.3, pan=-1, after=0.5)   # the same things by name; pan -1 is left, 1 is right
```

A chord has a name too: `"Cm"`, `"Cmaj7"`, `"Csus4"`, or a root and a kind, `chord_notes("C3", "minor")`. A letter followed by a number is always a note, so `"C7"` is the note C in octave 7; a seventh chord is `"Cdom7"`. The kinds: major, minor, dim, aug, sus2, sus4, 5, 6, m6, 7, maj7, m7, dim7, m7b5, mmaj7, add9, 9, maj9, m9 and octave.

## Lengths

Wherever a length is wanted there are two ways to say it, and they are never mixed up:

- **A number is seconds.** `play_note("C4", 0.5)` lasts half a second, whatever the tempo.
- **A name is a note length**, measured against the tempo: `play_note("C4", "quarter")`. At `set_tempo(120)` a quarter note is half a second; at 60 it is a whole one.

| | | |
|---|---|---|
| `"whole"` | `"1/1"`, `"w"` | 4 beats |
| `"half"` | `"1/2"`, `"h"` | 2 beats |
| `"quarter"` | `"1/4"`, `"q"` | 1 beat |
| `"eighth"` | `"1/8"`, `"e"` | half a beat |
| `"sixteenth"` | `"1/16"`, `"s"` | a quarter of a beat |

A dot makes one half as long again (`"quarter."`, `"q."`), and a triplet fits three where two were (`"eighth triplet"`, `"e3"`). Names work for the length of a note, a chord, an arpeggio or a sound (`play_sound("win", length="half")` cuts a sound short there, or holds its last note until then), for the step of a tune, and for `after="half"`. `set_tempo(140)` sets the beats in a minute (120 until you say), and `beats(3)` is how many seconds three beats last.

## A tune, one note a line

`play_note` plays a note **now**. `note` plays the **next** note of a tune: each one begins where the one before it ended, so a tune is written as ordinary lines of code, with loops and ifs, and no arithmetic.

```python
set_tempo(100)

note("E4", "quarter")
note("G4", "quarter")
rest("quarter")
note("C5", "half")
chord("Cm", "whole")

for name in ["C4", "D4", "E4"]:
    note(name, "eighth")
```

The same tune as text, for comparison: `play_notes("E4:q G4:q -:q C5:h Cm:w C4:e D4:e E4:e")`.

In a line, a length is a name, or a number of **beats** (`note("C4", 2)` is a half note); with nothing said it is a quarter. `note`, `chord` and `rest` write on the synth `play_note` uses, and every synth has its own line: `lead.note("C4", "eighth")`.

- **Two lines together.** Lines written in the same go begin together, however much code is between them: write the whole melody, then the whole bass, and they start on the same instant.

  ```python
  bass = make_synth("bass")
  for n in ["E4", "G4", "C5", "G4"]:
      lead.note(n, "quarter")
  bass.note("C2", "half")
  bass.note("G2", "half")
  ```

- **A section that repeats.** A `for` loop writes a section several times. `loop_notes` has it go round for ever, kept in time by the sound engine, and it follows `set_tempo` as it plays:

  ```python
  kick, snare = make_synth("kick"), make_synth("snare")
  with loop_notes() as drums:
      kick.note("C3", "quarter")
      snare.note("A3", "quarter")
  drums.stop()
  ```

  `with loop_notes(4):` goes round four times, and the lines carry on after it. A function works too: `loop_notes(section)`.

- **Starting over.** A line carries on from where it ended; if it ended a while ago, the next note begins now. `start_lines()` begins every line again from now, `start_lines(after="whole")` a bar from now, and `lead.start_line()` begins one.

## Tunes

```python
tune = play_notes("C4 E4 G4 - C5:2 G4+B4+D5 Am", 0.25, repeat=True)
tune.stop()
```

The notes are text with spaces between, or a list: `["C4", None, ["C4", "E4"]]`, where `None` is a rest and a list inside is a chord. In text a chord is joined with `+`, or named. The second thing is the time of a step: seconds as a number, or a note length (`"sixteenth"`); leave it out and a step is an eighth note. After a colon, a number is so many steps (`C5:2`) and a letter is a note length (`C5:h`). A tune with its step in seconds keeps that speed; one in note lengths follows `set_tempo`, even while it plays. More by name: `repeat` (`True`, or how many times), `volume`, `hold` (how much of its step a note sounds for, 0.9 unless you say), and `after`, `at` or `beat`.

Every synth has `play_notes` too: `make_synth("bass").play_notes("C2 C2 G2 C2", 0.25)`.

## Synths

```python
bass = make_synth("bass")                        # a ready-made synth
soft = make_synth("lead", cutoff=900)            # a ready-made one, changed
mine = make_synth(wave="square", attack=0.2)     # one from nothing
```

The ready-made synths: `keys` (what `play_note` uses), `bass`, `lead`, `pad`, `pluck`, `organ`, `strings`, `bell`, `flute`; the chip sounds `chip`, `chip_lead`, `chip_bass`, `chip_noise`, `chip_kick`, `chip_snare` and `chip_hat`; and the drums `kick`, `snare` and `hat`. All of them are settings of the same engine, not recordings, so every one can be changed. `synth_names()` lists them, and `main_synth()` is the one `play_note` and `play_notes` use, for changing its settings or tying a dial to it.

What a synth does:

| | |
|---|---|
| `lead.play("E4", 0.5)` | a note for half a second. A list of notes, or a chord's name, is a chord. No note at all plays the synth's own (a drum's). |
| `lead.play("E4", 0.5, 0.8)`, `lead.play("E4", length=1, volume=0.5, pan=-1, after=2)` | how loud, where, when |
| `held = lead.start("E4")` | a note that stays until `held.stop()`. While it sounds: `held.slide_to("G4", 0.5)`, `held.pitch = "A4"`, `held.volume = 0.5`, `held.pan = -1` |
| `lead.note("E4", "quarter")`, `lead.chord("Cm", "half")`, `lead.rest("eighth")` | the next note of this synth's line: see [A tune, one note a line](#a-tune-one-note-a-line) |
| `lead.stop()`, `lead.stop("E4")` | let go of every note of the synth, or of one |
| `lead.play_notes("C4 E4 G4", 0.25)` | a tune on this synth |
| `lead.cutoff = 800` | change a setting; notes already sounding change too |
| `lead.set(cutoff=4000, resonance=0.4)`, `lead.set(cutoff=4000, glide=2)` | change several, or glide there over two seconds (`slide=2` is an older word for the same) |
| `lead.voice = "robot"` | a voice changer on everything it plays: see [Your voice](#your-voice) |
| `lead.samples()`, `lead.level()`, `lead.notes()` | what it is doing now, for a scope, a meter or lit keys you draw yourself: see [Reading the sound back](#reading-the-sound-back) |
| `lead.arp("Cm7")` | a chord from one voice: see [Arpeggios](#arpeggios) |
| `lead.remove()` | finished with it |

### Settings

Every setting is a plain attribute, and reads back what you set: `lead.cutoff = 800`, `print(lead.cutoff)`.

| Setting | What it is |
|---|---|
| `wave` | the raw sound: `"sine"` (pure), `"triangle"` (soft), `"saw"` (bright), `"square"` (hollow), `"pulse"` (with `width`, 0.02 to 0.98) |
| `volume`, `pan` | how loud the synth is (1 is normal), and left (-1) to right (1) |
| `attack`, `decay`, `sustain`, `release` | the shape of a note's loudness: seconds to reach full, seconds to fall to the `sustain` level (0 to 1), which holds while the note lasts, and seconds to die away afterwards. A `sustain` of 0 makes a pluck or a drum |
| `cutoff`, `resonance` | the filter: `cutoff` is how bright (20 to 20000), `resonance` adds a whistle at the cutoff (0 to 1) |
| `filter` | `"lowpass"` (takes away the top; what `cutoff` does unless you say), `"highpass"`, `"bandpass"`, `"notch"`, `"off"` |
| `sweep`, `sweep_attack`, `sweep_decay`, `sweep_sustain` | each note opens the filter by `sweep` semitones and lets it close again: the "wow" of a synth bass |
| `octave`, `pitch`, `tune` | move every note by octaves, by semitones, or by hundredths of a semitone |
| `glide` | seconds to slide from one note to the next |
| `mode` | `"poly"` (many notes at once), `"mono"` (one at a time), `"legato"` |
| `voices`, `detune`, `spread` | several copies of each note, a little out of tune and spread left to right: a thick sound |
| `wave2`, `level2`, `pitch2`, `detune2` | a second wave mixed in, at its own pitch |
| `sub`, `noise` | a wave an octave below, and hiss (each 0 to 1) |
| `vibrato`, `vibrato_rate`, `vibrato_delay` | a wobble of pitch: how far (semitones), how fast, how long before it begins |
| `tremolo`, `wobble`, `wobble_rate` | a wobble of loudness, and of the filter |
| `pwm`, `pwm_rate` | the pulse wave's width moving in and out (0 to 1: how far) and how fast, in Hz: the thick, shifting sound of a `"pulse"` or `"square"` wave. `pwm_rate` and `wobble_rate` are one speed under two names |
| `pitch_sweep`, `pitch_sweep_decay` | each note begins that many semitones off and falls into place: a drum's thump, a laser |
| `echo`, `reverb`, `chorus` | how much of the synth goes to each effect (0 to 1) |
| `distortion`, `crush` | grit (0 to 1), and the bits each sample keeps (16 is clean, 4 is an old games console) |

There are more: `setting_names()` lists every one, and each also answers to the engine's own name for it (`lead.filter_cutoff`).

## Arpeggios, fast and musical

A chord is notes together. An arpeggio is the notes of a chord one at a time. There are two kinds here, and they sound nothing alike.

**Fast: the chord of a Commodore 64 tune.** One voice whose pitch jumps through the chord fifty times a second, which the ear hears as a shimmering chord. The chip had only three voices to spend.

```python
play_arp("Cm7")                             # half a second of C minor seventh
play_arp("C4", "minor", 2)                  # a note and a kind, for two seconds
play_arp(["C4", "E4", "G4", "C5"], 1, speed=12, order="up-down")
```

`speed` is steps a second: 50 unless you say, which is the speed chip music was written at; at 12 you can hear each step.

**Musical: each step a note of its own, in time with the tempo.** Say how long a step is with `step`, a note length, and every step is struck afresh, held for part of the step and let go.

```python
set_tempo(138)
lead = make_synth("pluck")
lead.arp("Am", "whole", step="sixteenth", octaves=2, gate=0.5)       # a trance arpeggio: up through two octaves
lead.arp("C", "whole", step="eighth", order="up-down", gate=0.9)     # a pop arpeggio: slower, nearly joined up
```

What an arpeggio can be told:

| | |
|---|---|
| `step` | how long a step is: `"sixteenth"`, `"eighth"`, `"eighth."`, `"1/12"`, or a number of beats. It follows `set_tempo`, even while the arpeggio is sounding |
| `speed` | steps a second instead (50): the fast kind |
| `order` | `"up"`, `"down"`, `"up-down"`, `"up-down2"` (the top and bottom notes twice), `"as written"`, `"random"`, `"together"` (the whole chord at each step: stabs) |
| `octaves` | 1 to 4: through the chord, then the same an octave up |
| `gate` | how much of its step each note is held, 0.05 to 1 (0.5). Short is plucked; 1 is joined up |
| `swing` | 0 to 0.75: every second step is that much of a step late (0.33 is a triplet feel) |
| `accent` | how hard each step is struck, up to eight numbers from 0 to 1 that go round: `[1, 0.5, 0.5, 0.5]`. 0 is a rest |
| `pattern` | a rhythm of its own in the place of the order: `"1 - 3 2 _ 1 3 5^"`, or one by name |
| `style` | `"strike"` (each step a new note: what `step` gives) or `"slide"` (one voice whose pitch jumps: what `speed` gives). Say it to have the other |

In a **pattern** each step is a number (that note of the chord, counted from 1 at the lowest; past the top it carries on an octave up), `-` for a rest, or `_` to hold the last note through the step. After a note, `'` is an octave up, `,` an octave down, `^` an accent and `:3` its own gate in tenths; `~` before a note slides into it. The patterns by name are `bounce`, `octaves`, `root-fifth`, `thumb`, `converge`, `diverge`, `offbeat`, `gallop`, `trance` and `acid`.

One that stays, and changes chord under your hands:

```python
chord = lead.start_arp("Am", step="sixteenth", pattern="trance")
chord.change("F")                          # from the next step, and it keeps its place in the pattern
chord.gate = 0.3                           # so do gate, octaves, swing, accent, pattern, order, step and speed
chord.stop()
```

A chord has room for eight notes. Every synth has `arp` and `start_arp`; with no synth (`play_arp`, `start_arp`) they play on a chip sound. The length after the chord is how long the arpeggio sounds, as for any note (half a second unless you say), and it takes `volume`, `pan`, `after`, `at` and `beat` like any note; `chord.change("F", after=2)` changes it later. A struck arpeggio is ordinary notes, so it goes through the synth's envelope and filter at every step, and plays the right recordings of an instrument from `load_samples`. The tempo an arpeggio in steps keeps is the page's: where several scenes share a page, it is the tempo that was set last.

A synth can have a pattern of its own, which every arpeggio of it follows unless it says another: `lead.arp_pattern = "trance"` (or the steps, or a list of them such as `[1, 0, 3, 2]`, where 0 is a rest). It reads back as its text, `"1^ - 3 2 - 1^ 3 -"`, and `lead.arp_pattern = "off"` takes it away. `lead.arp_step()` is the step that is sounding, counted from 0, for drawing it.

For a sequencer of your own that looks ahead: `sound_time()` is the sound's clock in seconds, and `lead.play("C4", at=sound_time() + 0.25)`, `lead.note_on("C4", 0.8, at=when)` and `lead.note_off("C4", at=when)` happen on the exact sample of that time.

### Bending a note

A note's pitch can move, on any synth and on a sample:

```python
lead.play("A4", 1, bend="scoop")                  # up into the note from just below, as a singer starts one
lead.play("C5", 1, glide="sixteenth")             # slides to C5 from the note this synth played last
lead.play("E5", 2, vibrato=True)                  # begins straight, then starts to sing
lead.play("A3", 1, bend="fall")                   # droops away at its end
lead.play("C4", 1, slide=12)                      # an octave up, at once: a laser
```

| | |
|---|---|
| `glide` | the note starts at the pitch of the synth's last note and slides to its own: `True` (a sixteenth), a note length, or seconds |
| `bend` | `"scoop"` (from 2 semitones below, over a sixteenth), `"fall"` (5 down over an eighth, ending with the note), `"dip"` (a semitone down and back), or `{"to": 2, "over": "eighth"}`: how far in semitones, or to a note by name, and how long. `{"shape": "scoop", "to": -5}` is a scoop of another size |
| `slide` | a bend by a number of semitones over a sixteenth, or `{"to": ..., "over": ...}` |
| `vibrato` | `True`, or `{"depth": 0.3, "rate": 6, "delay": "eighth"}`: semitones each way, times a second, and how long the note sounds first |

They are for one note at a time (a chord's notes would all be moved to one pitch), in `play`, `start` and `play_note`; a tune from `play_notes` does not take them. A note that is held can be moved as it sounds: `held = lead.start("C4")`, then `held.slide_to("E4", 0.2)`, `held.vibrato()` and `held.vibrato(False)`.

A **step macro** is the same idea for the sound itself: a short list of steps that every note of a synth plays through, each changing the wave, pitch, pulse width, cutoff or volume. It is what makes chip drums.

```python
drum = make_synth("chip", macro=[{"wave": "noise", "pitch": 24}, {"wave": "square"}, {"pitch": -5, "volume": 0.8}])
drum.macro_rate = 60          # steps a second
drum.macro = None             # take it away again
```

## The trance gate

A trance gate turns a synth's sound up and down in a pattern of steps, in time with the tempo, so a held chord becomes a rhythm. It chops whatever the synth is playing.

```python
set_tempo(138)
pad = make_synth("pad", echo=0.3)
pad.trance_gate = "x.x.xx.x"                # x is open, . is closed; a step is a sixteenth
pad.start(["A3", "C4", "E4"])
```

`pad.trance_gate = "trance"` is a pattern by name: `eighths`, `offbeat`, `gallop`, `trance`, `stutter`, `pump`, `triplets` (with `trance_gate_rate` 6) and `dotted`. A digit from `0` to `9` in a pattern is a step part of the way open, so `"2468"` swells; a list of levels from 0 to 1 is a pattern too. It reads back as the pattern's text, and `pad.trance_gate = "off"` takes it away.

Its settings, each one a dial can be tied to:

| | |
|---|---|
| `trance_gate_rate` | steps to a beat: 4 is sixteenths, 2 eighths, 3 and 6 triplets |
| `trance_gate_depth` | how far a closed step closes: 1 is silence, 0.5 is half. Giving a pattern makes it 1 |
| `trance_gate_smooth` | seconds from one level to the next; longer is softer |
| `trance_gate_swing` | every second step that much of a step late |
| `trance_gate_stereo` | left and right by turns |
| `trance_gate_sends` | `False`: the echo and the reverb are fed the sound before it is chopped |

`pad.set_trance_gate("x.x.xx.x", rate="eighth", depth=0.8, smooth=0.02)` says a pattern and its settings in one line, with the rate as a note length. The steps begin at `set_tempo`: call it where the bar begins and the gate is on the beat. `pad.trance_gate_step()` is the step that is sounding, for drawing it. (The word `gate` alone is something else twice over: an arpeggio's `gate` is how long each of its notes is held, and the microphone's `mic.gate` is its noise gate.)

## Effects

A synth sends some of its sound to an effect with one word: `lead.echo = 0.4`, `lead.reverb = 0.3`, `lead.chorus = 0.5`. `distortion` and `crush` belong to the synth alone. The echo, the reverb and the chorus are shared by every synth, and are shaped with `set_effects`:

```python
set_effects(echo_time=0.3, echo_feedback=0.5, echo_bounce=True, reverb_size=0.8)
```

| | |
|---|---|
| `echo_time`, `echo_feedback`, `echo_tone`, `echo_bounce` | seconds between echoes, how much each feeds the next (0 to 0.95), how much treble survives, and whether they bounce left and right |
| `reverb_type`, `reverb_size`, `reverb_damping` | what kind of space the reverb is, how big it is, and how soon its treble dies |
| `reverb_decay`, `reverb_predelay`, `reverb_low_cut` | seconds the tail takes to die away (0 leaves it to the type and the size), a gap before it begins, and where its bass is cut |
| `chorus_rate`, `chorus_depth` | how fast and how far the chorus wobbles |

The reverb is one room that every synth sends into, so its type and shape are one setting for everything: `set_effects(reverb_type="hall", reverb_decay=3)` and `lead.reverb_type = "hall"` do the same thing, and every synth reads the same value back. The types are `"room"`, `"hall"`, `"plate"`, `"cathedral"` and `"spring"`; `reverb_decay` is the seconds the tail takes to die away, `reverb_predelay` a gap before it begins, and `reverb_low_cut` keeps the bass out of it. With pydials it is a control like any other: `select("reverb", lead, "reverb_type")`.

## Samples

A sample is a recorded sound in a file beside your program: a `.wav`, or anything else your browser can read (`.mp3`, `.ogg`).

```python
kick = load_sample("kick.wav")
kick.play()                       # as it was recorded
kick.play("E4")                   # higher: a sample is a synth, and "C4" is its own pitch
kick.reverb = 0.3

hum = load_sample("hum.wav", loop=True, note="A3")   # goes round for as long as a note lasts; A3 is the note it was recorded at
hum.play("E4", 2)
```

There is nothing to wait for: play it straight away, and it sounds as soon as the file has arrived.

A sample can also be the wave of any synth, under its filter and its envelope:

```python
lead.sample = load_sample("piano.wav")                    # its wave is now "sample"; lead.wave = "saw" goes back
keys = make_synth(sample="piano.wav", note="C4", cutoff=1800, release=0.6)   # or all in one line: note is the note the recording is at
```

### Several recordings for one instrument

One recording stretched over a whole keyboard sounds thin at one end and muddy at the other. A real instrument is several recordings, each playing the keys near the note it was recorded at:

```python
piano = load_samples({"C2": "piano-C2.wav", "F#2": "piano-Fs2.wav", "C3": "piano-C3.wav"})   # the note each was played at
piano.play("E2")                  # the nearest recording (F#2), moved down to E
piano.reverb = 0.3                # a synth like any other: settings, dials, keyboard(piano), a tune, an arpeggio
```

The keys are split halfway between neighbours, and every key plays, below the lowest recording and above the highest too. With the notes in the files' names there is less to write: `load_samples(["piano-C2.wav", "piano-Fs2.wav", "piano-C3.wav"])` reads `C2`, `Fs2` (or `F#2`, `Gb2`) and `C3` from them, and a number alone (`60.wav`) is that key; `note_in_name("piano-Fs2.wav")` is how it reads one. A name with no note in it is refused, with what to do about it.

A drum kit is the same with `kit=True`: each key is its own sound, played as it was recorded whatever the key, to its end, and the keys between are silent.

```python
kit = load_samples({"C2": "kick.wav", "D2": "snare.wav", "F#2": "hat.wav"}, kit=True)
kit.play_notes("C2 F#2 D2 F#2", 0.25, repeat=True)
```

What else can be said:

- **`crossfade=3`** fades neighbouring recordings into each other over three keys, where a change from one to the next would be heard. `crossfade={"keys": 3, "loud": 0.1}` fades the loudness layers too.
- **Layers by how hard a note is played**, in the explicit form, a list of dicts: `load_samples([{"file": "soft-C4.wav", "note": "C4", "loud": [0, 0.5]}, {"file": "hard-C4.wav", "note": "C4", "loud": [0.5, 1]}])`. `loud` is the note's volume, from and to.
- **Takes that go in turn**: several files for one note, `{"C4": ["snare-1.wav", "snare-2.wav"]}`, and each hit plays the next.
- **By hand**, for each recording: `"from"` and `"to"` (its keys), `"tune"` (cents), `"volume"`, `"pan"`, `"release"` (seconds), `"one_shot"`, `"as_recorded"`, `"loop"`, `"start"` (frames). `loop=True` and `one_shot=True` after the files are for all of them.
- **Release.** With nothing said each recording has a release that suits its note, longer for the low ones, as a piano's are. `load_samples(files, release=1)` gives every recording that release in their place.
- **On an ordinary synth**: `lead.samples = {"C3": "a.wav", "C4": "b.wav"}`, `lead.set_samples(files, crossfade=3)` or `make_synth(samples={...}, cutoff=1800)`, and the recordings go through that synth's filter and envelope. `lead.samples = None` takes them away. (`lead.samples()` is still the wave for a scope.)
- **Reading it back**: `piano.zones()` is the list as you gave it, each with its file and its note. The keys each was worked out to play are the page's to know.

Where Python can read the files they are sent with the commands; otherwise the page fetches them from beside the scene, as for `load_sample`.

## When things start

Everything that makes a sound takes one of these:

```python
play_sound("coin", after=0.5)             # half a second from now
play_note("C4", 1, at=sound_time() + 2)   # at a time on the sound clock, which sound_time() reads
lead.play("E4", beats(1), beat=8)         # on beat 8
```

Beats are counted from `set_tempo(120)` (beats a minute; beat 0 is the moment you call it). `beats(2)` is how many seconds two beats last, and `beat()` is which beat it is now.

Sounds are placed on the exact sample they were asked for. That is why a tune you schedule with `after=` or `beat=`, or play with `play_notes`, stays in time even when your program is busy drawing. Everything is played a few hundredths of a second after it is asked for, so that this works; you will not notice it.

## MIDI

MIDI is how music keyboards, drum pads, boxes of knobs and synths talk to each other and to a computer. Plug a MIDI keyboard into your computer and one line makes it play a synth:

```python
lead = make_synth("keys", reverb=0.3)
lead.play_from_midi()
```

It follows the notes, how hard you hit each key, the pitch wheel, the modulation wheel and the sustain pedal. The first time a program uses MIDI the browser asks whether the page may use your MIDI devices: say yes. `lead.play_from_midi(channel=2)` listens to one channel alone, and `lead.play_from_midi(False)` stops.

The page plays the synth itself, where the keyboard is, and does not ask Python first. So a key sounds at once, even while your program is busy, or runs on another computer.

MIDI works in Chrome, Edge and Firefox on a computer. Safari, iPhones and iPads have no MIDI for web pages. Where there is none your program still runs: the page says so once, in the browser's console, and everything else carries on.

### Your own functions

In a Pyctures scene, give a function one of these names and it is called, like `on_key_down`:

```python
def on_midi_note(note, velocity, channel):
    play_sound("coin", velocity, pitch=note - 60)

def on_midi_control(number, value, channel):
    set_volume(value)
```

`note` is a number, where 60 is middle C, and `velocity` is how hard the key was hit, from 0 to 1. A key coming up calls `on_midi_note` with velocity 0, unless you write `def on_midi_note_off(note, channel):`, which is called then instead. `number` is which knob, slider or pedal it was (every one has a number from 0 to 127; the sustain pedal is 64) and `value` goes from 0 to 1. You may leave arguments off the end: `def on_midi_note(note, velocity):` is right too.

`def on_midi(message):` is given everything: `message.type` is `"noteOn"`, `"noteOff"`, `"control"`, `"bend"`, `"program"` and so on, with `message.note`, `message.velocity`, `message.control`, `message.value`, `message.bend`, `message.channel`, `message.device` (the name of what sent it), `message.data` (the bytes themselves) and `message.time`: when it happened, on the clock that `sound_time()` reads.

Your functions are called once a frame, with everything that arrived since the last one, so they hear a key up to a frame after it was pressed; `message.time` says exactly when. That wait is only for your own functions: `play_from_midi()` and `learn()` do not have it.

Anywhere else, or to give a function another name, hand it over: `on_midi_note(played)`, `on_midi_note_off(let_go)`, `on_midi_control(turned)`, `on_midi(heard)`.

### A knob turns a setting

```python
lead.learn("cutoff")                     # the next knob you turn on your controller is the cutoff from then on
lead.map_midi(74, "resonance")           # or say which knob, by its number
```

The knob goes through the setting's whole range, so nothing has to be worked out, and the page changes the synth itself, at once. `lead.cutoff` reads back what the knob has set, a frame later. A dial on the screen that is tied to the same setting (`dial("cutoff", lead, "cutoff")`, with pydials) turns with the knob. A function given next is called with each new value: `lead.learn("cutoff", print)`. `min=200, max=4000` narrow the range, and `lead.unmap_midi("cutoff")` lets it go.

### Sending

A synth or a drum machine on your desk can be played from your program:

```python
send_midi_note("C4")                                  # a note, let go half a second later
send_midi_note("C4", 0.8, length="quarter", channel=1)  # how hard, how long (seconds, or a note length), which channel (1 to 16)
send_midi_note(["C4", "E4", "G4"], beat=4)            # a chord, on beat 4
send_midi_control(74, 0.5)                            # turn knob 74 on the other device to half way
send_midi([0x90, 60, 100])                            # any message at all, as its bytes
```

Everything that is sent takes `after=`, `at=` or `beat=` like a sound ([When things start](#when-things-start)) and leaves at exactly that time. There are also `send_midi_note_off("C4")` (for a note sent with `length=None`, which is held), `send_midi_bend(0.5)` and `send_midi_program(5)`, which chooses a sound by its number. `output="Minilogue"` on any of them says which device. `stop_sound()` lets go of every note that has been sent and takes back the ones still to come.

`bass.send_to_midi()` sends what a synth plays, tunes and all, out as MIDI too; `channel=10` chooses the channel (10 is where drum machines listen). `send_midi_clock()` sends the beat, so that another device's own sequencer keeps time with `set_tempo`, and `send_midi_clock(False)` stops it.

### Which device

```python
def found(devices):
    print(devices["inputs"], devices["outputs"])     # the names of what is plugged in

on_midi_devices(found)                   # called when they are known, and again when one is plugged in or pulled out
use_midi_input("Keystation 49")          # listen to this one alone (otherwise: all of them)
use_midi_output("Minilogue")             # send to this one (otherwise: the first)
```

To choose on the screen instead, `midi_input()` and `midi_output()` are things a pydials control is tied to, with a `"device"` and a `"channel"`: `select("device", midi_input(), "device")`. `lead.midi_input()` is the same for one synth alone. The choices follow what is plugged in, which the page says a frame late.

`midi_devices()` gives the same `{"inputs": [...], "outputs": [...], "available": ...}` at any time, but the page has to be asked and its answer comes with a later frame: the first call gives empty lists with `available` as `None`. That is why `on_midi_devices` is there (in a scene, `def on_midi_devices(devices):`). `available` is `False` when there is no MIDI. `stop_midi()` forgets every function you gave and stops everything MIDI is doing.

With no keyboard to hand, `receive_midi({"type": "noteOn", "note": 60, "velocity": 0.8, "channel": 1})` hands your program a message just as a keyboard would.

## Your voice

The microphone is a synth whose sound comes in instead of being made. Ask for it, give it a voice, and listen:

```python
mic = use_microphone()            # the browser asks whether the page may use the microphone
mic.voice = "robot"               # robot, chipmunk, monster, cave, telephone, alien, whisper, or "none"
mic.listen()                      # now you hear yourself, as a robot. mic.mute() stops it
```

**Wear headphones when you listen.** Through loudspeakers the microphone hears itself, and the sound goes round and round until it howls. That is why nothing is heard until you say `listen()`. Recording does not need it.

| voice | |
|---|---|
| `robot` | a machine, ringing in a metal pipe |
| `chipmunk` | small and squeaky: seven semitones higher |
| `monster` | huge and deep: seven semitones lower, with a growl |
| `cave` | far inside a cave: long echoes in a very big room |
| `telephone` | down an old phone line |
| `alien` | not from here: higher, with a slow metallic sweep |
| `whisper` | hoarse and breathy, with no pitch at all |

`voice_names()` lists them. A voice is only a handful of settings, and you can turn them yourself once it is on. A microphone has every setting a synth has, and a few words of its own:

```python
mic = use_microphone()
mic.pitch = 7                     # semitones up or down, -12 to 12, without getting faster or slower
mic.echo = 0.4                    # and reverb, chorus, distortion, crush, cutoff, pan, volume, as on a synth
mic.ring = 1                      # multiply the voice by a wave: mic.ring_speed = 50 is how fast (the robot)
mic.comb = 0.5                    # ring like a pipe at one note: mic.comb_tone = 110. mic.flanger sweeps it
mic.gain = 2                      # turn a quiet microphone up
mic.gate = -40                    # quieter than this (in dB) counts as silence. It starts at -50; "off" for none
```

Choosing another voice first puts back what the last one changed, so pick the voice and then turn the dials. `use_microphone("robot", listen=True, echo=0.3)` does it in one line.

With [pydials](https://github.com/johnwylie70/pydials) the microphone is a synth too, and its controls act on it in the page, at once: `select("voice", mic, "voice")`, `dial("pitch", mic, "pitch")`, `toggle("listen", mic, "listening")`, `scope(mic)`, `meter(mic)`. The scope and the meter show your voice even while it is muted.

### Recording

```python
take = record_sound(3)                  # three seconds of the microphone, starting now
take.on_done(lambda: take.play())       # when it is over, play it back
```

`record_sound` gives you the recording at once and does not wait: your program carries on, and the take fills up behind it. A take is a sample, so everything a sample does it does, even while it is still recording:

```python
take = record_sound(3)
take.play()                       # as you said it
take.play("E4")                   # higher and faster: middle C is its own pitch
take.reverse = True               # backwards
take.loop = True                  # round and round while its note is held
take.voice = "monster"            # any voice, afterwards
take.done, take.seconds           # is it over, and how long it is
```

- What is recorded is **your plain voice**, whether or not you are listening. The take is then given the voice the microphone has, so it plays back the way the microphone sounds, and you can change your mind afterwards: `take.voice = "none"` is you, and `take.sound_like(mic)` is the microphone as it is set now.
- `start_recording()` records until `stop_recording()`. It stops by itself after 30 seconds; `start_recording(max=60)` gives it longer, up to 120.
- One recording is made at a time: starting another ends the one before, which keeps what it had.
- `record_sound(3, effects=True)` records the voice after its effects instead of before. That only works while you are listening.

**What is a frame late.** The page makes the recording, and tells Python about it with the next frame's message. So `take.done` and `take.seconds` change the frame *after* the recording ended, `take.on_done(...)` is called then, and `mic.state` and `mic.ready` are filled in a frame after the browser answered. Nothing in your program ever waits for any of them. In a scene that can wait (an `async def`), `await take.when_done()` and `await mic.when_ready()` look again each frame until it is so.

### Recording what you play

```python
tune = record_output(10)          # everything that is played for the next ten seconds, in stereo
play_notes("C4 E4 G4 C5", 0.25)
save_sound(tune, "my-tune.wav")   # saved as soon as it is over
```

`lead.record(4)` records one synth alone.

### Saving

`save_sound(take, "hello.wav")` makes a WAV file. Where it goes:

- **Run with `pyctures run`**, the file is written beside your program, a frame or two after the recording is over (the page hands Python the file).
- **In a web page** (`pyctures build`), the browser downloads it, or the app that shows the page keeps it with the scene's other files.
- `saved = save_sound(take, download=False)` saves nothing anywhere and hands Python the file's bytes: `saved.bytes`, once `saved.done`.

It gives back at once and does not wait: `saved.done`, `saved.path` (where Python wrote it) and `saved.on_done(...)`.

### With no microphone

A computer with no microphone, a person who says no, a page that is not allowed to ask: none of these stops your program. Every function still works, the browser's console says once why there is no microphone and what to do about it, and a recording is simply empty and done (`take.seconds` is 0). `mic.state` is `"asking"` until the page has said, then `"on"`, or why not: `"refused"`, `"none"`, `"busy"` or `"unavailable"`. `mic.ready` is `None` while it is asking, then `True` or `False`, and `mic.on_ready(fn)` calls your function with that. `stop_microphone()` lets the microphone go, and the browser's recording light goes out.

A page has to be served over `https` or from `localhost` to be given a microphone (`pyctures run` is), and a page inside a frame needs `allow="microphone"` on the frame.

### The voice effects on a synth

The pitch shifter, the ring modulator and the comb are not only for voices. Every synth has them, under names that do not clash with its own `pitch` and `ring`:

```python
lead.pitch_shift = 12             # an octave up, with the same length
lead.ring_mod = 0.6               # bell-like and strange: lead.ring_speed = 300
lead.comb = 0.5                   # a metal pipe: lead.comb_tone, lead.comb_feedback
lead.flanger = 0.6                # the comb, sweeping: lead.flanger_rate
lead.voice = "robot"              # or a whole voice at once
```

Eight synths can use the pitch shifter or the comb at once.

## Reading the sound back

For a scope, a meter or lit keys that your own program draws:

```python
lead.play("C4", 2)
wave = lead.samples()             # the wave it is making: about a thousand numbers from -1 to 1
loud = lead.level()               # how loud it is, [left, right], each from 0 to 1
held = lead.notes()               # the notes it is sounding, as numbers
```

`sound_output()` has the same three for everything that is sounding, the microphone has them for your voice, and a song has them a channel at a time: `song.channel(3).level()`. They are **a frame late**: Python cannot ask the page and be answered, so the first call asks the page to start saying, and from the next frame on each call gives what the page said with that frame. The very first call gives an empty list, zeros and no notes. The page stops saying a second and a half after your program stops asking. (With pydials, `scope(lead)` and `meter(lead)` are drawn by the page itself and are not late at all.)

## Volume, mute and stop

```python
set_volume(0.5)      # everything half as loud. 1 is normal
mute_sound()         # silence, and unmute_sound() to bring it back
stop_sound()         # stop everything that is sounding or waiting to sound
```

### If the sound clicks

```python
set_sound_buffer("large")        # "small" (1024 frames), "medium" (2048), "large" (4096), "auto", or a number of frames
now = sound_buffer()             # {"frames": 4096, "delay": 179, "thread": "page", "underruns": 0, "setting": 4096}
```

A page that is not served over https (a development build opened on a phone or an iPad by the computer's address) makes its sound on the page's own thread, a buffer at a time, and clicks when the page is busy for longer than a buffer lasts. A larger buffer rides over that and is heard later: `"large"` is about a fifth of a second from a key to its note, `"small"` a twentieth. `"auto"` lets the page choose, and double it once if it keeps clicking. It may be called before the first sound or at any time. `delay` is the milliseconds from a key to its note, `thread` is `"page"` there and `"audio"` on an https page, where there is nothing to fix and the same call sets how far ahead everything is scheduled instead; `underruns` counts the clicks. What `sound_buffer()` says is what the page last said, a frame late, and all zeros before it has. A number that is not a power of two from 256 to 16384 is taken as the nearest, with one message.

## Songs

A song is a whole piece of music in one file, played by the sound engine itself: a tracker's `.mod` or `.xm` file, or a song in synths' own format, which is text you can read and change.

```python
song = play_song("tune.mod")          # it goes round and round until it is stopped

song.pause()
song.resume()
song.volume = 0.5
song.seek(2)                          # jump to the third part of the song (and seek(2, 16): its row 16)
song.stop()
```

`play_song("tune.xm", repeat=False)` plays it once, and `volume=0.6` starts it quieter. One song plays at a time, and your own notes and game sounds play over it. `stop_song()` stops whichever song is playing.

A song is made of channels, counted from 0, and of patterns it plays in turn:

```python
song = play_song("tune.mod")
song.mute(2)                          # silence channel 2. song.mute(2, False) or song.unmute(2) brings it back
song.solo(0)                          # hear only the channels that are soloed. song.solo("all", False) hears the rest again
song.loop_pattern()                   # stay on the pattern that is playing. song.loop_pattern(False) carries on
```

**The mix.** Each channel has a place in the song's mix that can be moved while it plays, and the changes glide, so a fader can be dragged:

```python
song = play_song("tune.mod")
song.channel(0).volume = 0.6               # its fader, 0 to 2
song.channel(0).pan = -0.5                 # -1 is left, 1 is right
song.channel(0).reverb = 0.4               # how much of it goes to the reverb, 0 to 1
song.channel(0).echo = 0.3                 # and to the echo
song.loop([1, 0], [5, 0])                  # go round from the top of place 1 in the order to the top of place 5; song.loop(None) runs on
```

`volume` and `pan` reach a channel whatever plays on it. `reverb` and `echo` reach a channel's sampled instruments; a synth instrument has the sends of its own synth (`reverb` and `echo` in its patch). Each reads back what was last set here. The reverb and the echo are the ones every synth shares, so `set_effects(reverb_type="hall", reverb_level=0.8, echo_time=0.3, echo_level=0.7)` shapes them; `reverb_level` and `echo_level` are how loud each comes back, for everything sent to it.

`song.position` says where the song is, for drawing it: `{"state", "order", "pattern", "row", "tick", "speed", "tempo", "rounds", "rows", "orders"}`, where `state` is `"playing"`, `"paused"`, `"stopped"` or `"none"`. Like everything read back it is [a frame late](#reading-the-sound-back), and `"none"` the first time it is read. `song.replace(edited)` puts an edited song in the place of the one playing, for an editor: its bytes, its JSON as text, or the song as a dictionary. When the two have the same shape nothing stops, and the change is heard from the next row.

In a song of synths' own, an instrument can be a synth instead of a recording, called by a name. A name that is a ready-made synth's (`"bass"`, `"chip_kick"`) plays as that; any other name is told what it is:

```python
play_song("songs/night_drive.json", patches={"tune": "bell", "wobble": {"preset": "bass", "cutoff": 300, "wobble": 12}})
```

A `.mod` or `.xm` sounds as its tracker made it sound, rough edges included; `raw=False` smooths the samples and `raw=True` leaves any song rough. The format of synths' own songs is described in [synths-core](https://github.com/johnwylie70/synths-core/blob/main/docs/song-format.md).

## Mistakes

A mistake is said in plain words, with what was probably meant, on the line that made it:

```
play_sound("lazer"): there is no sound called "lazer". Did you mean "laser"? The sounds are: coin, jump, laser, …
make_synth(): there is no setting called "cutof". Did you mean "cutoff"?
"H4" is not a note. Write a note as a name like "C4", "F#3" or "Bb5", or as a number, where 60 is middle C
"robt" is not a voice. Did you mean "robot"? The voices are: robot, chipmunk, monster, cave, telephone, alien, whisper, and "none"
```

## How it works

No sound is worked out in Python. Each function writes a **command**, plain data such as `{"op": "note", "id": "s1", "note": [60], "len": 0.5, "t": 12.25}`, in the format of synths.js ([its docs/commands.md](https://github.com/johnwylie70/synths.js/blob/main/docs/commands.md) is the contract). Python chooses every id and nothing is ever answered, so no line of your program waits for the sound. A player (synths.js, in the page) owns the sound card and carries the commands out, with the engine on the browser's audio thread.

Every command carries the time it was asked for on Python's clock, and every batch the clock when it was sent. The page lines that clock up with its own, so the commands of a frame, sent together when the frame ends, are played with exactly the spacing they were called with, wherever Python is running.

A scene that is being recorded as a video is given one frame at a time, each exactly 1/fps after the last however long it took, and Pyctures says what time that is. The sound goes by that clock too: `sound_time()`, `beat()` and the time on every command are the video's own, so the sound in the video is in step with its pictures to the sample, and the program is not changed.

How the commands travel:

- **In a Pyctures scene** they ride the frame's own message. The first sound of a frame adds one command to the frame, a call of `send(batch)` on the page's sound object (Pyctures' fixed handle 10), and the rest of that frame's sounds join the batch. It is the same in a browser's own Python (`pyctures build`), in your Python (`pyctures run`), and with Python on another computer. Sound asked for at the top of the file, in `setup()` or in `on_key_down()` is inside the same call from the page, so it leaves with that call's reply.
- **A host of its own** calls `synths.connect(send)` and is handed each command at once, as `{"synths": 1, "now": …, "cmds": […]}`.
- **MIDI** goes the same way. Its functions write a `midi` command into the same batches ([docs/midi.md](https://github.com/johnwylie70/synths.js/blob/main/docs/midi.md) of synths.js is the contract); the page, where the devices are, plays a synth from a keyboard and turns a setting from a knob without Python in between; and what was received comes back as plain data. In a Pyctures scene the page hands it over with the next frame, each message with its own time moved onto Python's clock. A host of its own gives `synths.receive_midi(events)` what its player's `onMidi` gave.
- **The microphone, recording and saving** are `mic`, `record` and `save` commands in the same batches ([docs/microphone.md](https://github.com/johnwylie70/synths.js/blob/main/docs/microphone.md) of synths.js is the contract). The page opens the microphone, where the person is asked, and a dial tied to it acts on it there. What the player says back (the microphone is on or is not, a recording is over, a file is saved) and what is read back (a synth's wave, level and notes, a song's place) come as plain data with the next frame. A host of its own gives `synths.receive_sound_events(events)` what its player's `onSoundEvents` gave.
- **Plain Python** has no player: the program is started again with `pyctures run`, or says how to.

The names of every sound, synth and setting are those of synths.js, carried inside the module: `python scripts/sync_names.py` copies them from its `synths-names.json`, and a test fails while the two differ.

## Tests

```bash
pip install pytest
pytest
```

They need no browser and make no sound: they check the names against synths.js, every command against the command format, and what a mistake says. The tests of the microphone and the voices listen without one: where [node](https://nodejs.org) and synths.js are beside this repository, synths.js's offline player renders Python's commands with a tone in a microphone's place, and the pitch, the length of a recording and a saved WAV file are measured (they are skipped otherwise). The tests that listen (a scene heard under `pyctures run` and in a built page, with dials and a keyboard) are in Pyctures.

## Licence

MIT. See [LICENSE](LICENSE).
