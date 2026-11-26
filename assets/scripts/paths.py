"""Where one-shot-app keeps things.

The skill folder is shareable and holds no personal data. Everything about the person using
it (keys, identity, imprint, history, personal learnings) lives in their own data home:

    $ONE_SHOT_HOME  (default ~/.one-shot-app/)
      config.json      secrets + account keys          (chmod 600)
      profile.json     the library: identity, imprint, accounts, menu defaults, preferences, apps
      learnings.md     personal learnings from their runs

On first use the files are created from the examples in the skill folder. Older installs that
kept config.json / profile.json inside the skill folder are migrated automatically (the old
paths become symlinks, so scripts in apps built earlier keep working).
"""
from __future__ import annotations

import os
import pathlib
import shutil

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
HOME = pathlib.Path(os.environ.get("ONE_SHOT_HOME", "~/.one-shot-app")).expanduser()
CONFIG = HOME / "config.json"
PROFILE = HOME / "profile.json"
LEARNINGS = HOME / "learnings.md"
CONFIG_EXAMPLE = SKILL_DIR / "config.example.json"
PROFILE_EXAMPLE = SKILL_DIR / "profile.example.json"

LEARNINGS_SEED = """# Personal learnings

What one-shot-app learned from *your* runs: taste, accounts, past apps, things that broke.
The skill reads this before every run and appends to it at the end of each run.
"""


def ensure_home(create_files: bool = True) -> list[str]:
    """Create the data home, migrate legacy files, seed missing ones. Returns what it did."""
    did = []
    HOME.mkdir(parents=True, exist_ok=True)
    HOME.chmod(0o700)
    for name, example in (("config.json", CONFIG_EXAMPLE), ("profile.json", PROFILE_EXAMPLE)):
        legacy, target = SKILL_DIR / name, HOME / name
        if legacy.exists() and not legacy.is_symlink() and not target.exists():
            shutil.move(str(legacy), target)
            legacy.symlink_to(target)
            did.append(f"moved {name} from the skill folder to {HOME}")
        if create_files and not target.exists() and example.exists():
            shutil.copy(example, target)
            did.append(f"created {target} from the example")
        if target.exists():
            target.chmod(0o600)
    if create_files and not LEARNINGS.exists():
        LEARNINGS.write_text(LEARNINGS_SEED)
        LEARNINGS.chmod(0o600)
        did.append(f"created {LEARNINGS}")
    return did
