import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# The JavaScript library, where the names and the command format are written, when it is beside this repository.
JS_REPO = ROOT.parent / "synths.js"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def of_synths_js(name):
    """A file of synths.js as it was last committed, as text; None when synths.js is not beside this repository."""
    from sync_names import committed
    if not (JS_REPO / name).exists():
        return None
    return committed(JS_REPO, name).decode("utf-8")


@pytest.fixture
def sent():
    """Every command the library writes during a test, in order."""
    import synths
    class Sent(list):
        pass
    cmds = Sent()
    batches = []

    def send(batch):
        batches.append(batch)
        cmds.extend(batch["cmds"])
    synths.connect(send)
    cmds.batches = batches
    yield cmds
    synths.connect(None)


class Studio:
    """A Python program and a player with no sound card to play it (tests/studio.mjs: synths.js's offline player
    in node). The program's clock is where rendering has reached, and what the player says back is handed to
    the program after each stretch, as a page hands it over with a frame."""

    def __init__(self, microphone=None):
        import json, shutil, subprocess, tempfile
        import synths
        self.synths, self.json = synths, json
        # The copy of synths.js that the names here were taken from: as it was last committed.
        self.folder = tempfile.mkdtemp()
        from sync_names import committed
        for name in ("synths.js", "synths_core.wasm", "synths-midi.js"):
            (Path(self.folder) / name).write_bytes(committed(JS_REPO, name))
        self.node = subprocess.Popen([shutil.which("node"), str(ROOT / "tests" / "studio.mjs"), str(Path(self.folder) / "synths.js")],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.time, self.batches, self.said, self.events, self.all_cmds = 0.0, [], [], [], []
        synths.connect(self.batches.append)
        synths._sound().clock = lambda: self.time
        self.ask({"open": {"microphone": microphone, "start": 0}})

    def ask(self, what):
        self.node.stdin.write(self.json.dumps(what) + "\n")
        self.node.stdin.flush()
        line = self.node.stdout.readline()
        assert line, "the player stopped"
        return self.json.loads(line)

    def go(self, seconds, hz=None, read=None):
        """Send what the program has written, render so many seconds, and hand the program what the player said."""
        batches, self.batches[:] = list(self.batches), []
        self.all_cmds += [c for b in batches for c in b["cmds"]]
        ask = {"send": batches, "render": seconds, "hz": hz}
        if read is not None:
            ask["read"] = read
        out = self.ask(ask)
        self.time = out["time"]
        self.said += out["said"]
        self.events += out["events"]
        self.synths.receive_sound_events(out["events"])
        return out

    def close(self):
        import shutil
        self.synths.connect(None)
        self.node.stdin.close()
        self.node.wait(timeout=10)
        shutil.rmtree(self.folder, ignore_errors=True)


@pytest.fixture
def studio():
    """studio(microphone={"hz": 440, "seconds": 5}) is a Studio; none with no node or no synths.js beside this repository."""
    import shutil
    if not shutil.which("node") or not (JS_REPO / "synths.js").exists():
        pytest.skip("this test listens with synths.js in node, and one of the two is not here")
    made = []

    def make(microphone=None):
        made.append(Studio(microphone))
        return made[-1]
    yield make
    for s in made:
        s.close()
