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
