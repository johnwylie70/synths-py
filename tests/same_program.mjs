// One program, as synths.js writes it: the commands, for tests/test_voice.py to set beside what Python writes.
import { pathToFileURL } from 'node:url'
const { createSound } = await import(pathToFileURL(process.argv[2]).href)
const batches = []
const s = createSound({ sound: { send: (b) => batches.push(b) }, clock: () => 0, batch: 'manual' })
const mic = s.useMicrophone()
mic.voice = 'robot'
mic.listen()
mic.pitch = 7
mic.gain = 2
mic.gate = -40
mic.set({ gate: 'off' })
mic.cutoff = 900
mic.voice = 'cave'
mic.echo = 0.4
const take = s.recordSound(3)
take.voice = 'monster'
take.reverse = true
take.loop = true
take.play('E4')
take.soundLike(mic)
mic.mute()
const open = s.startRecording({ max: 60 })
s.stopRecording()
open.stopRecording()
const lead = s.makeSynth('lead')
lead.voice = 'alien'
lead.pitchShift = 12
lead.ringMod = 0.6
lead.set({ comb: 0.5, voice: 'none' }, { glide: 2 })
const part = lead.record(4)
const tune = s.recordOutput(10)
s.saveSound(part, 'part')
s.saveSound(part, { download: false })
const song = s.playSong('tune.mod')
song.mute(2)
song.mute(2, false)
song.unmute()
song.solo(0)
song.solo('all', false)
song.loopPattern()
song.loop_pattern(false)
song.replace({ title: 'x' })
song.replace('{"title":"y"}')
lead.sample = part
lead.wave = 'saw'
const bare = s.makeSynth('bass')
bare.wave = 'sample'
const keys = s.makeSynth({ sample: 'piano.wav', note: 'C4', cutoff: 1800 })
keys.set({ sample: 'other.wav', wave: 'sample' })
const piano = s.loadSamples({ C2: 'piano-C2.wav', 'F#2': ['a.wav', 'b.wav'] }, { crossfade: 3, reverb: 0.3 })
piano.play('E2')
const kit = s.loadSamples(['kick_36.wav', 'snare-D2.wav'], { kit: true })
kit.play()
s.loadSamples([{ file: 'soft-C4.wav', note: 'C4', loud: [0, 0.5], tune: -5 }, { file: 'hard-C4.wav', note: 'C4', loud: [0.5, 1], oneShot: true, from: 'C3', to: 72 }], { release: 1, loop: true })
const pad = s.makeSynth('pad')
pad.setSamples({ C3: 'a.wav' }, { crossfade: { keys: 2, loud: 0.1 }, oneShot: true })
pad.samples = null
s.makeSynth('lead', { samples: { C3: 'a.wav' }, cutoff: 900 })
lead.arp('Cm7', 'whole', { step: 'sixteenth', octaves: 2, gate: 0.5 })
const held = lead.startArp('Am', { step: 0.5, order: 'up-down2', swing: 0.2, accent: [1, 0.5, 0, 0.5] })
held.change('F', { pattern: 'trance' })
held.gate = 0.3
held.speed = 30
held.step = 'eighth'
held.order = 'together'
lead.arp(['C4', 'E4', 'G4'], 1, { style: 'slide', pattern: "1 - 3 2 _ 1 3 5^" })
s.playArp('Cm7', { speed: 30, order: 'down' })
lead.play('A4', 1, { bend: 'scoop' })
lead.play('C5', 1, { glide: 'sixteenth' })
lead.play('E5', 2, { vibrato: true, glide: true })
lead.play('A3', 1, { bend: 'fall' })
lead.play('C4', 1, { slide: 12 })
lead.play('C4', 1, { bend: { to: 'E4', over: 'eighth' }, vibrato: { depth: 0.5, rate: 5, delay: 'quarter' } })
lead.play('C4', 1, { slide: { to: -3, over: 0.5 } })
const moved = lead.start('C4', { bend: 'dip' })
moved.vibrato()
moved.vibrato({ depth: 1 })
moved.vibrato(false)
s.playNote('A4', 1, { bend: { shape: 'scoop', to: -5 } })
lead.arpPattern = 'trance'
lead.arpPattern = [1, 0, 3, 2]
lead.arp('Cm7', { pattern: 'off' })
lead.arp('Cm7', { pattern: [1, null, "3^"] })
lead.arpPattern = 'off'
const gated = s.makeSynth('pad', { echo: 0.3 })
gated.tranceGate = 'x.x.xx.x'
gated.tranceGate = 'pump'
gated.tranceGate = [1, 0, 0.5, 0.25]
gated.set({ tranceGate: 'X. x.', cutoff: 900 })
gated.setTranceGate('x.x.xx.x', { rate: 'eighth', depth: 0.8, smooth: 0.02 })
gated.tranceGateSwing = 0.2
gated.tranceGate = null
s.setEffects({ reverbLevel: 0.8, echoLevel: 0.7 })
song.channel(0).volume = 0.6
song.channel(0).pan = -0.5
song.channel(3).reverb = 0.4
song.channel(3).echo = 0.3
song.loop([1, 0], [5, 0])
song.loop(2, [4])
song.loop(null)
s.stopMicrophone()
await new Promise((yes) => setTimeout(yes, 0))
s.flush()
process.stdout.write(JSON.stringify(batches.flatMap((b) => b.cmds)))
