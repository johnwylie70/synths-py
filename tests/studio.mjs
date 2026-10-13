/**
 * A player with no sound card, for the Python tests: synths.js's offline player, told what to do a line at a
 * time. Python writes commands, this renders them with the real engine and says what came out and what the
 * player said back, so a test can listen to what a Python program would sound like, with sound given in a
 * microphone's place and no microphone ever opened.
 *
 *   node tests/studio.mjs path/to/synths.js
 *
 * Each line in is JSON: { open: { microphone: { hz, seconds, level } | null, start } } once, then any number of
 * { send: [batches], render: seconds, hz: [low, high] }. Each line out is JSON: for a render, { time, peak,
 * loudest (the loudest pitch between the two), events (what the player said, a file's bytes in base64), said
 * (what it wrote in the console) }.
 */
import { createInterface } from 'node:readline'
import { pathToFileURL } from 'node:url'

const synths = await import(pathToFileURL(process.argv[2]).href)
const SR = 48000
const said = []
for (const how of ['warn', 'info', 'error']) console[how] = (...a) => said.push(a.join(' '))

const peak = (a) => a.reduce((m, v) => Math.max(m, Math.abs(v)), 0)
function level(a, hz) {
  let re = 0, im = 0
  for (let i = 0; i < a.length; i++) {
    const w = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (a.length - 1))
    re += a[i] * w * Math.cos(2 * Math.PI * hz * i / SR)
    im += a[i] * w * Math.sin(2 * Math.PI * hz * i / SR)
  }
  return 4 * Math.hypot(re, im) / a.length
}
function loudest(a, low, high) {
  let best = low, most = 0
  for (let hz = low; hz <= high; hz += 2) { const l = level(a, hz); if (l > most) { most = l; best = hz } }
  for (let hz = best - 2; hz <= best + 2; hz += 0.2) { const l = level(a, hz); if (l > most) { most = l; best = hz } }
  return Math.round(best * 10) / 10
}

let player = null
let events = []
const plain = (e) => (e.bytes ? { ...e, bytes: Buffer.from(e.bytes).toString('base64') } : e)
for await (const line of createInterface({ input: process.stdin })) {
  if (!line.trim()) continue
  const ask = JSON.parse(line)
  let reply = {}
  if (ask.open) {
    const m = ask.open.microphone
    const microphone = m ? Float32Array.from({ length: Math.round(m.seconds * SR) }, (_, i) => (m.level ?? 0.5) * Math.sin(2 * Math.PI * m.hz * i / SR)) : undefined
    player = await synths.createOfflinePlayer({ sampleRate: SR, start: ask.open.start || 0, microphone })
    player.onSoundEvents((list) => events.push(...list.map(plain)), undefined)
    reply = { ok: true }
  } else {
    for (const batch of ask.send || []) player.send(batch)
    await new Promise((yes) => setTimeout(yes, 0))
    const out = ask.render ? (await player.render(ask.render)).left : new Float32Array(0)
    await new Promise((yes) => setTimeout(yes, 0))
    reply = { time: player.time, peak: peak(out), loudest: ask.hz && out.length ? loudest(out, ask.hz[0], ask.hz[1]) : null, events, said: said.splice(0) }
    events = []
    if (ask.read !== undefined) { const r = player.read(ask.read || undefined); reply.read = { samples: Array.from(r.samples), level: r.level, notes: r.notes }; reply.position = player.songPosition() }
  }
  process.stdout.write(JSON.stringify(reply) + '\n')
}
