#!/usr/bin/env bash
# Checks that a task's inputs filer ran with the filer's hardened defaults,
# from the Jobs of a namespace (`kubectl get jobs -o json`) on standard
# input; used by `.github/actions/install-chart` after
# `tests/smoke/deployment.sh`, whose task with an input starts the filer.
# Passes if there is at least one inputs filer Job and each of them has
# completed, with the security contexts that the taskmaster of tesk-core
# 0.12.0 gives the filer by default (the chart's `tesk.filer.*` contexts are
# empty by default): a non-root pod with the RuntimeDefault seccomp profile,
# and a container with a read-only root filesystem, without privilege
# escalation and with all capabilities dropped. Couples to the taskmaster's
# names: filer Jobs end in `-inputs-filer`, and the filer is their only
# container. Prints the filer Jobs found; needs jq.
set -euo pipefail

filers="$(jq -c '[.items[] | select(.metadata.name | endswith("-inputs-filer"))
    | {name: .metadata.name, succeeded: (.status.succeeded // 0),
       pod: .spec.template.spec.securityContext,
       container: .spec.template.spec.containers[0].securityContext}]')"
echo "Inputs filer jobs: ${filers}"
if ! jq -e 'length > 0 and all(.[];
    .succeeded >= 1
    and .pod.runAsNonRoot == true
    and .pod.seccompProfile.type == "RuntimeDefault"
    and .container.readOnlyRootFilesystem == true
    and .container.allowPrivilegeEscalation == false
    and ((.container.capabilities.drop // []) | index("ALL") != null))' \
    <<< "${filers}" > /dev/null; then
  echo "::error::No completed inputs filer job with the filer's hardened defaults"
  exit 1
fi
echo "ok: the inputs filer completed with the hardened defaults"
