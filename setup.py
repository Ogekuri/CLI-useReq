"""@file setup.py
@brief Setuptools entry shim that excludes generated egg-info metadata from the sdist.
@details Project metadata and build configuration remain declared in pyproject.toml (PEP 621,
PEP 517, PEP 639). This module only overrides the sdist command: setuptools appends
`<egg_info>/SOURCES.txt` to the sdist file list unconditionally, so the override removes every
project-relative path containing a `*.egg-info` path component before the release tree is
populated. Complexity: O(F * P) over F file paths with P path components each.
"""

from setuptools import setup
from setuptools.command.sdist import sdist as _sdist


class SdistWithoutEggInfo(_sdist):
    """@brief Sdist command variant omitting generated egg-info paths from the release tree.
    @details Keeps every setuptools sdist behavior; only the candidate file list passed to
    `make_release_tree` is filtered. Side effects: none beyond the delegated sdist tree build.
    """

    def make_release_tree(self, base_dir, files) -> None:
        """@brief Populate the sdist release tree while excluding egg-info paths.
        @details Rejects every candidate whose path contains a component ending in `.egg-info`,
        then delegates population to setuptools with the retained list.
        @param base_dir {str} Absolute release-tree root directory created by the sdist command.
        @param files {list[str]} Project-relative candidate file paths.
        @return {None} Function return value.
        """
        retained = [
            entry
            for entry in files
            if not any(part.endswith(".egg-info") for part in entry.split("/"))
        ]
        super().make_release_tree(base_dir, retained)


setup(cmdclass={"sdist": SdistWithoutEggInfo})
