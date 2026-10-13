# synths

[![MIT licence](https://img.shields.io/badge/licence-MIT-green)](LICENSE)

synths is for making sounds and music in Python, and for enjoying it: game sounds in one line, notes and tunes, synths you shape yourself, arpeggios, recorded samples, effects and tracker songs. It is for any age and any level. You type a line and hear something. It is the sound sibling of [Pyctures](https://github.com/johnwylie70/pyctures), designed for projects made in [Circuitry Studio](https://www.circuitry.dev).

Prefer JavaScript? [synths.js](https://github.com/johnwylie70/synths.js) is the same library for JavaScript, with the same names. The sound engine itself is [synths-core](https://github.com/johnwylie70/synths-core).

## Install

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

There are fourteen ready-made game sounds: `coin`, `jump`, `laser`, `shoot`, `explosion`, `hit`, `powerup`, `blip`, `click`, `zap`, `bounce`, `pop`, `win` and `lose`. In a game it is one line where the thing happens:

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

## Tunes

```python
tune = play_notes("C4 E4 G4 - C5:2 G4+B4+D5 Am", 0.25, repeat=True)
tune.stop()
```

The notes are text with spaces between, or a list: `["C4", None, ["C4", "E4"]]`, where `None` is a rest and a list inside is a chord. In text a chord is joined with `+`, or named. The second thing is the seconds in a step; leave it out and a step is half a beat (see [When things start](#when-things-start)). More by name: `repeat` (`True`, or how many times), `volume`, `hold` (how much of its step a note sounds for, 0.9 unless you say), and `after`, `at` or `beat`.

Every synth has `play_notes` too: `make_synth("bass").play_notes("C2 C2 G2 C2", 0.25)`.

## Synths

```python
bass = make_synth("bass")                        # a ready-made synth
soft = make_synth("lead", cutoff=900)            # a ready-made one, changed
mine = make_synth(wave="square", attack=0.2)     # one from nothing
```

The ready-made synths: `keys` (what `play_note` uses), `bass`, `lead`, `pad`, `pluck`, `organ`, `strings`, `bell`, `flute`; the chip sounds `chip`, `chip_lead`, `chip_bass`, `chip_noise`, `chip_kick`, `chip_snare` and `chip_hat`; and the drums `kick`, `snare` and `hat`. All of them are settings of the same engine, not recordings, so every one can be changed. `synth_names()` lists them.

What a synth does:

| | |
|---|---|
| `lead.play("E4", 0.5)` | a note for half a second. A list of notes, or a chord's name, is a chord. No note at all plays the synth's own (a drum's). |
| `lead.play("E4", 0.5, 0.8)`, `lead.play("E4", length=1, volume=0.5, pan=-1, after=2)` | how loud, where, when |
| `note = lead.start("E4")` | a note that stays until `note.stop()`. While it sounds: `note.slide_to("G4", 0.5)`, `note.pitch = "A4"`, `note.volume = 0.5`, `note.pan = -1` |
| `lead.stop()`, `lead.stop("E4")` | let go of every note of the synth, or of one |
| `lead.play_notes("C4 E4 G4", 0.25)` | a tune on this synth |
| `lead.cutoff = 800` | change a setting; notes already sounding change too |
| `lead.set(cutoff=4000, resonance=0.4)`, `lead.set(cutoff=4000, slide=2)` | change several, or slide there over two seconds |
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
| `pitch_sweep`, `pitch_sweep_decay` | each note begins that many semitones off and falls into place: a drum's thump, a laser |
| `echo`, `reverb`, `chorus` | how much of the synth goes to each effect (0 to 1) |
| `distortion`, `crush` | grit (0 to 1), and the bits each sample keeps (16 is clean, 4 is an old games console) |

There are more: `setting_names()` lists every one, and each also answers to the engine's own name for it (`lead.filter_cutoff`).

## Arpeggios

An arpeggio plays the notes of a chord one after another, so fast that one voice sounds like a chord: the sound of a home computer's music.

```python
lead.arp("Cm7")                                   # half a second of it
lead.arp("C4", "minor", 2, speed=30, order="up-down")

chord = lead.start_arp("Am")                      # one that stays
chord.change("F")                                 # another chord, and the note carries on
chord.stop()

play_arp("Cm7")                                   # with no synth of your own: a chip sound
```

`speed` is steps a second (50 unless you say) and `order` is `"up"`, `"down"`, `"up-down"`, `"as written"` or `"random"`. A chord here has up to eight notes.

A **step macro** is the same idea for the sound itself: a short list of steps that every note of a synth plays through, each changing the wave, pitch, pulse width, cutoff or volume. It is what makes chip drums.

```python
drum = make_synth("chip", macro=[{"wave": "noise", "pitch": 24}, {"wave": "square"}, {"pitch": -5, "volume": 0.8}])
drum.macro_rate = 60          # steps a second
drum.macro = None             # take it away again
```

## Effects

A synth sends some of its sound to an effect with one word: `lead.echo = 0.4`, `lead.reverb = 0.3`, `lead.chorus = 0.5`. `distortion` and `crush` belong to the synth alone. The echo, the reverb and the chorus are shared by every synth, and are shaped with `set_effects`:

```python
set_effects(echo_time=0.3, echo_feedback=0.5, echo_bounce=True, reverb_size=0.8)
```

| | |
|---|---|
| `echo_time`, `echo_feedback`, `echo_tone`, `echo_bounce` | seconds between echoes, how much each feeds the next (0 to 0.95), how much treble survives, and whether they bounce left and right |
| `reverb_size`, `reverb_damping` | how big the room is, and how soon its treble dies |
| `chorus_rate`, `chorus_depth` | how fast and how far the chorus wobbles |

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

## When things start

Everything that makes a sound takes one of these:

```python
play_sound("coin", after=0.5)             # half a second from now
play_note("C4", 1, at=sound_time() + 2)   # at a time on the sound clock, which sound_time() reads
lead.play("E4", beats(1), beat=8)         # on beat 8
```

Beats are counted from `set_tempo(120)` (beats a minute; beat 0 is the moment you call it). `beats(2)` is how many seconds two beats last, and `beat()` is which beat it is now.

Sounds are placed on the exact sample they were asked for. That is why a tune you schedule with `after=` or `beat=`, or play with `play_notes`, stays in time even when your program is busy drawing. Everything is played a few hundredths of a second after it is asked for, so that this works; you will not notice it.

## Volume, mute and stop

```python
set_volume(0.5)      # everything half as loud. 1 is normal
mute_sound()         # silence, and unmute_sound() to bring it back
stop_sound()         # stop everything that is sounding or waiting to sound
```

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

`play_song("tune.xm", repeat=False)` plays it once, and `volume=0.6` starts it quieter. One song plays at a time, and your own notes and game sounds play over it.

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
```

## How it works

No sound is worked out in Python. Each function writes a **command**, plain data such as `{"op": "note", "id": "s1", "note": [60], "len": 0.5, "t": 12.25}`, in the format of synths.js ([its docs/commands.md](https://github.com/johnwylie70/synths.js/blob/main/docs/commands.md) is the contract). Python chooses every id and nothing is ever answered, so no line of your program waits for the sound. A player (synths.js, in the page) owns the sound card and carries the commands out, with the engine on the browser's audio thread.

Every command carries the time it was asked for on Python's clock, and every batch the clock when it was sent. The page lines that clock up with its own, so the commands of a frame, sent together when the frame ends, are played with exactly the spacing they were called with, wherever Python is running.

How the commands travel:

- **In a Pyctures scene** they ride the frame's own message. The first sound of a frame adds one command to the frame, a call of `send(batch)` on the page's sound object (Pyctures' fixed handle 10), and the rest of that frame's sounds join the batch. It is the same in a browser's own Python (`pyctures build`), in your Python (`pyctures run`), and with Python on another computer. Sound asked for at the top of the file, in `setup()` or in `on_key_down()` is inside the same call from the page, so it leaves with that call's reply.
- **A host of its own** calls `synths.connect(send)` and is handed each command at once, as `{"synths": 1, "now": …, "cmds": […]}`.
- **Plain Python** has no player: the program is started again with `pyctures run`, or says how to.

The names of every sound, synth and setting are those of synths.js, carried inside the module: `python scripts/sync_names.py` copies them from its `synths-names.json`, and a test fails while the two differ.

## Tests

```bash
pip install pytest
pytest
```

They need no browser and make no sound: they check the names against synths.js, every command against the command format, and what a mistake says. The tests that listen (a scene heard under `pyctures run` and in a built page, with dials and a keyboard) are in Pyctures.

## Licence

MIT. See [LICENSE](LICENSE).
