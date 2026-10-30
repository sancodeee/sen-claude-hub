from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "jenkins-cli.sh"
DOWNLOAD_SCRIPT = SCRIPT.with_name("download-client.sh")


class JenkinsCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="jenkins cli test ")
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.jar = self.root / "jenkins cli.jar"
        self.jar.touch()
        self.config = self.root / "config.env"
        self.config.touch(mode=0o600)
        self.capture = self.root / "invocation.json"
        self.java = self.root / "fake java"
        # Substitute only the external Java process; the real wrapper is exercised.
        self.java.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "if sys.argv[1:] == ['-version']:\n"
            "    sys.exit(int(os.environ.get('JAVA_PROBE_EXIT', '0')))\n"
            "Path(os.environ['JAVA_CAPTURE']).write_text(json.dumps({\n"
            "    'args': sys.argv[1:], 'stdin': sys.stdin.read(),\n"
            "    'user': os.environ.get('JENKINS_USER_ID'),\n"
            "    'token': os.environ.get('JENKINS_API_TOKEN'),\n"
            "    'proxies': {k: os.environ[k] for k in\n"
            "        ['ALL_PROXY', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY',\n"
            "         'http_proxy', 'https_proxy'] if k in os.environ}\n"
            "}))\n"
            "sys.exit(int(os.environ.get('JAVA_COMMAND_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.java.chmod(0o700)
        self.curl_capture = self.root / "curl-invocation.json"
        self.curl = self.root / "curl"
        self.curl.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "target = Path(os.environ['JENKINS_CLI_JAR'])\n"
            "Path(os.environ['CURL_CAPTURE']).write_text(json.dumps({\n"
            "    'target_before_download': target.read_text() if target.exists() else None\n"
            "}))\n"
            "Path(args[args.index('--output') + 1]).write_text('downloaded-jar')\n"
            "sys.exit(int(os.environ.get('CURL_COMMAND_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.curl.chmod(0o700)
        # Do not inherit the user's Jenkins configuration or credentials.
        self.env = {
            "PATH": os.defpath,
            "JENKINS_URL": "https://jenkins.example.invalid/",
            "JENKINS_USER_ID": "test-user",
            "JENKINS_API_TOKEN": "test-token-!$",
            "JENKINS_CLI_JAR": str(self.jar),
            "JENKINS_CLI_ENV_FILE": str(self.config),
            "JAVA_BIN": str(self.java),
            "JAVA_CAPTURE": str(self.capture),
            "CURL_CAPTURE": str(self.curl_capture),
        }

    def run_cli(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/bash", str(SCRIPT), *args],
            env=self.env,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )

    def test_help_does_not_require_dependencies_or_configuration(self) -> None:
        self.env = {"PATH": os.defpath}
        result = self.run_cli("--help")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--check", result.stdout)

    def test_local_options_reject_extra_arguments_without_forwarding(self) -> None:
        for option in ["--check", "-version", "--help", "-h"]:
            with self.subTest(option=option):
                result = self.run_cli(option, "--verbose")
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("Local options do not accept extra arguments", result.stderr)
                self.assertFalse(self.capture.exists())

    def test_unknown_local_options_fail_before_loading_configuration(self) -> None:
        self.env = {"PATH": os.defpath}
        for option in ["--version", "--unknown"]:
            with self.subTest(option=option):
                result = self.run_cli(option)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("Unknown local option", result.stderr)
                self.assertFalse(self.capture.exists())

    def test_config_load_failures_are_sanitized_and_stop_execution(self) -> None:
        marker = "11CONFIG_PRIVATE_TOKEN"
        cases = {
            "invalid-export": f"export JENKINS_API_TOKEN = {marker}\n",
            "invalid-syntax": f"JENKINS_API_TOKEN='{marker}'\n(\n",
            "non-final-failure": f"false\nJENKINS_API_TOKEN='{marker}'\n",
        }
        for label, content in cases.items():
            with self.subTest(case=label):
                self.config.write_text(content, encoding="utf-8")
                result = self.run_cli("--check")
                self.assertNotEqual(0, result.returncode)
                self.assertIn("JENKINS_CLI_ENV_FILE could not be loaded", result.stderr)
                self.assertNotIn(marker, result.stdout + result.stderr)
                self.assertFalse(self.capture.exists())

    def test_config_output_is_not_forwarded(self) -> None:
        marker = "11CONFIG_PRIVATE_TOKEN"
        self.config.write_text(f"printf '%s\\n' '{marker}'\n", encoding="utf-8")
        result = self.run_cli("--check")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn(marker, result.stdout + result.stderr)

    def test_config_cannot_leave_credential_tracing_enabled(self) -> None:
        marker = "11CONFIG_PRIVATE_TOKEN"
        self.config.write_text(f"set -x\nJENKINS_API_TOKEN='{marker}'\n", encoding="utf-8")
        result = self.run_cli("--check")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn(marker, result.stdout + result.stderr)
        self.assertNotIn("test-token-!$", result.stdout + result.stderr)

    def test_config_variable_attributes_cannot_change_caller_credentials(self) -> None:
        marker = "11CONFIG_PRIVATE_TOKEN"
        self.env["JENKINS_API_TOKEN"] = marker
        for declaration in [
            "declare -i JENKINS_API_TOKEN=1",
            "readonly JENKINS_API_TOKEN='config-token'",
            "declare -a JENKINS_API_TOKEN=('config-token')",
        ]:
            with self.subTest(declaration=declaration):
                self.config.write_text(declaration + "\n", encoding="utf-8")
                result = self.run_cli("--check")
                self.assertNotEqual(0, result.returncode)
                self.assertIn("JENKINS_CLI_ENV_FILE could not be loaded", result.stderr)
                self.assertNotIn(marker, result.stdout + result.stderr)
                self.assertFalse(self.capture.exists())

    def test_check_validates_local_prerequisites_without_connecting(self) -> None:
        result = self.run_cli("--check")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("server connectivity not checked", result.stdout)
        self.assertFalse(self.capture.exists())

    def test_preserves_arguments_stdin_and_credentials_without_auth_argument(self) -> None:
        args = ["build", "folder/job with spaces", "-p", "message=hello $world", "-f", "-v"]
        result = self.run_cli(*args, stdin="<project>input</project>\n")
        self.assertEqual(0, result.returncode, result.stderr)
        invocation = json.loads(self.capture.read_text())
        self.assertEqual(
            ["-jar", str(self.jar), "-s", "https://jenkins.example.invalid/", "-webSocket", *args],
            invocation["args"],
        )
        self.assertEqual("<project>input</project>\n", invocation["stdin"])
        self.assertEqual("test-user", invocation["user"])
        self.assertEqual("test-token-!$", invocation["token"])
        self.assertNotIn("test-token-!$", result.stdout + result.stderr)

    def test_loads_shared_configuration_and_keeps_explicit_overrides(self) -> None:
        self.config.write_text(
            "JENKINS_URL='https://config.example.invalid/'\n"
            "JENKINS_USER_ID='config-user'\n"
            "JENKINS_API_TOKEN='config-token'\n"
            "JENKINS_CLI_MODE='-http'\n"
            "JAVA_BIN='/missing/java'\n"
            "JENKINS_CLI_JAR='/missing/cli.jar'\n",
            encoding="utf-8",
        )
        del self.env["JENKINS_USER_ID"]
        del self.env["JENKINS_API_TOKEN"]
        result = self.run_cli("who-am-i")
        self.assertEqual(0, result.returncode, result.stderr)
        invocation = json.loads(self.capture.read_text())
        self.assertEqual("https://jenkins.example.invalid/", invocation["args"][3])
        self.assertEqual("-http", invocation["args"][4])
        self.assertEqual("config-user", invocation["user"])
        self.assertEqual("config-token", invocation["token"])

    def test_explicit_empty_credentials_do_not_fall_back_to_config(self) -> None:
        self.config.write_text("JENKINS_API_TOKEN='config-token'\n", encoding="utf-8")
        self.env["JENKINS_API_TOKEN"] = ""
        result = self.run_cli("version")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("JENKINS_API_TOKEN is not set", result.stderr)
        self.assertFalse(self.capture.exists())

    def test_missing_required_settings_fail_without_exposing_credentials(self) -> None:
        for name in ["JENKINS_URL", "JENKINS_USER_ID", "JENKINS_API_TOKEN"]:
            with self.subTest(name=name):
                original = self.env.pop(name)
                result = self.run_cli("version")
                self.env[name] = original
                self.assertNotEqual(0, result.returncode)
                self.assertIn(f"{name} is not set", result.stderr)
                self.assertNotIn("test-token-!$", result.stdout + result.stderr)
                self.assertFalse(self.capture.exists())

    def test_invalid_mode_fails_before_forwarding(self) -> None:
        self.env["JENKINS_CLI_MODE"] = "-ssh"
        result = self.run_cli("version")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("JENKINS_CLI_MODE must be -webSocket or -http", result.stderr)
        self.assertFalse(self.capture.exists())

    def test_invalid_or_credential_bearing_url_is_rejected(self) -> None:
        for url in [
            "file:///tmp/jenkins",
            "https://user:private-token@example.invalid/",
            "https://?bad",
            "https://#bad",
            "http://:8080/",
        ]:
            with self.subTest(url=url):
                self.env["JENKINS_URL"] = url
                result = self.run_cli("version")
                self.assertNotEqual(0, result.returncode)
                self.assertIn("JENKINS_URL", result.stderr)
                self.assertNotIn(url, result.stdout + result.stderr)
                self.assertFalse(self.capture.exists())

    def test_missing_jar_reports_dependency(self) -> None:
        self.jar.unlink()
        result = self.run_cli("--check")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("jenkins-cli.jar not found or not readable", result.stderr)

    def test_unusable_java_reports_dependency(self) -> None:
        self.env["JAVA_PROBE_EXIT"] = "1"
        result = self.run_cli("--check")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("java not found or not usable", result.stderr)

    def test_explicit_missing_config_file_reports_error(self) -> None:
        self.config.unlink()
        result = self.run_cli("--check")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("JENKINS_CLI_ENV_FILE", result.stderr)

    def test_client_version_does_not_require_server_configuration(self) -> None:
        for name in ["JENKINS_URL", "JENKINS_USER_ID", "JENKINS_API_TOKEN"]:
            del self.env[name]
        result = self.run_cli("-version")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["-jar", str(self.jar), "-version"], json.loads(self.capture.read_text())["args"])

    def test_clears_proxy_variables(self) -> None:
        self.env.update({name: "http://proxy.invalid:8080" for name in [
            "ALL_PROXY", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"
        ]})
        result = self.run_cli("version")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({}, json.loads(self.capture.read_text())["proxies"])

    def test_preserves_cli_exit_status(self) -> None:
        self.env["JAVA_COMMAND_EXIT"] = "23"
        result = self.run_cli("version")
        self.assertEqual(23, result.returncode, result.stderr)

    def run_downloader(self) -> subprocess.CompletedProcess[str]:
        env = dict(self.env, PATH=str(self.root) + os.pathsep + os.defpath)
        return subprocess.run(
            ["/bin/bash", str(DOWNLOAD_SCRIPT)],
            env=env,
            input="",
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )

    def test_download_replaces_jar_only_after_validation(self) -> None:
        self.jar.write_text("existing-jar", encoding="utf-8")
        result = self.run_downloader()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("downloaded-jar", self.jar.read_text())
        self.assertEqual("existing-jar", json.loads(self.curl_capture.read_text())["target_before_download"])
        validation_args = json.loads(self.capture.read_text())["args"]
        self.assertEqual("-version", validation_args[-1])
        self.assertNotEqual(str(self.jar), validation_args[1])
        self.assertEqual([], list(self.root.glob(".jenkins-cli.*")))

    def test_failed_download_keeps_existing_jar_and_removes_partial_file(self) -> None:
        self.jar.write_text("existing-jar", encoding="utf-8")
        self.env["CURL_COMMAND_EXIT"] = "18"
        result = self.run_downloader()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Jenkins CLI download failed", result.stderr)
        self.assertEqual("existing-jar", self.jar.read_text())
        self.assertEqual([], list(self.root.glob(".jenkins-cli.*")))
        self.assertFalse(self.capture.exists())

    def test_failed_download_does_not_leave_a_new_jar(self) -> None:
        self.jar.unlink()
        self.env["CURL_COMMAND_EXIT"] = "18"
        result = self.run_downloader()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Jenkins CLI download failed", result.stderr)
        self.assertFalse(self.jar.exists())
        self.assertEqual([], list(self.root.glob(".jenkins-cli.*")))

    def test_invalid_download_keeps_existing_jar_and_cleans_up(self) -> None:
        self.jar.write_text("existing-jar", encoding="utf-8")
        self.env["JAVA_COMMAND_EXIT"] = "1"
        result = self.run_downloader()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Downloaded Jenkins CLI JAR is not usable", result.stderr)
        self.assertEqual("existing-jar", self.jar.read_text())
        self.assertEqual([], list(self.root.glob(".jenkins-cli.*")))


if __name__ == "__main__":
    unittest.main()
