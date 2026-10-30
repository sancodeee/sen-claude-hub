#!/usr/bin/env bash

# Configuration may contain credentials; never trace its expansion.
set +x
set -euo pipefail

wrapper_action="${1:-}"
case "$wrapper_action" in
  --help|-h|--check|-version)
    if [[ "$#" -ne 1 ]]; then
      echo "Local options do not accept extra arguments; use --help" >&2
      exit 2
    fi
    ;;
  --*)
    echo "Unknown local option; use --help" >&2
    exit 2
    ;;
esac

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'USAGE'
Usage: jenkins-cli [--check | -version | COMMAND [ARGS...]]
  --check   Check local Java, JAR and configuration without connecting.
  -version  Print the local Jenkins CLI JAR version without connecting.
  version   Query the Jenkins server version (requires a connection).
Configuration: JENKINS_URL, JENKINS_USER_ID, JENKINS_API_TOKEN.
Optional: JENKINS_CLI_JAR, JENKINS_CLI_MODE (-webSocket or -http), JAVA_BIN,
          JENKINS_CLI_ENV_FILE (default: ~/.local/share/jenkins/.jenkins-cli.env).
USAGE
  exit 0
fi

config_file="${JENKINS_CLI_ENV_FILE:-${HOME:?HOME must be set}/.local/share/jenkins/.jenkins-cli.env}"
saved_names=()
saved_values=()
for name in JENKINS_URL JENKINS_USER_ID JENKINS_API_TOKEN JENKINS_CLI_JAR JENKINS_CLI_MODE JAVA_BIN; do
  if declare -p "$name" >/dev/null 2>&1; then
    saved_names+=("$name")
    saved_values+=("${!name}")
  fi
done

if [[ -f "$config_file" && -r "$config_file" ]]; then
  # Only source a local shell configuration the user trusts.
  # Keep source outside a condition so errexit still stops non-final failures.
  # Suppress diagnostics that may quote credentials; report a fixed error on exit.
  # EXIT can run before source's redirections unwind, so preserve stderr separately.
  exec 9>&2
  trap 'echo "JENKINS_CLI_ENV_FILE could not be loaded; check syntax and assignments locally" >&9; exit 1' EXIT
  {
    # shellcheck disable=SC1090
    source "$config_file"
    set +x
    set -euo pipefail
    # Attributes such as integer/readonly/array can reinterpret or block overrides.
    for name in JENKINS_URL JENKINS_USER_ID JENKINS_API_TOKEN JENKINS_CLI_JAR JENKINS_CLI_MODE JAVA_BIN; do
      if declaration="$(declare -p "$name" 2>/dev/null)"; then
        attributes="${declaration#declare }"
        attributes="${attributes%% *}"
        case "$attributes" in
          --|-x) ;;
          *) exit 1 ;;
        esac
      fi
    done
    unset declaration attributes
    for ((index = 0; index < ${#saved_names[@]}; index++)); do
      printf -v "${saved_names[$index]}" '%s' "${saved_values[$index]}"
    done
  } >/dev/null 2>&1
  trap - EXIT
  exec 9>&-
elif [[ -n "${JENKINS_CLI_ENV_FILE:-}" || -e "$config_file" ]]; then
  echo "JENKINS_CLI_ENV_FILE not found or not readable" >&2
  exit 1
fi

# Avoid passing unused credential copies to the client when the caller exports all variables.
unset saved_names saved_values

jar_path="${JENKINS_CLI_JAR:-${HOME:?HOME must be set}/.local/share/jenkins/jenkins-cli.jar}"
java_bin="${JAVA_BIN:-java}"
if ! command -v "$java_bin" >/dev/null 2>&1 || ! "$java_bin" -version >/dev/null 2>&1; then
  echo "java not found or not usable; install a compatible Java runtime or set JAVA_BIN" >&2
  exit 1
fi
if [[ ! -f "$jar_path" || ! -r "$jar_path" ]]; then
  echo "jenkins-cli.jar not found or not readable; set JENKINS_CLI_JAR" >&2
  exit 1
fi

if [[ "$#" -eq 1 && "$1" == "-version" ]]; then
  exec "$java_bin" -jar "$jar_path" -version
fi

for name in JENKINS_URL JENKINS_USER_ID JENKINS_API_TOKEN; do
  if [[ -z "${!name:-}" ]]; then
    echo "$name is not set" >&2
    exit 1
  fi
done
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

mode="${JENKINS_CLI_MODE:--webSocket}"
if [[ "$mode" != "-webSocket" && "$mode" != "-http" ]]; then
  echo "JENKINS_CLI_MODE must be -webSocket or -http" >&2
  exit 1
fi
if [[ "$#" -eq 1 && "$1" == "--check" ]]; then
  echo "Local prerequisites are ready (server connectivity not checked)."
  exit 0
fi

# The official client accepts both variables, so the token stays out of argv.
export JENKINS_USER_ID JENKINS_API_TOKEN
exec env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  "$java_bin" -jar "$jar_path" -s "$JENKINS_URL" "$mode" "$@"
