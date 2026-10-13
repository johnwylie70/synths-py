import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# The JavaScript library, where the names and the command format are written, when it is beside this repository.
JS_REPO = ROOT.parent / "synths.js"

sys.path.insert(0, str(ROOT / "src"))


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
