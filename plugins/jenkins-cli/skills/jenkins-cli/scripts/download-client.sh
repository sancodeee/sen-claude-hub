#!/usr/bin/env bash

set +x
set -euo pipefail

if [[ "$#" -ne 0 ]]; then
  echo "Usage: set JENKINS_URL, optional JENKINS_CLI_JAR and JAVA_BIN, then run without arguments" >&2
  exit 2
fi
if [[ -z "${JENKINS_URL:-}" ]]; then
  echo "JENKINS_URL is not set" >&2
  exit 1
fi
case "$JENKINS_URL" in
  http://?*|https://?*) ;;
  *) echo "JENKINS_URL must be an HTTP or HTTPS URL" >&2; exit 1 ;;
esac
server_authority="${JENKINS_URL#*://}"
server_authority="${server_authority%%[/?#]*}"
if [[ -z "$server_authority" || "$server_authority" == :* || "$server_authority" == *'@'* || "$JENKINS_URL" == *[[:space:]]* ]]; then
  echo "JENKINS_URL must have a host and must not contain credentials or whitespace" >&2
  exit 1
fi

java_bin="${JAVA_BIN:-java}"
if ! command -v curl >/dev/null 2>&1 || ! command -v "$java_bin" >/dev/null 2>&1 || ! "$java_bin" -version >/dev/null 2>&1; then
  echo "curl and a usable Java runtime are required" >&2
  exit 1
fi
jar_path="${JENKINS_CLI_JAR:-${HOME:?HOME must be set}/.local/share/jenkins/jenkins-cli.jar}"
if [[ -d "$jar_path" ]]; then
  echo "JENKINS_CLI_JAR must be a file path" >&2
  exit 1
fi
jar_directory="$(dirname -- "$jar_path")"
mkdir -p -- "$jar_directory"
temporary_jar="$(mktemp "$jar_directory/.jenkins-cli.XXXXXX")"
trap 'rm -f -- "$temporary_jar"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

if ! curl --fail --location --silent --show-error \
  --output "$temporary_jar" "${JENKINS_URL%/}/jnlpJars/jenkins-cli.jar"; then
  echo "Jenkins CLI download failed; destination was not replaced" >&2
  exit 1
fi
if ! "$java_bin" -jar "$temporary_jar" -version >/dev/null 2>&1; then
  echo "Downloaded Jenkins CLI JAR is not usable; destination was not replaced" >&2
  exit 1
fi
chmod 644 "$temporary_jar"
# The temporary file shares the destination directory, so replacement is atomic.
mv -f -- "$temporary_jar" "$jar_path"
echo "Jenkins CLI JAR installed successfully."
