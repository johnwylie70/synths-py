"""Copy the names from the JavaScript library, which is where they are written.

    python scripts/sync_names.py [path/to/synths.js]

Every sound, ready-made synth and setting has one name in both languages. They are written in
synths.js, which publishes them as ``synths-names.json``; this puts that file's contents into
``src/synths/__init__.py`` between the two NAMES lines, so the package is one file that needs
nothing beside it (it is loaded as one file where Python runs in a browser). Run it again
whenever synths.js changes. The tests fail while the two differ.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "src" / "synths" / "__init__.py"
BEGIN, END = "# NAMES:BEGIN", "# NAMES:END"


def one_line(value):
    return json.dumps(value, ensure_ascii=True, separators=(", ", ": "))


def written(names):
    """The names as Python source: JSON, a setting or a sound to a line, so a change reads well in a diff."""
    out = ["{"]
    keys = list(names)
    for key in keys:
        value = names[key]
        end = "" if key == keys[-1] else ","
        if isinstance(value, list):
            out.append(' %s: [' % json.dumps(key))
            out.extend("  %s%s" % (one_line(row), "" if i == len(value) - 1 else ",") for i, row in enumerate(value))
            out.append(" ]" + end)
        elif isinstance(value, dict) and key in ("synths", "sounds"):
            out.append(' %s: {' % json.dumps(key))
            inner = list(value)
            out.extend("  %s: %s%s" % (json.dumps(k), one_line(value[k]), "" if k == inner[-1] else ",") for k in inner)
            out.append(" }" + end)
        else:
            out.append(" %s: %s%s" % (json.dumps(key), one_line(value), end))
    out.append("}")
    text = "\n".join(out)
    assert json.loads(text) == names
    return text


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "synths.js"
    names = json.loads((source / "synths-names.json").read_text(encoding="utf-8"))
    module = MODULE.read_text(encoding="utf-8")
    head, rest = module.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    block = "%s\n_NAMES = json.loads(r'''\n%s\n''')\n%s" % (BEGIN, written(names), END)
    assert "'''" not in written(names)
    MODULE.write_text(head + block + tail, encoding="utf-8")
    print("wrote the names of synths.js %s into %s (%d settings, %d synths, %d sounds)"
          % (names.get("version"), MODULE.relative_to(ROOT), len(names["settings"]), len(names["synths"]), len(names["sounds"])))


if __name__ == "__main__":
    main()
