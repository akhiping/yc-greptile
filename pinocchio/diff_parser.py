"""
Diff parser — converts git diff output into structured FileChange objects.

Uses the `unidiff` library.
Provides run_and_parse(repo_path) convenience function.
"""

import subprocess
from dataclasses import dataclass, field
from typing import List, Tuple

from unidiff import PatchSet


@dataclass
class FileChange:
    filepath: str
    added_lines: List[str] = field(default_factory=list)
    removed_lines: List[str] = field(default_factory=list)
    is_test_file: bool = False
    hunks: List[Tuple[int, int]] = field(default_factory=list)


def parse_diff(diff_text: str) -> List[FileChange]:
    """Parse a unified diff string into a list of FileChange objects."""
    patch = PatchSet(diff_text)
    changes = []
    for patched_file in patch:
        filepath = patched_file.path
        added = []
        removed = []
        hunk_ranges = []
        for hunk in patched_file:
            hunk_ranges.append((hunk.target_start, hunk.target_length))
            for line in hunk:
                if line.is_added:
                    added.append(line.value.rstrip("\n"))
                elif line.is_removed:
                    removed.append(line.value.rstrip("\n"))
        changes.append(FileChange(
            filepath=filepath,
            added_lines=added,
            removed_lines=removed,
            is_test_file="test" in filepath.lower(),
            hunks=hunk_ranges,
        ))
    return changes


def run_and_parse(repo_path: str) -> List[FileChange]:
    """Run git diff HEAD~1 in repo_path and return parsed FileChanges."""
    result = subprocess.run(
        ["git", "diff", "HEAD~1"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return parse_diff(result.stdout)


if __name__ == "__main__":
    from rich import print as rprint
    changes = run_and_parse("../demo-repo")
    for c in changes:
        rprint(f"[bold]{c.filepath}[/bold]  test={c.is_test_file}")
        rprint(f"  +{len(c.added_lines)} -{len(c.removed_lines)}  hunks={c.hunks}")
