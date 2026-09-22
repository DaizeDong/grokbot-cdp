"""The documents must agree with the code and with each other.

Three kinds of drift live here, and all three are invisible until someone is
misled by them.

The version appears in one literal and three pieces of prose. The literal is
`grokbot_cdp.__version__`; `pyproject.toml` derives from it and a test in
test_packaging.py pins that derivation. The prose copies, in the README badge,
the ROADMAP heading and the newest released CHANGELOG entry, have nothing
holding them except this file.

The two READMEs are meant to be the same document in two languages. Nothing
makes a section added to one appear in the other.

And a pointer to a file that does not exist is worse than no pointer, because
a reader assumes the answer is somewhere and stops looking.

Every check asserts it found something before it compares, so a regex that
silently matched nothing cannot print the same green as real agreement.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8")


def declared_version() -> str:
    source = read("grokbot_cdp/__init__.py")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', source, re.M)
    assert match, "no __version__ literal in grokbot_cdp/__init__.py"
    return match.group(1)


def headings(text: str) -> list[str]:
    return re.findall(r"^## (.+)$", text, re.M)


def local_links(text: str) -> list[str]:
    """Markdown links that point at a path in this repository."""
    out = []
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        out.append(target.split("#", 1)[0])
    return [t for t in out if t]


class VersionAgreementTest(unittest.TestCase):
    def test_the_readme_badge_matches_the_code(self):
        for name in ("README.md", "README_CN.md"):
            with self.subTest(name):
                found = re.findall(r"Roadmap-v([0-9][^-]*?)-purple", read(name))
                self.assertEqual(len(found), 1, f"{name}: expected one Roadmap badge")
                self.assertEqual(found[0], declared_version())

    def test_the_roadmap_heading_matches_the_code(self):
        found = re.findall(r"^Current:\s*\*\*v([^*]+)\*\*", read("ROADMAP.md"), re.M)
        self.assertEqual(len(found), 1, "expected one 'Current: **vX.Y.Z**' line")
        self.assertEqual(found[0], declared_version())

    def test_the_newest_released_changelog_entry_matches_the_code(self):
        # Unreleased is skipped on purpose: it is the entry that exists before a
        # version does, so requiring it to carry one would forbid the normal state.
        released = re.findall(r"^## \[([0-9][^\]]*)\]", read("CHANGELOG.md"), re.M)
        self.assertTrue(released, "CHANGELOG.md has no released version entry")
        self.assertEqual(released[0], declared_version())


class BilingualTest(unittest.TestCase):
    def test_both_readmes_have_the_same_number_of_sections(self):
        en, cn = headings(read("README.md")), headings(read("README_CN.md"))
        self.assertGreaterEqual(len(en), 5, "README.md parsed as almost no sections")
        self.assertEqual(
            len(en), len(cn),
            "the two READMEs are meant to be the same document in two languages;\n"
            f"  README.md    : {en}\n  README_CN.md : {cn}",
        )

    def test_the_shared_section_names_line_up(self):
        # Only the headings that are not translated can be compared by name. They
        # are the anchor: if the running order diverges, these stop matching.
        en, cn = headings(read("README.md")), headings(read("README_CN.md"))
        shared = [(i, h) for i, h in enumerate(en) if h.startswith("Roadmap ")]
        self.assertTrue(shared, "expected at least one untranslated heading")
        for index, name in shared:
            self.assertTrue(
                cn[index].startswith("Roadmap "),
                f"position {index} is {name!r} in English and {cn[index]!r} in Chinese",
            )


class PointersResolveTest(unittest.TestCase):
    def test_every_local_link_in_the_docs_exists(self):
        docs = ["README.md", "README_CN.md", "CONTRIBUTING.md"]
        docs += [str(p.relative_to(REPO_ROOT)).replace("\\", "/")
                 for p in sorted((REPO_ROOT / "reference").glob("*.md"))]
        checked = 0
        missing = []
        for doc in docs:
            for target in local_links(read(doc)):
                checked += 1
                if not (REPO_ROOT / target).exists():
                    missing.append(f"{doc} -> {target}")
        self.assertGreater(checked, 10, "found almost no links; the parser is broken")
        self.assertEqual(missing, [], "\n".join(missing))

    def test_the_reference_index_covers_every_shard(self):
        # A shard nobody points at is a shard nobody reads.
        shards = {p.name for p in (REPO_ROOT / "reference").glob("*.md")}
        self.assertTrue(shards, "reference/ is empty")
        readme = read("README.md")
        unlisted = sorted(s for s in shards if f"reference/{s}" not in readme)
        self.assertEqual(unlisted, [], f"not linked from README.md: {unlisted}")


if __name__ == "__main__":
    unittest.main()
