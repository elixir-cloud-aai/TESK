#!/usr/bin/env bash
# Checks of a deployed instance of TESK from outside, e.g., after an
# installation or upgrade: the service info, the access control (with
# `auth.mode: auth`), a small task that ends COMPLETE with the expected
# output in its logs, and a task that is cancelled while it runs and ends
# CANCELED. Run it from anywhere, with the base URL of the TES API as
# argument (e.g., `https://tes.example.org/ga4gh/tes/v1`); needs Bash, curl
# and jq. Prints one line per check, and stops with a non-zero exit code at
# the first check that fails. See "Checking a deployment" in
# `docs/deployment.md`. Environment:
#
# - `TOKEN`: an access token of a user who may run tasks, for instances
#   with `auth.mode: auth`. Then the script also checks that requests
#   without a token or with an invalid one are refused (401); without
#   `TOKEN`, these checks are skipped, and the tasks are sent without a
#   token (for instances with `auth.mode: noauth`)
# - `ALLOW_HTTP=true`: send `TOKEN` to a URL with `http` (e.g., through a
#   port forward); by default, the token is only sent over HTTPS
# - `TASK_TIMEOUT`: seconds to wait for each state of a task (default 600;
#   the first task on a node may wait for image pulls)
#
# The token is read from the environment only and goes to curl on its
# standard input, so that it doesn't show up in the process list. Each
# request has a limit of 60 seconds. The two tasks stay in the task list,
# as TES has no way to delete tasks (see "Deleting finished tasks" in
# `docs/deployment.md`); if the script stops early, it cancels the task
# that hasn't ended yet.
set -euo pipefail

api="${1:?usage: $0 <base URL of the TES API>}"
api="${api%/}"
token="${TOKEN:-}"
task_timeout="${TASK_TIMEOUT:-600}"
if [[ ! "${task_timeout}" =~ ^[1-9][0-9]*$ ]]; then
  echo "::error::TASK_TIMEOUT must be a positive number of seconds"
  exit 1
fi
if [[ -n "${token}" && "${api}" != https://* \
    && "${ALLOW_HTTP:-false}" != true ]]; then
  echo "::error::${api} isn't an HTTPS URL: set ALLOW_HTTP=true to send TOKEN to it"
  exit 1
fi
# The image of the tasks, pinned by digest (to update it, take the digest of
# the index of a newer tag, e.g., from `docker buildx imagetools inspect
# alpine:<tag>`)
image='alpine:3.22@sha256:2e0b81d60597f449baa56dc25d355367869d2dca4cd57e866f1e2b52af3eb55f'
final_states=(COMPLETE EXECUTOR_ERROR SYSTEM_ERROR CANCELED)
# Seconds that SYSTEM_ERROR must last to count as an end (see `await_state`)
system_error_grace=10
# The last response body and status
body="$(mktemp)"
status=""
# The identifier of the task that `create_task` created
task_id=""
# The task that hasn't ended yet, to cancel if the script stops early
running=""

cleanup() {
  if [[ -n "${running}" ]]; then
    echo "Cancelling task ${running}"
    request "${token}" POST "/tasks/${running}:cancel" || true
  fi
  rm -f "${body}"
}
trap cleanup EXIT

# Request a path with a token (none if empty) and an optional JSON body;
# sets `status` (000 if there was no response) and writes the response body
# to `${body}`
request() {
  local auth="$1" method="$2" path="$3" data="${4:-}"
  local args=(--silent --show-error --max-time 60 --output "${body}"
    --write-out '%{http_code}' -X "${method}"
    --header 'Accept: application/json')
  if [[ -n "${data}" ]]; then
    args+=(--header 'Content-Type: application/json' --data "${data}")
  fi
  : > "${body}"
  if [[ -n "${auth}" ]]; then
    # The token goes to curl on its standard input, not as an argument
    status="$(printf 'Authorization: Bearer %s\n' "${auth}" \
      | curl "${args[@]}" --header @- "${api}${path}")" || true
  else
    status="$(curl "${args[@]}" "${api}${path}" < /dev/null)" || true
  fi
  status="${status:-000}"
}

# Fail with a message and the last response body
fail() {
  echo "::error::$1"
  if [[ -s "${body}" ]]; then
    head -c 4000 "${body}"
    echo
  fi
  exit 1
}

# Check a request: its status and, if a jq filter is given, that the JSON
# response matches it; prints the description (if any) once it passed
check() {
  local description="$1" auth="$2" method="$3" path="$4" expected="$5"
  local filter="${6:-}" data="${7:-}"
  request "${auth}" "${method}" "${path}" "${data}"
  if [[ "${status}" != "${expected}" ]]; then
    fail "${method} ${path}: status ${status}, expected ${expected}"
  fi
  if [[ -n "${filter}" ]] && ! jq -e "${filter}" "${body}" > /dev/null 2>&1; then
    fail "${method} ${path}: the response doesn't match ${filter}"
  fi
  if [[ -n "${description}" ]]; then
    echo "ok: ${description}"
  fi
}

# Create a task with one executor that runs a command (JSON array); sets
# `task_id` and `running`
create_task() {
  local name="$1" command="$2" task
  task="$(jq -cn --arg name "${name}" --arg image "${image}" \
    --argjson command "${command}" \
    '{name: $name, executors: [{image: $image, command: $command}]}')"
  check "" "${token}" POST /tasks 200 '.id | type == "string" and length > 0' \
    "${task}"
  task_id="$(jq -r .id "${body}")"
  running="${task_id}"
  echo "ok: POST /tasks created task ${task_id}"
}

# Wait until a task has a state; fails if it ends in another one first.
# tesk-api reports SYSTEM_ERROR for a moment while Kubernetes updates the
# status of a task's jobs (e.g., right after the task was created, or when
# its taskmaster ends), so SYSTEM_ERROR only counts as an end once it has
# lasted `system_error_grace` seconds. Clears `running` once the task has
# ended
await_state() {
  local id="$1" wanted="$2" state="" final ended since=""
  local deadline=$((SECONDS + task_timeout))
  while ((SECONDS < deadline)); do
    check "" "${token}" GET "/tasks/${id}?view=MINIMAL" 200 '.state | type == "string"'
    state="$(jq -r .state "${body}")"
    ended=false
    for final in "${final_states[@]}"; do
      if [[ "${state}" == "${final}" ]]; then
        ended=true
      fi
    done
    if [[ "${state}" == SYSTEM_ERROR ]]; then
      since="${since:-${SECONDS}}"
      if ((SECONDS - since < system_error_grace)); then
        ended=false
      fi
    else
      since=""
    fi
    if [[ "${ended}" == true ]]; then
      running=""
    fi
    if [[ "${state}" == "${wanted}" ]]; then
      return
    fi
    if [[ "${ended}" == true ]]; then
      request "${token}" GET "/tasks/${id}?view=FULL"
      fail "task ${id} ended ${state}, expected ${wanted}"
    fi
    sleep 2
  done
  request "${token}" GET "/tasks/${id}?view=FULL"
  fail "task ${id} is ${state:-unknown} after ${task_timeout} s, expected ${wanted}"
}

echo "Checking the TES API at ${api}"

# The service info (with the token, in case it isn't public:
# `auth.serviceInfoPublic: false`)
check "GET /service-info answers with the service info of a TES" \
  "${token}" GET /service-info 200 \
  '(.id | type == "string" and length > 0) and .type.group == "org.ga4gh"
   and (.type.artifact | ascii_downcase) == "tes"'

# Access control: the task endpoints need a valid token
if [[ -n "${token}" ]]; then
  check "GET /tasks without a token is refused (401)" \
    "" GET '/tasks?view=MINIMAL' 401
  check "GET /tasks with an invalid token is refused (401)" \
    not-a-token GET '/tasks?view=MINIMAL' 401
  check "GET /tasks with TOKEN answers (200)" \
    "${token}" GET '/tasks?view=MINIMAL' 200 '.tasks | type == "array"'
else
  echo "skip: access control (TOKEN isn't set)"
  request "" GET '/tasks?view=MINIMAL'
  if [[ "${status}" == 401 || "${status}" == 403 ]]; then
    fail "GET /tasks: status ${status}: the instance needs a token; set TOKEN"
  fi
  check "GET /tasks without a token answers (200)" \
    "" GET '/tasks?view=MINIMAL' 200 '.tasks | type == "array"'
fi

# A task that completes, with its output in the executor's log
marker="tesk-deployment-check-$(date +%s)-${RANDOM}"
create_task "deployment check: complete" "[\"echo\", \"${marker}\"]"
id="${task_id}"
await_state "${id}" COMPLETE
echo "ok: task ${id} ended COMPLETE"
check "task ${id} has exit code 0 and the expected output in its logs" \
  "${token}" GET "/tasks/${id}?view=FULL" 200 \
  "(.logs[-1].logs[0].exit_code == 0)
   and (.logs[-1].logs[0].stdout | contains(\"${marker}\"))"

# A task that is cancelled while it runs
create_task "deployment check: cancel" '["sleep", "600"]'
id="${task_id}"
await_state "${id}" RUNNING
echo "ok: task ${id} is RUNNING"
check "POST /tasks/${id}:cancel answers (200)" \
  "${token}" POST "/tasks/${id}:cancel" 200
await_state "${id}" CANCELED
echo "ok: task ${id} ended CANCELED"

echo "Deployment checks passed"
