#!/usr/bin/env python3
"""Deterministic structure checks; this does not claim agent behavior coverage."""

from collections import deque
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / "SKILL.md"
REFERENCES = ROOT / "references"
OPENAI_YAML_PATH = ROOT / "agents" / "openai.yaml"
LINK_PATTERN = re.compile(r"\]\(([^)#]+\.md)(?:#[^)]+)?\)")


def markdown_links(source: Path) -> list[Path]:
    content = source.read_text(encoding="utf-8")
    return [(source.parent / target).resolve() for target in LINK_PATTERN.findall(content)]


class SkillStructureTest(unittest.TestCase):
    def test_openai_interface_metadata_is_valid(self) -> None:
        self.assertTrue(OPENAI_YAML_PATH.is_file(), "missing agents/openai.yaml")
        metadata = yaml.safe_load(OPENAI_YAML_PATH.read_text(encoding="utf-8"))
        interface = metadata.get("interface", {})

        self.assertTrue(interface.get("display_name"))
        short_description = interface.get("short_description", "")
        self.assertGreaterEqual(len(short_description), 25)
        self.assertLessEqual(len(short_description), 64)
        self.assertIn("$product-copilot-rules", interface.get("default_prompt", ""))

    def test_entrypoint_stays_concise(self) -> None:
        line_count = len(SKILL_PATH.read_text(encoding="utf-8").splitlines())
        self.assertLessEqual(line_count, 250)

    def test_local_markdown_links_resolve(self) -> None:
        sources = (SKILL_PATH, *REFERENCES.glob("*.md"))
        for source in sources:
            for target in markdown_links(source):
                self.assertTrue(target.is_file(), f"broken link: {source} -> {target}")

    def test_every_reference_is_reachable_from_entrypoint(self) -> None:
        reachable: set[Path] = set()
        pending = deque([SKILL_PATH.resolve()])
        while pending:
            source = pending.popleft()
            for target in markdown_links(source):
                if target.parent == REFERENCES.resolve() and target not in reachable:
                    reachable.add(target)
                    pending.append(target)

        expected = {path.resolve() for path in REFERENCES.glob("*.md")}
        self.assertEqual(expected, reachable)


if __name__ == "__main__":
    unittest.main()
