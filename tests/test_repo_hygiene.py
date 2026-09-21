"""No screenshot of a live machine may be committed.

This exists because the fleet-wide data_boundary guard does not catch one.
Measured before it was written: `git add -f screen.jpg` followed by the guard
reported "clean, 22 tracked files carry no real-run shape". Its RUN-SHAPE
heuristic knows jsonl ledgers, dated files under output directories and
databases; a bare .jpg is not a shape it recognises, and this repo's only
real-run output is exactly that.

So .gitignore was the whole control, and .gitignore is advisory -- `git add -f`
walks straight through it. This check is the control that is not.

What is at stake: a screenshot here shows whatever was on a remote machine when
it was taken. A terminal mid-session, a browser someone left open, a credential
if echo was on. Those are the things the rest of this library goes out of its
way not to render.
"""

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}

#: Paths under these are someone else's repository, pinned as submodules.
SUBMODULES = ("guards/", "style/")


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                         cwd=str(REPO_ROOT))
    if out.returncode != 0:
        raise AssertionError("git ls-files failed: %s" % out.stderr.strip())
    return [line for line in out.stdout.splitlines() if line.strip()]


class NoCapturedScreensTests(unittest.TestCase):
    def test_the_file_list_is_not_empty(self):
        # A check fed nothing prints the same green as a check that found
        # nothing wrong. This one says which it is.
        self.assertGreater(len(tracked_files()), 5,
                           "git listed almost nothing; the check below would "
                           "have passed without examining anything")

    def test_no_image_is_tracked(self):
        offenders = [
            path for path in tracked_files()
            if Path(path).suffix.lower() in IMAGE_SUFFIXES
            and not path.startswith(SUBMODULES)
        ]
        self.assertEqual(
            offenders, [],
            "a captured screen is committed: %s. It shows whatever was on the "
            "remote machine. Remove it from the index, and if it has been "
            "pushed, rewrite the history rather than deleting the file in a "
            "later commit." % offenders,
        )

    def test_gitignore_still_covers_the_default_output_names(self):
        # Belt as well as braces: the examples write these names into the
        # working directory, and nobody should have to remember that.
        ignored = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("*.jpg", "*.png"):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, ignored)


if __name__ == "__main__":
    unittest.main()
