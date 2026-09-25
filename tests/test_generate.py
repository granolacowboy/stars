import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate", ROOT / "scripts" / "generate.py")
generate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(generate)


class GenerateViewsTests(unittest.TestCase):
    def test_build_repo_index_tracks_cross_list_membership_once(self):
        snapshots = [
            {
                "name": "Agents",
                "items": [{
                    "nameWithOwner": "acme/tool",
                    "url": "https://github.com/acme/tool",
                    "description": "x",
                    "stargazerCount": 10,
                    "isArchived": False,
                    "pushedAt": "2026-09-20T00:00:00Z",
                    "primaryLanguage": {"name": "Python"},
                }],
            },
            {
                "name": "Security",
                "items": [{
                    "nameWithOwner": "acme/tool",
                    "url": "https://github.com/acme/tool",
                    "description": "x",
                    "stargazerCount": 10,
                    "isArchived": False,
                    "pushedAt": "2026-09-20T00:00:00Z",
                    "primaryLanguage": {"name": "Python"},
                }],
            },
        ]
        index = generate.build_repo_index(snapshots)
        self.assertEqual(index["acme/tool"]["lists"], ["Agents", "Security"])

    def test_render_repo_view_escapes_markdown_pipes(self):
        text = generate.render_repo_view(
            "View",
            "Description",
            [{
                "nameWithOwner": "acme/tool",
                "url": "https://github.com/acme/tool",
                "description": "one | two",
                "stargazerCount": 10,
                "isArchived": True,
                "pushedAt": "2026-09-20T00:00:00Z",
                "primaryLanguage": {"name": "Python"},
                "lists": ["Agents"],
            }],
            "2026-09-25",
        )
        self.assertIn("one \\| two", text)
        self.assertIn("archived", text)

    def test_slug_is_stable(self):
        self.assertEqual(generate.slug("MCP Servers & Integrations"), "mcp-servers-integrations")


if __name__ == "__main__":
    unittest.main()
