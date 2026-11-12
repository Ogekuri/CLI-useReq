"""Unit tests for online update-check dispatch in CLI command flows."""

import io
import http.client
import json
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from usereq import cli


class TestOnlineUpdateCheck(unittest.TestCase):
    """Verifies that command execution triggers online update checks."""

    def test_files_references_triggers_online_update_check(self) -> None:
        """Analysis subcommand files-references must invoke release-check once."""
        fixture = Path(__file__).resolve().parent / "fixtures" / "fixture_python.py"
        repo_base = Path(__file__).resolve().parents[1]

        with patch("usereq.cli.maybe_notify_newer_version", autospec=True) as notify_mock:
            with patch("sys.stdout"):
                exit_code = cli.main(
                    [
                        "files-references",
                        "--prj-base",
                        str(repo_base),
                        "--git-base",
                        str(repo_base),
                        str(fixture),
                    ]
                )

        self.assertEqual(exit_code, 0)
        notify_mock.assert_called_once_with(timeout_seconds=2.0)

    def test_version_triggers_online_update_check(self) -> None:
        """Version-only command must still execute startup release-check."""
        with patch("usereq.cli.maybe_notify_newer_version", autospec=True) as notify_mock:
            with patch("usereq.cli.fetch_github_latest_version", return_value=None):
                with patch("sys.stdout"):
                    exit_code = cli.main(["--version"])

        self.assertEqual(exit_code, 0)
        notify_mock.assert_called_once_with(timeout_seconds=2.0)

    def test_update_check_runs_before_argument_parsing(self) -> None:
        """Release-check must run before parse_args is executed."""
        with patch("usereq.cli.maybe_notify_newer_version", autospec=True) as notify_mock:
            with patch("usereq.cli.parse_args", side_effect=RuntimeError("parse failure")):
                with patch("sys.stdout"), patch("sys.stderr"):
                    exit_code = cli.main(["--files-references", "missing.py"])

        self.assertEqual(exit_code, 1)
        notify_mock.assert_called_once_with(timeout_seconds=2.0)

    def test_version_forces_online_check_even_with_active_idle_state(self) -> None:
        """Version-only command must force online release-check despite idle-state gating."""
        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            now_timestamp = 1700000000
            idle_state = {
                "last_success_timestamp": now_timestamp - 10,
                "last_success_human_readable_timestamp": "2023-11-14T22:13:10Z",
                "idle_until_timestamp": now_timestamp + 3600,
                "idle_until_human_readable_timestamp": "2023-11-15T00:13:20Z",
            }
            idle_path.write_text(json.dumps(idle_state), encoding="utf-8")
            response_mock = MagicMock()
            response_mock.read.return_value = json.dumps({"info": {"version": "0.0.1"}}).encode(
                "utf-8"
            )
            urlopen_cm = MagicMock()
            urlopen_cm.__enter__.return_value = response_mock
            urlopen_cm.__exit__.return_value = None

            with patch("usereq.cli.time.time", return_value=now_timestamp):
                with patch(
                    "usereq.cli.get_release_check_idle_file_path",
                    return_value=idle_path,
                ):
                    with patch(
                        "usereq.cli.urllib.request.urlopen",
                        return_value=urlopen_cm,
                    ) as urlopen_mock:
                        with patch("sys.stdout"):
                            exit_code = cli.main(["--version"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(urlopen_mock.call_count, 2)
        first_request = urlopen_mock.call_args_list[0].args[0]
        self.assertEqual(
            first_request.full_url,
            "https://pypi.org/pypi/cli-usereq/json",
        )

    def test_release_api_url_is_hardcoded(self) -> None:
        """Release-check URL must resolve to the hardcoded PyPI JSON API endpoint."""
        resolved_url = cli.resolve_pypi_latest_version_url()
        self.assertEqual(
            resolved_url,
            "https://pypi.org/pypi/cli-usereq/json",
        )

    def test_newer_version_warning_is_bright_green(self) -> None:
        """Remote-newer detection must print a bright-green availability payload."""
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps({"info": {"version": "9.9.9"}}).encode("utf-8")
        urlopen_cm = MagicMock()
        urlopen_cm.__enter__.return_value = response_mock
        urlopen_cm.__exit__.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=1700000000):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.resolve_pypi_latest_version_url",
                            return_value=(
                                "https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest"
                            ),
                        ):
                            with patch(
                                "usereq.cli.urllib.request.urlopen",
                                return_value=urlopen_cm,
                            ):
                                with patch("sys.stderr") as fake_stderr:
                                    cli.maybe_notify_newer_version(timeout_seconds=2.0)

        written = "".join(call.args[0] for call in fake_stderr.write.call_args_list)
        self.assertIn(cli.ANSI_BRIGHT_GREEN, written)
        self.assertIn("installed 0.0.1, latest 9.9.9.", written)
        self.assertIn(cli.ANSI_RESET, written)

    def test_release_check_http_403_rate_limit_sets_extended_idle_delay(self) -> None:
        """403 API rate-limit failures must print diagnostics and persist one-day idle delay."""
        now_timestamp = 1700000000
        http_error = urllib.error.HTTPError(
            url="https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest",
            code=403,
            msg="Forbidden",
            hdrs=http.client.HTTPMessage(),
            fp=io.BytesIO(b'{"message":"API rate limit exceeded"}'),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=now_timestamp):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.resolve_pypi_latest_version_url",
                            return_value=(
                                "https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest"
                            ),
                        ):
                            with patch(
                                "usereq.cli.urllib.request.urlopen",
                                side_effect=http_error,
                            ):
                                with patch("sys.stderr") as fake_stderr:
                                    cli.maybe_notify_newer_version(timeout_seconds=2.0)
            payload = json.loads(idle_path.read_text(encoding="utf-8"))

        written = "".join(call.args[0] for call in fake_stderr.write.call_args_list)
        self.assertIn(cli.ANSI_BRIGHT_RED, written)
        self.assertIn("HTTP 403", written)
        self.assertIn("API rate limit exceeded", written)
        self.assertIn(cli.ANSI_RESET, written)
        self.assertEqual(
            payload["idle_until_timestamp"],
            now_timestamp + cli.RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
        )

    def test_release_check_network_failure_sets_extended_idle_delay(self) -> None:
        """Network failures must persist one-day idle delay and rewrite the idle-state file."""
        now_timestamp = 1700000000
        network_error = urllib.error.URLError("offline")

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=now_timestamp):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.resolve_pypi_latest_version_url",
                            return_value=(
                                "https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest"
                            ),
                        ):
                            with patch(
                                "usereq.cli.urllib.request.urlopen",
                                side_effect=network_error,
                            ):
                                with patch("sys.stderr") as fake_stderr:
                                    cli.maybe_notify_newer_version(timeout_seconds=2.0)
            payload = json.loads(idle_path.read_text(encoding="utf-8"))

        written = "".join(call.args[0] for call in fake_stderr.write.call_args_list)
        self.assertIn("network failure (offline)", written)
        self.assertEqual(
            payload["idle_until_timestamp"],
            now_timestamp + cli.RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
        )

    def test_release_check_uses_hardcoded_url(self) -> None:
        """Release-check request must target the hardcoded GitHub endpoint URL."""
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps({"info": {"version": "0.0.1"}}).encode("utf-8")
        urlopen_cm = MagicMock()
        urlopen_cm.__enter__.return_value = response_mock
        urlopen_cm.__exit__.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=1700000000):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.urllib.request.urlopen",
                            return_value=urlopen_cm,
                        ) as urlopen_mock:
                            cli.maybe_notify_newer_version(timeout_seconds=2.0)

        urlopen_call = urlopen_mock.call_args
        request_object = urlopen_call.args[0]
        self.assertEqual(
            request_object.full_url,
            "https://pypi.org/pypi/cli-usereq/json",
        )

    def test_release_check_skips_network_when_idle_window_active(self) -> None:
        """Active idle-until state must skip remote HTTP calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            now_timestamp = 1700000000
            idle_state = {
                "last_success_timestamp": now_timestamp - 10,
                "last_success_human_readable_timestamp": "2023-11-14T22:13:10Z",
                "idle_until_timestamp": now_timestamp + 3600,
                "idle_until_human_readable_timestamp": "2023-11-15T00:13:20Z",
            }
            idle_path.write_text(json.dumps(idle_state), encoding="utf-8")

            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=now_timestamp):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch("usereq.cli.urllib.request.urlopen") as urlopen_mock:
                            cli.maybe_notify_newer_version(timeout_seconds=2.0)

        urlopen_mock.assert_not_called()

    def test_release_check_idle_delay_default_is_3600_seconds(self) -> None:
        """Default release-check idle-delay constant must match one hour."""
        self.assertEqual(cli.RELEASE_CHECK_IDLE_DELAY_SECONDS, 3600)

    def test_release_check_rate_limit_idle_delay_is_86400_seconds(self) -> None:
        """Rate-limited release-check idle-delay constant must match one day."""
        self.assertEqual(cli.RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS, 86400)

    def test_release_check_idle_file_path_uses_home_cache_directory(self) -> None:
        """Idle-state path must be anchored under ~/.cache/usereq."""
        fake_home = Path("/tmp/fake-home")
        with patch("usereq.cli.Path.home", return_value=fake_home):
            resolved_path = cli.get_release_check_idle_file_path()
        self.assertEqual(
            resolved_path,
            fake_home / ".cache" / "usereq" / "check_version_idle-time.json",
        )

    def test_write_release_check_idle_state_creates_parent_directories(self) -> None:
        """Idle-state writer must create missing parent cache directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = (
                Path(temp_dir)
                / ".cache"
                / "usereq"
                / "check_version_idle-time.json"
            )
            cli.write_release_check_idle_state(
                file_path=idle_path,
                now_timestamp=1700000000,
            )
            self.assertTrue(idle_path.exists())

    def test_release_check_executes_when_idle_until_expired(self) -> None:
        """Expired idle-until timestamp must allow a new remote release-check."""
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps({"info": {"version": "0.0.1"}}).encode("utf-8")
        urlopen_cm = MagicMock()
        urlopen_cm.__enter__.return_value = response_mock
        urlopen_cm.__exit__.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            now_timestamp = 1700000000
            idle_state = {
                "last_success_timestamp": now_timestamp - 30,
                "last_success_human_readable_timestamp": "2023-11-14T22:13:10Z",
                "idle_until_timestamp": now_timestamp - 1,
                "idle_until_human_readable_timestamp": "2023-11-14T22:13:19Z",
            }
            idle_path.write_text(json.dumps(idle_state), encoding="utf-8")

            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=now_timestamp):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.urllib.request.urlopen",
                            return_value=urlopen_cm,
                        ) as urlopen_mock:
                            cli.maybe_notify_newer_version(timeout_seconds=2.0)

        urlopen_mock.assert_called_once()

    def test_successful_release_check_writes_idle_state_file(self) -> None:
        """Successful release check must persist timestamps and human-readable fields."""
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps({"info": {"version": "0.0.1"}}).encode("utf-8")
        urlopen_cm = MagicMock()
        urlopen_cm.__enter__.return_value = response_mock
        urlopen_cm.__exit__.return_value = None
        now_timestamp = 1700000000

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=now_timestamp):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.resolve_pypi_latest_version_url",
                            return_value=(
                                "https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest"
                            ),
                        ):
                            with patch(
                                "usereq.cli.urllib.request.urlopen",
                                return_value=urlopen_cm,
                            ):
                                cli.maybe_notify_newer_version(timeout_seconds=2.0)

            payload = json.loads(idle_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["last_success_timestamp"], now_timestamp)
        self.assertEqual(
            payload["last_success_human_readable_timestamp"],
            cli.format_unix_timestamp_utc(now_timestamp),
        )
        self.assertEqual(
            payload["idle_until_timestamp"],
            now_timestamp + cli.RELEASE_CHECK_IDLE_DELAY_SECONDS,
        )
        self.assertEqual(
            payload["idle_until_human_readable_timestamp"],
            cli.format_unix_timestamp_utc(
                now_timestamp + cli.RELEASE_CHECK_IDLE_DELAY_SECONDS
            ),
        )

    def test_release_check_invalid_payload_sets_default_idle_delay(self) -> None:
        """Non-API release payload failures must rewrite idle-state using the default delay."""
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps({"missing": "tag"}).encode("utf-8")
        urlopen_cm = MagicMock()
        urlopen_cm.__enter__.return_value = response_mock
        urlopen_cm.__exit__.return_value = None
        now_timestamp = 1700000000

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=now_timestamp):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.resolve_pypi_latest_version_url",
                            return_value=(
                                "https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest"
                            ),
                        ):
                            with patch(
                                "usereq.cli.urllib.request.urlopen",
                                return_value=urlopen_cm,
                            ):
                                with patch("sys.stderr") as fake_stderr:
                                    cli.maybe_notify_newer_version(timeout_seconds=2.0)
            payload = json.loads(idle_path.read_text(encoding="utf-8"))

        written = "".join(call.args[0] for call in fake_stderr.write.call_args_list)
        self.assertIn("invalid response payload (missing 'info.version')", written)
        self.assertEqual(
            payload["idle_until_timestamp"],
            now_timestamp + cli.RELEASE_CHECK_IDLE_DELAY_SECONDS,
        )

    def test_release_check_http_429_sets_extended_idle_delay_when_retry_after_is_higher(
        self,
    ) -> None:
        """HTTP 429 handling must ignore shorter policy differences and persist one-day backoff."""
        now_timestamp = 1700000000
        hdrs_429 = http.client.HTTPMessage()
        hdrs_429["Retry-After"] = "900"
        http_error = urllib.error.HTTPError(
            url="https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest",
            code=429,
            msg="Too Many Requests",
            hdrs=hdrs_429,
            fp=io.BytesIO(b'{"message":"rate limit exceeded"}'),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=now_timestamp):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.resolve_pypi_latest_version_url",
                            return_value=(
                                "https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest"
                            ),
                        ):
                            with patch(
                                "usereq.cli.urllib.request.urlopen",
                                side_effect=http_error,
                            ):
                                cli.maybe_notify_newer_version(timeout_seconds=2.0)

            payload = json.loads(idle_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["last_success_timestamp"], now_timestamp)
        self.assertEqual(
            payload["idle_until_timestamp"],
            now_timestamp + cli.RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
        )

    def test_release_check_http_429_sets_extended_idle_delay_when_retry_after_is_lower(
        self,
    ) -> None:
        """HTTP 429 handling must persist one-day backoff even with short Retry-After values."""
        now_timestamp = 1700000000
        hdrs_429_short = http.client.HTTPMessage()
        hdrs_429_short["Retry-After"] = "60"
        http_error = urllib.error.HTTPError(
            url="https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest",
            code=429,
            msg="Too Many Requests",
            hdrs=hdrs_429_short,
            fp=io.BytesIO(b'{"message":"rate limit exceeded"}'),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            with patch("usereq.cli.load_package_version", return_value="0.0.1"):
                with patch("usereq.cli.time.time", return_value=now_timestamp):
                    with patch(
                        "usereq.cli.get_release_check_idle_file_path",
                        return_value=idle_path,
                    ):
                        with patch(
                            "usereq.cli.resolve_pypi_latest_version_url",
                            return_value=(
                                "https://api.github.com/repos/ExampleOrg/ExampleRepo/releases/latest"
                            ),
                        ):
                            with patch(
                                "usereq.cli.urllib.request.urlopen",
                                side_effect=http_error,
                            ):
                                cli.maybe_notify_newer_version(timeout_seconds=2.0)

            payload = json.loads(idle_path.read_text(encoding="utf-8"))

        self.assertEqual(
            payload["idle_until_timestamp"],
            now_timestamp + cli.RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
        )

    def test_failed_idle_state_recalculates_idle_until_from_now(self) -> None:
        """Failure idle-state writer must recompute idle-until from current time."""
        now_timestamp = 1700000000
        idle_state = {
            "last_success_timestamp": now_timestamp - 7200,
            "last_success_human_readable_timestamp": "2023-11-14T20:13:20Z",
            "idle_until_timestamp": now_timestamp + 172800,
            "idle_until_human_readable_timestamp": "2023-11-16T22:13:20Z",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            idle_path = Path(temp_dir) / "idle.json"
            cli.write_failed_release_check_idle_state(
                file_path=idle_path,
                now_timestamp=now_timestamp,
                idle_state=idle_state,
                idle_delay_seconds=cli.RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
            )
            payload = json.loads(idle_path.read_text(encoding="utf-8"))

        self.assertEqual(
            payload["last_success_timestamp"],
            idle_state["last_success_timestamp"],
        )
        self.assertEqual(
            payload["idle_until_timestamp"],
            now_timestamp + cli.RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
        )

    def test_upgrade_command_requests_latest_pypi_version(self) -> None:
        """Default --upgrade must request the latest PyPI version (SRS-343).

        UUT: run_upgrade. Level 1: depends only on mocked subprocess.run.
        `uv tool install <pkg>` keeps the already-installed version when the tool
        environment exists, so the command must carry --upgrade to upgrade the tool.
        """
        # Arrange
        result_mock = MagicMock(returncode=0)

        # Act
        with patch("usereq.cli.subprocess.run", return_value=result_mock) as run_mock:
            cli.run_upgrade()

        # Assert
        command = run_mock.call_args.args[0]
        self.assertIn("--upgrade", command)

    def test_upgrade_command_installs_from_pypi_by_default(self) -> None:
        """Default upgrade command must run the standard install without forcing (SRS-343)."""
        result_mock = MagicMock(returncode=0)

        with patch("usereq.cli.subprocess.run", return_value=result_mock) as run_mock:
            cli.run_upgrade()

        run_mock.assert_called_once_with(
            [
                "uv",
                "tool",
                "install",
                cli.TOOL_PROGRAM_NAME,
                "--upgrade",
            ],
            check=False,
        )

    def test_upgrade_command_without_force_has_no_forcing_options(self) -> None:
        """Standard --upgrade must run the plain install/update process (SRS-343, SRS-508).

        Without --force no uv forcing option (--force, --reinstall, --refresh)
        may appear in the executed command.
        """
        # Arrange
        result_mock = MagicMock(returncode=0)

        # Act
        with patch("usereq.cli.subprocess.run", return_value=result_mock) as run_mock:
            cli.run_upgrade()

        # Assert
        command = run_mock.call_args.args[0]
        self.assertNotIn("--force", command)
        self.assertNotIn("--reinstall", command)
        self.assertNotIn("--refresh", command)

    def test_upgrade_command_with_force_reinstalls_completely(self) -> None:
        """--upgrade --force must force download and full reinstallation (SRS-509)."""
        # Arrange
        result_mock = MagicMock(returncode=0)

        # Act
        with patch("usereq.cli.subprocess.run", return_value=result_mock) as run_mock:
            cli.run_upgrade(force=True)

        # Assert
        run_mock.assert_called_once_with(
            [
                "uv",
                "tool",
                "install",
                cli.TOOL_PROGRAM_NAME,
                "--force",
                "--reinstall",
                "--refresh",
            ],
            check=False,
        )

    def test_fetch_github_latest_version_raw_tag_preserves_v_prefix(self) -> None:
        """raw_tag=True must return tag_name without stripping the v prefix (SRS-451)."""
        # Arrange
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps({"tag_name": " v9.9.9 "}).encode("utf-8")
        urlopen_cm = MagicMock()
        urlopen_cm.__enter__.return_value = response_mock
        urlopen_cm.__exit__.return_value = None

        # Act
        with patch("usereq.cli.load_package_version", return_value="0.0.1"):
            with patch("usereq.cli.urllib.request.urlopen", return_value=urlopen_cm):
                raw_tag = cli.fetch_github_latest_version(raw_tag=True)
                normalized_tag = cli.fetch_github_latest_version(raw_tag=False)

        # Assert
        self.assertEqual(raw_tag, "v9.9.9")
        self.assertEqual(normalized_tag, "9.9.9")

    def test_upgrade_command_with_github_installs_latest_release_tag(self) -> None:
        """--upgrade --develop must pin the raw latest GitHub release tag (SRS-440, SRS-451, SRS-452)."""
        # Arrange
        result_mock = MagicMock(returncode=0)

        # Act
        with (
            patch("usereq.cli.fetch_github_latest_version", return_value="v9.9.9") as fetch_mock,
            patch("usereq.cli.subprocess.run", return_value=result_mock) as run_mock,
        ):
            cli.run_upgrade(use_github=True)

        # Assert
        fetch_mock.assert_called_once_with(raw_tag=True)
        run_mock.assert_called_once_with(
            [
                "uv",
                "tool",
                "install",
                cli.TOOL_PROGRAM_NAME,
                "--from",
                "git+https://github.com/Ogekuri/CLI-useReq.git@v9.9.9",
            ],
            check=False,
        )

    def test_upgrade_command_with_github_and_force_reinstalls_completely(self) -> None:
        """--upgrade --develop --force must force reinstall of the GitHub tag (SRS-510)."""
        # Arrange
        result_mock = MagicMock(returncode=0)

        # Act
        with (
            patch("usereq.cli.fetch_github_latest_version", return_value="v9.9.9"),
            patch("usereq.cli.subprocess.run", return_value=result_mock) as run_mock,
        ):
            cli.run_upgrade(use_github=True, force=True)

        # Assert
        run_mock.assert_called_once_with(
            [
                "uv",
                "tool",
                "install",
                cli.TOOL_PROGRAM_NAME,
                "--force",
                "--reinstall",
                "--refresh",
                "--from",
                "git+https://github.com/Ogekuri/CLI-useReq.git@v9.9.9",
            ],
            check=False,
        )

    def test_upgrade_accepts_force_argument(self) -> None:
        """--upgrade must accept the auxiliary --force argument (SRS-508)."""
        # Arrange / Act
        args = cli.parse_args(["--upgrade", "--force"])

        # Assert
        self.assertTrue(args.upgrade)
        self.assertTrue(args.force)

    def test_upgrade_help_documents_force_argument(self) -> None:
        """Inline help must document --force as an auxiliary --upgrade argument (SRS-511)."""
        # Arrange
        parser = cli.build_parser()

        # Act
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit):
                parser.parse_args(["--help"])

        # Assert
        help_text = mock_stdout.getvalue()
        self.assertIn("--force", help_text)
        self.assertIn("--reinstall", help_text)

    def test_main_upgrade_force_dispatches_forced_upgrade(self) -> None:
        """main must dispatch --upgrade --force with force=True (SRS-508, SRS-509)."""
        # Arrange / Act
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("usereq.cli.run_upgrade") as upgrade_mock,
            patch("usereq.cli._maybe_auto_install_after_upgrade", autospec=True),
            patch("sys.stdout"),
        ):
            exit_code = cli.main(["--upgrade", "--force"])

        # Assert
        self.assertEqual(exit_code, 0)
        upgrade_mock.assert_called_once_with(use_github=False, force=True)

    def test_main_upgrade_develop_force_dispatches_forced_github_upgrade(self) -> None:
        """main must dispatch --upgrade --develop --force with both flags (SRS-510)."""
        # Arrange / Act
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("usereq.cli.run_upgrade") as upgrade_mock,
            patch("usereq.cli._maybe_auto_install_after_upgrade", autospec=True),
            patch("sys.stdout"),
        ):
            exit_code = cli.main(["--upgrade", "--develop", "--force"])

        # Assert
        self.assertEqual(exit_code, 0)
        upgrade_mock.assert_called_once_with(use_github=True, force=True)

    def test_upgrade_command_with_github_fails_when_tag_unfetchable(self) -> None:
        """GitHub tag-resolution failure must raise ReqError code 1 without executing uv (SRS-453)."""
        # Arrange
        # Act
        with (
            patch(
                "usereq.cli.fetch_github_latest_version",
                side_effect=urllib.error.URLError("offline"),
            ),
            patch("usereq.cli.subprocess.run") as run_mock,
            self.assertRaises(cli.ReqError) as context,
        ):
            cli.run_upgrade(use_github=True)

        # Assert
        self.assertEqual(context.exception.code, 1)
        self.assertIn(
            "unable to resolve the latest GitHub release tag",
            context.exception.message,
        )
        run_mock.assert_not_called()

    def test_upgrade_command_with_github_fails_when_tag_missing(self) -> None:
        """Empty GitHub tag payload must raise ReqError code 1 without executing uv (SRS-453)."""
        # Arrange
        # Act
        with (
            patch("usereq.cli.fetch_github_latest_version", return_value=None),
            patch("usereq.cli.subprocess.run") as run_mock,
            self.assertRaises(cli.ReqError) as context,
        ):
            cli.run_upgrade(use_github=True)

        # Assert
        self.assertEqual(context.exception.code, 1)
        run_mock.assert_not_called()

    def test_upgrade_command_fails_on_nonzero_exit(self) -> None:
        """Upgrade command must raise ReqError when uv exits with non-zero status."""
        result_mock = MagicMock(returncode=7)
        with patch("usereq.cli.subprocess.run", return_value=result_mock):
            with self.assertRaises(cli.ReqError) as context:
                cli.run_upgrade()
        self.assertIn("auto-upgrade failed", context.exception.message)
        self.assertEqual(context.exception.code, 7)

    def test_uninstall_command_uses_tool_program_name(self) -> None:
        """Uninstall command must target configured tool program name."""
        result_mock = MagicMock(returncode=0)
        with patch("usereq.cli.subprocess.run", return_value=result_mock) as run_mock:
            cli.run_uninstall()

        run_mock.assert_called_once_with(
            [
                "uv",
                "tool",
                "uninstall",
                cli.TOOL_PROGRAM_NAME,
            ],
            check=False,
        )


class TestVersionOutput(unittest.TestCase):
    """SRS-441/SRS-442: --ver/--version three-line output with PyPI and GitHub latest."""

    @staticmethod
    def _urlopen_response(payload: dict) -> MagicMock:
        """Build a urlopen context-manager mock returning one JSON payload."""
        response_mock = MagicMock()
        response_mock.read.return_value = json.dumps(payload).encode("utf-8")
        cm = MagicMock()
        cm.__enter__.return_value = response_mock
        cm.__exit__.return_value = None
        return cm

    def test_version_output_prints_installed_pypi_and_github_latest(self) -> None:
        """--ver must print installed, PyPI latest, and GitHub latest lines (SRS-441)."""
        pypi_cm = self._urlopen_response({"info": {"version": "2.3.4"}})
        github_cm = self._urlopen_response({"tag_name": "v3.4.5"})

        def fake_urlopen(request, timeout=None):
            if "pypi.org" in request.full_url:
                return pypi_cm
            return github_cm

        with patch("usereq.cli.load_package_version", return_value="1.2.3"):
            with patch(
                "usereq.cli.urllib.request.urlopen", side_effect=fake_urlopen
            ):
                with patch("sys.stdout", new_callable=io.StringIO) as fake_stdout:
                    printed = cli.maybe_print_version(["--ver"])

        self.assertTrue(printed)
        output_lines = fake_stdout.getvalue().strip().splitlines()
        self.assertEqual(
            output_lines,
            [
                "Current Installed : 1.2.3",
                "Latest @ PyPI     : 2.3.4",
                "Latest @ GitHub   : 3.4.5",
            ],
        )

    def test_version_output_prints_unknown_on_fetch_failure(self) -> None:
        """Unfetchable latest versions must degrade to the unknown label (SRS-442)."""
        with patch("usereq.cli.load_package_version", return_value="1.2.3"):
            with patch(
                "usereq.cli.urllib.request.urlopen",
                side_effect=urllib.error.URLError("offline"),
            ):
                with patch("sys.stdout", new_callable=io.StringIO) as fake_stdout:
                    with patch("sys.stderr"):
                        printed = cli.maybe_print_version(["--version"])

        self.assertTrue(printed)
        output_lines = fake_stdout.getvalue().strip().splitlines()
        self.assertEqual(
            output_lines,
            [
                "Current Installed : 1.2.3",
                "Latest @ PyPI     : unknown",
                "Latest @ GitHub   : unknown",
            ],
        )

    def test_version_output_reuses_startup_pypi_latest_without_refetch(self) -> None:
        """PyPI latest from the startup check must be reused without a second PyPI request."""
        github_cm = self._urlopen_response({"tag_name": "v3.4.5"})

        with patch("usereq.cli.load_package_version", return_value="1.2.3"):
            with patch(
                "usereq.cli.urllib.request.urlopen", return_value=github_cm
            ) as urlopen_mock:
                with patch("sys.stdout", new_callable=io.StringIO) as fake_stdout:
                    printed = cli.maybe_print_version(
                        ["--ver"], pypi_latest="2.3.4"
                    )

        self.assertTrue(printed)
        output_lines = fake_stdout.getvalue().strip().splitlines()
        self.assertEqual(
            output_lines,
            [
                "Current Installed : 1.2.3",
                "Latest @ PyPI     : 2.3.4",
                "Latest @ GitHub   : 3.4.5",
            ],
        )
        urlopen_mock.assert_called_once()
        self.assertIn(
            "api.github.com",
            urlopen_mock.call_args.args[0].full_url,
        )
