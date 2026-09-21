"""The packaging metadata must describe the code that is actually here.

Two copies of the same fact drift, and packaging metadata is the kind nobody
reads until an install produces something subtly wrong. `requirements.txt` is
what a reader of the README runs; `pyproject.toml` is what `pip install -e .`
uses. Nothing makes them agree except this.

These checks are written so they cannot pass by finding nothing: each one
asserts the list it parsed is non-empty before comparing it. A parser that
silently matched zero lines would otherwise print the same green as a genuine
agreement, which is the failure shape this repo keeps running into.
"""

import re
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def pyproject() -> dict:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def normalise(spec: str) -> str:
    """'requests >= 2.31' and 'requests>=2.31' are the same requirement."""
    return re.sub(r"\s+", "", spec).lower()


def requirements_txt() -> list[str]:
    lines = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return [normalise(line) for line in lines
            if line.strip() and not line.lstrip().startswith("#")]


class PackagingTests(unittest.TestCase):
    def test_dependencies_match_requirements_txt(self):
        declared = [normalise(dep) for dep in pyproject()["project"]["dependencies"]]
        pinned = requirements_txt()
        self.assertTrue(declared, "pyproject declares no dependencies to compare")
        self.assertTrue(pinned, "requirements.txt parsed as empty; nothing was compared")
        self.assertEqual(sorted(declared), sorted(pinned))

    def test_version_is_read_from_the_package(self):
        # The one number, not a second copy of it.
        project = pyproject()["project"]
        self.assertIn("version", project.get("dynamic", []))
        attr = pyproject()["tool"]["setuptools"]["dynamic"]["version"]["attr"]
        self.assertEqual(attr, "grokbot_cdp.__version__")

        import grokbot_cdp
        self.assertRegex(grokbot_cdp.__version__, r"^\d+\.\d+\.\d+")

    def test_the_package_is_the_one_that_ships(self):
        packages = pyproject()["tool"]["setuptools"]["packages"]
        self.assertEqual(packages, ["grokbot_cdp"])
        # Auto-discovery would have walked the submodules; make sure nobody
        # later "simplifies" this into shipping someone else's repository.
        for name in packages:
            self.assertTrue((REPO_ROOT / name / "__init__.py").is_file())

    def test_python_floor_covers_the_syntax_the_code_uses(self):
        # `X | None` in annotations under `from __future__ import annotations`
        # is fine much earlier, but tomllib (used above) is 3.11, and the CI
        # matrix starts there. Keep the claim and the matrix in step.
        self.assertEqual(pyproject()["project"]["requires-python"], ">=3.11")
        workflow = (REPO_ROOT / ".github" / "workflows" / "tests.yml").read_text(
            encoding="utf-8")
        self.assertIn("'3.11'", workflow)


if __name__ == "__main__":
    unittest.main()
