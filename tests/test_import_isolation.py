"""@file test_import_isolation.py
@brief Verify pytest resolves ``usereq`` from the repository source tree.
@details Level 1 regression: pytest configuration -> sys.path insertion ->
conftest import. A stale foreign ``usereq`` distribution exported through
``PYTHONPATH`` must never shadow the repository package during test runs;
the failure mode is the conftest ``ModuleNotFoundError`` observed in the
pre-release ``unit-tests`` stage.
@satisfies SRS-479
"""

import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
COLLECT_TARGET = REPO_ROOT / "tests" / "test_doxygen_parser.py"


def test_pytest_imports_repository_package_despite_foreign_shadow(
    tmp_path: Path,
) -> None:
    """@brief Collect tests with a shadowing ``usereq`` on ``PYTHONPATH``.
    @details Arrange a foreign ``usereq`` package without ``source_analyzer``
    in a disposable directory; run pytest collection of one suite module in a
    subprocess with ``PYTHONPATH`` pointing only at the shadow; assert the
    repository conftest imports successfully. Complexity O(1) plus one
    subprocess collection; all writes stay under ``tmp_path``.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Completes when the subprocess exit status is asserted.
    @throws {AssertionError} When collection fails or reports a missing
    ``usereq.source_analyzer`` module.
    @satisfies SRS-479
    """
    # @brief Arrange a stale foreign package lacking the analyzed submodule.
    shadow_package = tmp_path / "usereq"
    shadow_package.mkdir()
    (shadow_package / "__init__.py").write_text(
        '"""Stale foreign usereq package without source_analyzer."""\n'
        '__version__ = "0.68.0"\n',
        encoding="utf-8",
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(tmp_path)
    environment.pop("PYTEST_ADDOPTS", None)

    # @brief Act through the pytest CLI in a clean subprocess environment.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only",
         str(COLLECT_TARGET)],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    # @brief Assert the repository package wins the import resolution.
    assert result.returncode == 0, result.stdout + result.stderr
    assert "No module named 'usereq.source_analyzer'" not in result.stderr
