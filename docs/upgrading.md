# Upgrading

Changes that affect existing deployments, newest first. Upgrade a release
with the same values files as before, adapted as described here, unless a
section says otherwise (releases of charts before [Resource names from the
release name](#resource-names-from-the-release-name) must be installed
again):

```bash
helm upgrade tesk charts/tesk --namespace tesk -f my-values.yaml -f secrets.yaml
```

## Unreleased

### Audiences per client of tokenClients

**Breaking, with `auth.tokenClients` only.** Each client of
`auth.tokenClients` now has audiences of its own, and its tokens are
accepted only for one of them, so that one client's tokens for another
client's audience are refused (see [Tokens of
services](deployment.md#tokens-of-services);
[#336](https://github.com/elixir-cloud-aai/TESK/issues/336)).
`auth.tokenClients.clients` is a map from client ID to the client's
settings, and the shared `auth.tokenClients.audience` and
`auth.tokenClients.allowAnyAudience` are removed. Convert the values of
chart 0.4.0 as follows:

```yaml
# Chart 0.4.0
auth:
  tokenClients:
    audience: https://tesk.example.org
    clients: [my-gateway, my-smoke-tests]
---
# Now
auth:
  tokenClients:
    clients:
      my-gateway:
        audiences: [https://tesk.example.org]
      my-smoke-tests:
        audiences: [https://tesk.example.org]
```

Each client first gets the former shared audience; then give each client
its own audiences where your provider lets you register them. Without an
audience (`allowAnyAudience: true` in chart 0.4.0), give each client
`allowAnyAudience: true` instead (`my-gateway: {allowAnyAudience: true}`),
or better its audiences: any audience is no longer the default of a
client. The chart fails with a hint while the values still have the form
of chart 0.4.0 (a shared `audience` or `allowAnyAudience`, also empty or
null, or `clients` as a list, also `[]`), also with `auth.tokenClients`
off, as tesk-api 2.1.0 doesn't start with the variables that they stood
for. A client without audiences (unless `allowAnyAudience: true`), with
both, or with a blank audience, and blank or duplicate client IDs (after
trimming) fail too.

The chart passes the clients on to tesk-api as one JSON variable,
`TESK_API_AUTHORISATION_SERVICE_CLIENTS_CLIENTS`, which replaces
`…_CLIENT_IDS` and `…_AUDIENCE` (see [Upgrading](tesk-api/upgrading.md) in
the docs of tesk-api), so `auth.tokenClients` now needs tesk-api 2.1.0 or
later: with it on and an older `tesk.image.tag` (a version number, by
default the chart's `appVersion`), the chart fails instead of starting a
tesk-api that doesn't start (2.0.0) or ignores the setting. Use tesk-api
2.1.0 or later, or turn `auth.tokenClients` off. With the update strategy
`RollingUpdate` (`tesk.strategy`; the default `Recreate` stops the old pod
first), the old pod still accepts every listed client's tokens for the
former shared audience during the rollout: the audiences per client hold
once it has completed (`kubectl rollout status deployment/<prefix>-api`).
A rollback to chart 0.4.0
(`helm rollback`) restores its values with it. Without
`auth.tokenClients`, nothing changes.

### The old Helm repository is gone

The Helm repository at `https://elixir-cloud-aai.github.io/TESK/` (the
`gh-pages` branch), which held only charts 0.1.0 and 0.1.1, is retired:
`helm repo add tesk https://elixir-cloud-aai.github.io/TESK/`, `helm repo
update` and installs of `tesk/tesk` fail. Remove it from your Helm setup:

```bash
helm repo remove tesk
```

The old charts stay attached to the GitHub releases
[`tesk-0.1.0`](https://github.com/elixir-cloud-aai/TESK/releases/tag/tesk-0.1.0)
and [`tesk-0.1.1`](https://github.com/elixir-cloud-aai/TESK/releases/tag/tesk-0.1.1),
and Helm installs them from their URLs, e.g.:

```bash
helm upgrade --install tesk \
    https://github.com/elixir-cloud-aai/TESK/releases/download/tesk-0.1.1/tesk-0.1.1.tgz \
    --namespace tesk --create-namespace -f my-values.yaml
```

They get no fixes, though: move to the current chart instead. Releases
of charts before 0.3.0 can't be upgraded in place; install them again
with your values adapted, as described in [0.3.0](#030) (see [Migrating a
release](#migrating-a-release)), then follow the sections of the later
releases above, and install the chart from its GitHub release (see [From
a release](deployment.md#from-a-release)).

### Security contexts and resources of task pods

New values give the taskmasters', the filers' and the executors' pods
security contexts and resources, e.g., for namespaces that enforce the
`restricted` Pod Security Standard or have a quota on `limits.cpu` (see
[Restricted namespaces and
quotas](deployment.md#restricted-namespaces-and-quotas)):
`tesk.taskmaster.podSecurityContext`, `tesk.taskmaster.securityContext`,
`tesk.taskmaster.resources`, `tesk.filer.resources`,
`tesk.executor.podSecurityContext` and `tesk.executor.defaultCpu`. They
are unset by default, which changes nothing; most of them need tesk-api
2.1.0 or later, and the notes warn of those that an older one ignores.

**`tesk.executor.securityContext` is the executors' container context
now (breaking).** Up to chart 0.4.0, it was the executors' pod context,
with the fields `runAsUser`, `runAsGroup`, `fsGroup` and `runAsNonRoot`
only; now it takes the fields of a Kubernetes `SecurityContext`, as
`tesk.securityContext` and `tesk.filer.securityContext` do, and the pod's
context is `tesk.executor.podSecurityContext`. Move `fsGroup`, which a
container's context doesn't have, to the pod's context; the installation
fails with a hint while it is under `tesk.executor.securityContext` (a
null `fsGroup` there is fine, e.g., to drop the old one of a release
upgraded with `--reuse-values`):

```yaml
tesk:
  executor:
    podSecurityContext:
      fsGroup: 1000
    securityContext:
      runAsUser: 1000
      runAsGroup: 1000
      runAsNonRoot: true
```

`runAsUser`, `runAsGroup` and `runAsNonRoot` may stay where they are, as
they apply to the executor (the pod's only container) either way; the
chart still puts them into the ConfigMap `<prefix>-executor`, which all
versions of tesk-api read, so they keep working with tesk-api 2.0.0.
Moving them to `tesk.executor.podSecurityContext` too is the clearer
choice.

With tesk-api 2.1.0, the executors of tasks without `resources.cpu_cores`
get 1 CPU as request and limit by default (`tesk.executor.defaultCpu`;
`""` for none, as before), and the taskmasters' containers get requests
and limits by default (`tesk.taskmaster.resources`; `{}` for none): in
namespaces with a `LimitRange` whose CPU maximum is below these, set them
to fit (see [Resources](deployment.md#resources)).

## 0.4.0

Releases of chart 0.3.0 are upgraded in place (`helm upgrade` with the
chart of the [release](deployment.md#from-a-release)). The upgrade brings
tesk-api 2.0.0 (TES 1.1) and the taskmaster and filer of tesk-core 0.12.0,
and the API is down for about a minute during each rollout (update strategy
`Recreate`): read [tesk-api 2.0.0, taskmaster and filer
0.12.0](#tesk-api-200-taskmaster-and-filer-0120) before you upgrade,
especially if your values pin image tags, or if your cluster refuses pods
with the `RuntimeDefault` seccomp profile.

**Don't upgrade with `--reuse-values`:** Helm then renders the chart with
the values of the 0.3.0 release in place of the new defaults, so none of
them apply (e.g., the taskmaster and filer tags, `tesk.strategy` and
`tesk.filer.*`). With the default tags of chart 0.3.0, the API still
moves to tesk-api 2.0.0, as `tesk.image.tag` was empty there, but the
taskmaster and filer stay at 0.11.0, which can't run some TES 1.1 tasks
as asked (see below), so the service info reports TES 1.0.0; and the
API's Deployment keeps `RollingUpdate`. Tags that your values pinned stay
as they were. A copy of the `values.yaml` of chart 0.3.0 among your values
files pins the old taskmaster and filer tags in the same way (the
strategy `Recreate` still applies, as that file doesn't set one). Upgrade
with your own values files, as above, or with
`--reset-then-reuse-values` (Helm 3.14 or later), which applies the
chart's new defaults below the values of the release. The notes of `helm
upgrade` warn about tesk-api 2.0.0 or later with a taskmaster before
0.12.0.

### tesk-api 2.0.0, taskmaster and filer 0.12.0

The chart deploys tesk-api 2.0.0 (its `appVersion`) and taskmaster and
filer 0.12.0 by default now (chart 0.3.0 deployed tesk-api 1.2.0 and
taskmaster and filer 0.11.0). tesk-api 2.0.0 implements TES 1.1, and runs
on Java 21 and Spring Boot 4; tesk-core 0.12.0 adds the taskmaster and
filer side of TES 1.1 (outputs with wildcards and `path_prefix`,
`executors[].ignore_error`, output file logs). With the chart's defaults,
one `helm upgrade` brings both, in the order that they need: the API's
update strategy `Recreate` stops the old API before the new one starts
tasks with the new taskmaster (see [API update strategy
Recreate](#api-update-strategy-recreate)).

- **Act on this if your values pin `tesk.image.tag`,
  `tesk.taskmaster.image.tag` or `tesk.filer.image.tag`:** the new
  defaults apply only to the tags that you don't set. Upgrade the API to
  2.0.0 no later than the taskmaster to 0.12.0: an older API with the new
  taskmaster reports wrong task states, so the installation fails with
  such a pair (e.g., values that pin `tesk.image.tag: 1.2.0` but not the
  taskmaster): set `tesk.taskmaster.image.tag` and `tesk.filer.image.tag`
  to `0.11.0` too, or upgrade the API. Set the taskmaster and filer tags
  together, to the same release. tesk-api 2.0.0 runs with taskmaster and
  filer 0.11.0 too, but it accepts tasks that they can't run as asked:
  executors with `ignore_error: true` stop the task at their failure
  (`SYSTEM_ERROR`, unless the failed executor was the last one and the
  task has no outputs), outputs with wildcards and `path_prefix` fail or land
  in the wrong place, and output file logs stay empty; the notes warn, and
  the service info reports TES 1.0.0. Quote X.Y tags of the taskmaster and filer
  (e.g., `"0.12"`): tags that YAML reads as numbers (e.g., an unquoted
  `0.10`, which is 0.1) fail the installation now. Tags pinned by digest
  (e.g., `0.12.0@sha256:…`) are compared by their version.
- **Act on this if your cluster refuses pods with the `RuntimeDefault`
  seccomp profile, or sets the user of pods by a policy:** filer pods of
  0.12.0 run with a restricted security context (non-root, the
  `RuntimeDefault` seccomp profile, no privilege escalation and
  capabilities, a read-only root filesystem; see the [upgrade notes of
  tesk-core](tesk-core/upgrading.md#hardened-filer-pods)). Replace them
  with the new values `tesk.filer.podSecurityContext` and
  `tesk.filer.securityContext` (see [Configuration](configuration.md));
  e.g., where the cluster refuses pods that ask for `RuntimeDefault` and
  sets its own profile:

    ```yaml
    tesk:
      filer:
        podSecurityContext:
          runAsNonRoot: true
    ```

  Whether OpenShift accepts the filer's defaults (see the [filer's pod
  security](tesk-core/filer.md#pod-security)) depends on the cluster:
  some OpenShift clusters (e.g., CSC Rahti) reject pods that ask for
  `RuntimeDefault` and need `tesk.filer.podSecurityContext:
  {runAsNonRoot: true}`, as above (see [OpenShift and other restricted
  clusters](deployment.md#openshift-and-other-restricted-clusters)). On
  any cluster, check that a task with an input runs after the upgrade:
  the smoke test runs one, which starts a filer pod (see [Checking a
  deployment](deployment.md#checking-a-deployment)).
- **FTP credentials by reference:** with an FTP secret
  (`ftp.classicFtpSecret`), the chart also passes its name on to the
  taskmasters (`TESK_FTP_SECRET_NAME`), so that the filer jobs of
  taskmaster 0.12.0 reference the secret instead of holding the
  credentials as values (see the [upgrade notes of
  tesk-core](tesk-core/upgrading.md#ftp-credentials-by-reference)).
  Nothing to do.
- **Act on this if you use `serviceInfo.existingConfigMap`:** tesk-api
  2.0.0 implements TES 1.1, so set `type.version` to `1.1.0` (with
  taskmaster and filer 0.12.0 or later; `1.0.0` with older ones) and
  `version` to `2.0.0` in your ConfigMap. The chart's own service info
  does this itself: its `type.version` follows `tesk.image.tag` and
  `tesk.taskmaster.image.tag` (`1.1.0` from tesk-api 2.0.0 and taskmaster
  0.12.0 on, `1.0.0` before), and from tesk-api 2.0.0 on it lists
  `tesResources_backend_parameters: []` (TESK supports none). In your own
  ConfigMap, the field is optional: tesk-api 2.0.0 reports `[]` also
  without it; don't add it while the API is still 1.x, which can't read
  the service info with it. With the chart's own service info, the
  ConfigMap changes, so the upgrade restarts the API's pod anyway.
- **Act on this if clients use your API:** tesk-api 2.0.0 changes some
  answers, e.g., `GET /tasks` without `page_size` returns at most 256
  tasks, the states `CANCELING` and `PREEMPTED`, the API description at
  `/v3/api-docs`, and tokens only in the `Authorization` header. Read the
  [upgrade notes of tesk-api](tesk-api/upgrading.md#to-200) before you
  upgrade, and [those of tesk-core](tesk-core/upgrading.md#0120).
  Where the docs of tesk-core 0.12.0 describe the order of the upgrade or
  the filer's security contexts, the chart's order (one `helm upgrade`,
  see above) and its values `tesk.filer.*` take precedence.
- **Private executor images aren't supported by the chart:** tesk-api
  2.0.0 can pull executor images from private registries
  (`docker_registry`, `docker_login` and `docker_pass`, an experimental
  extension, see [Private executor
  images](tesk-api/api.md#private-executor-images)), with an image pull
  secret that it creates for the task. The chart's Role doesn't let it
  create and delete secrets, so such tasks fail (HTTP 500). Use public
  executor images.
- **Act on this if you roll back to chart 0.3.0:** `helm rollback`
  applies the stored manifests of chart 0.3.0 again, without the chart's
  check of the API and taskmaster versions. tesk-api 1.2.0 then reads the
  tasks of taskmaster 0.12.0, takes their filer jobs for executors, and
  reports wrong task states; the API's Deployment also goes back to
  `RollingUpdate`. Before you roll back, let the tasks of taskmaster
  0.12.0 end; to keep new ones from starting meanwhile, upgrade once with
  `tesk.taskmaster.image.tag` and `tesk.filer.image.tag` set to `0.11.0`
  first. Until the rollback, tesk-api 2.0.0 then starts new tasks with
  taskmaster 0.11.0, with the limits described above (e.g., outputs with
  wildcards and `path_prefix`): keep this time short, or hold back such
  tasks.
- `auth.tokenClients` takes effect with tesk-api 2.0.0 (see [Tokens of
  services](#tokens-of-services)); the notes of `helm install` and `helm
  upgrade` warn if it is on with an earlier tesk-api.

### Origins of browser clients (CORS)

The chart can let tesk-api answer cross-origin requests of browser apps
(`tesk.cors.allowedOrigins`, see [Browser clients
(CORS)](deployment.md#browser-clients-cors)). It is empty by default, and
the rendered manifests are unchanged until you list origins. It needs
tesk-api 2.0.0 or later (`tesk.image.tag`; the chart's default now).

### API update strategy Recreate

The API's Deployment uses the update strategy `Recreate` by default
(`tesk.strategy`, see [Configuration](configuration.md)): on every
rollout, Kubernetes stops the old API pod before it starts the new one, so
the API is down until the new pod is ready: usually about a minute (the
default startup probe gives the API up to 5 minutes to start, after the
image pull). Charts up to 0.3.0 set no strategy, so Kubernetes used
`RollingUpdate`, which keeps the old pod serving until the new one is
ready.

The reason is the upgrade to tesk-api 2.0.0 and the taskmaster and filer of
tesk-core 0.12.0. The new taskmaster also labels the filer jobs with
`taskmaster-name`
([tesk-core#147](https://github.com/elixir-cloud-aai/tesk-core/issues/147)),
and tesk-api 2.0.0 selects a task's executor jobs by
`taskmaster-name=<task>,job-type=executor`
([tesk-api#183](https://github.com/elixir-cloud-aai/tesk-api/pull/183)).
An older API that reads tasks started by the new taskmaster takes the
filer jobs for executors, and reports wrong task states. So the TESK API
must be upgraded first, then the taskmaster; see the upgrade notes of
[tesk-api](tesk-api/upgrading.md) and [tesk-core](tesk-core/upgrading.md).
In this chart, the API's pod starts the tasks with the taskmaster and filer
images of `tesk.taskmaster.image` and `tesk.filer.image`, so one `helm
upgrade` that brings both switches them together: with `Recreate`, no old
API pod serves while the new one starts tasks with the new taskmaster.

**Act on this if the API must stay available during rollouts:** set
`tesk.strategy.type: RollingUpdate` (optionally with
`tesk.strategy.rollingUpdate`), but not for an upgrade that brings
tesk-api 2.0.0 and taskmaster 0.12.0 together. Upgrade in two steps
instead: first the API (`tesk.image.tag`) with the old taskmaster and
filer tags, then, once the rollout is done and no old API pod is left
(`kubectl rollout status deployment/<prefix>-api`), the taskmaster and
filer tags. Between the two steps, the new API starts tasks with the old
taskmaster and filer, which fail outputs with wildcards and `path_prefix`
(TES 1.1) or put their matches in the wrong place, and stop a task at the
failure of an executor with `ignore_error: true` (see the [upgrade notes
of tesk-core](tesk-core/upgrading.md#0120)): keep the time between the
steps short. With `Recreate`, one upgrade is enough.

`helm upgrade` with Helm 3 (client-side apply) replaces the strategy of a
release of an earlier chart in place: Kubernetes removes the
`rollingUpdate` settings that it had set by default. **Act on this if
you upgrade a release of a chart up to 0.3.0 with server-side apply**
(e.g., Flux, Argo CD with `ServerSideApply=true`, or Helm 4 for a release
that it installed): there, Kubernetes keeps those settings, and the
upgrade fails with `spec.strategy.rollingUpdate: Forbidden: may not be
specified when strategy type is 'Recreate'`. Releases installed with this
chart's default never have them. Replace the strategy once before the
upgrade (this doesn't restart the API):

```bash
kubectl patch deployment tesk-api --namespace tesk --type=json \
    -p '[{"op": "replace", "path": "/spec/strategy", "value": {"type": "Recreate"}}]'
```

with the name of your API's Deployment (`<prefix>-api`, e.g., `tesk-api`
for the release `tesk`) and its namespace. Alternatively, keep
`RollingUpdate` (see above).

### No FTP secret without credentials

The chart creates the FTP secret (`ftp.classicFtpSecret`, by default
`<prefix>-ftp`) only if `ftp.username` or `ftp.password` is set, and
passes it on to tesk-api only then; before, it created the secret with
empty credentials also without FTP. Releases that use FTP with
`ftp.username` and `ftp.password` keep their secret as it is, as long as
you upgrade with the same values (e.g., `-f secrets.yaml`, as above).

Without FTP credentials, `helm upgrade` deletes the secret, and the API
restarts without an FTP secret, so that tasks get none; as the secret held
no credentials, FTP works as before (anonymously, or with a `.netrc` file).
**Act on this if you put credentials into the secret by hand** (e.g., with
`kubectl edit`) instead of the values: `helm upgrade` would delete it. Move
them into `ftp.username` and `ftp.password` (in `secrets.yaml`) first.
The same applies to a secret of the name in `ftp.classicFtpSecret` that is
made outside the chart: without credentials in the values, tesk-api doesn't
get it. The notes that `helm upgrade` prints warn if `ftp.classicFtpSecret`
is set, but neither `ftp.username` nor `ftp.password`; they don't warn for
the default name (`ftp.classicFtpSecret` null), and they are printed only
after the upgrade. To see them before, run `helm upgrade --dry-run` with
the same values.

### Tokens of services

The chart can let tesk-api accept the access tokens of allow-listed
clients, e.g., of a gateway that calls TESK with the client credentials
grant (`auth.tokenClients`, see [Tokens of
services](deployment.md#tokens-of-services)). It is off by default, and the
rendered manifests are unchanged until you turn it on. It needs tesk-api
2.0.0 or later (`tesk.image.tag`; the chart's default now); with
`auth.mode: noauth`, without an issuer, without an audience (unless
`allowAnyAudience: true`) or without client IDs, the chart fails instead
of starting tesk-api with the setting.

## 0.3.0

**Breaking: install existing releases again.** Releases of charts before
0.3.0 (e.g., 0.1.1) can't be upgraded in place: install them again (see
[Resource names from the release name](#resource-names-from-the-release-name)
and [Migrating a release](#migrating-a-release)), with your values
adapted, as the installation fails on the keys of earlier charts (see
[Values renamed to camelCase](#values-renamed-to-camelcase)). Charts from
0.3.0 on are installed from their GitHub release, not from the Helm
repository on `gh-pages` (see [Releases and chart
versions](#releases-and-chart-versions)).

### tesk-api 1.2.0, taskmaster and filer 0.11.0

The chart deploys tesk-api 1.2.0 (its `appVersion`) and taskmaster and
filer 0.11.0 by default now (chart 0.1.1 deployed tesk-api 1.1.0 and
taskmaster and filer v0.10.2). With these images, the changes below that
need "tesk-api 1.2.0" or "images newer than v0.10.6" take effect when you
upgrade, unless your values pin older tags:

- **Act on this if you use `auth.mode: auth`:** tasks created before the
  upgrade no longer belong to their creators (see [Creator labels of
  tesk-api 1.2.0](#creator-labels-of-tesk-api-120)).
- **Act on this if your tasks use FTP with `ftp.username` and
  `ftp.password`:** the filer sends them only to `ftp.hosts` (see [FTP
  credentials go only to configured
  hosts](#ftp-credentials-go-only-to-configured-hosts)).
- **Act on this if you use the Swagger UI:** tesk-api serves it only with
  `tesk.swaggerUi.enabled: true` (see [Swagger UI with tesk-api
  1.2.0](#swagger-ui-with-tesk-api-120)).
- **Act on this if you set `auth.clientSecret`:** tesk-api 1.2.0 ignores it
  (see [Swagger UI client secret
  deprecated](#swagger-ui-client-secret-deprecated)).
- The taskmaster deletes the PVCs of failed and cancelled tasks (see
  [Newer taskmaster images delete the PVCs of failed
  tasks](#newer-taskmaster-images-delete-the-pvcs-of-failed-tasks)), and
  the filer's HTTP(S) requests time out after 300 seconds without progress
  (see [Timeout of the filer's HTTP(S)
  requests](#timeout-of-the-filers-https-requests)).
- **Act on this if your tasks use more CPU or memory than they request:**
  the executors are limited to the resources that a task requests, and
  are killed (OOM) or throttled beyond them (see [Taskmaster and filer
  v0.10.6](#taskmaster-and-filer-v0106)).
- **Act on this if your tasks leave symbolic links in their outputs:** the
  filer 0.11.0 fails such outputs, and the task fails; executors must copy
  the targets instead (see the [upgrade notes of
  tesk-core](tesk-core/upgrading.md#outputs-cant-contain-symbolic-links)).
- `tesk.taskTtlSeconds` and `tesk.maxQueueSeconds` take effect if you set
  them (see [Deleting finished tasks and a max queue
  time](#deleting-finished-tasks-and-a-max-queue-time)).

tesk-api and tesk-core have upgrade notes of their own, for changes that
the chart's values don't cover (e.g., API responses, log formats, failed
jobs): read the [upgrade notes of tesk-api](tesk-api/upgrading.md) and
[of tesk-core](tesk-core/upgrading.md) too.

**Image tags without `v`:** releases of tesk-core from 0.11.0 on tag their
images `X.Y.Z` (e.g., `0.11.0`), as tesk-api does; earlier ones were tagged
`vX.Y.Z` (e.g., `v0.10.6`). If your values set `tesk.taskmaster.image.tag`
or `tesk.filer.image.tag`, use `0.11.0`, not `v0.11.0`. Set both tags
together, to the same release: from 0.11.0 on, the filer must be of the
same version as the taskmaster. The installation fails if the two tags
are different releases and one of them is 0.11.0 or later (e.g., an older
taskmaster pinned in your values with the default filer 0.11.0); tags that
aren't release versions (e.g., `dev`) aren't checked.

### Creator labels of tesk-api 1.2.0

**Act on this if you use `auth.mode: auth`.** With tesk-api 1.2.0, tasks
created before you upgrade tesk-api no longer belong to their creators.
Upgrade when no tasks run and the old ones are no longer needed, or set the
new value `auth.legacyUserLabels` to `true` for a transition (see [Tasks
created before tesk-api 1.2.0](deployment.md#tasks-created-before-tesk-api-120)).
Releases of charts before 0.3.0 are installed again (see [Migrating a
release](#migrating-a-release)). When you later upgrade a release of 0.3.0
or newer in place to change these settings, the old and the new pod of the
API run side by side for a moment, and creators may get `403 Forbidden`
for their newest tasks until the new pod has taken over.

### Resource names from the release name

**Breaking: install existing releases again.** The chart follows Helm's
conventions now. Its objects get new names and its Deployment a new
selector, which Kubernetes doesn't allow changing: `helm upgrade` fails
for a release named `tesk` (whose Deployment keeps the name `tesk-api`),
and for other release names it would replace all objects at once, with the
problems of an uninstallation (see below) but without a clean state, or
fail on the new Ingress, whose host and path clash with the old one. The
changes:

- **Names:** the names of the chart's objects start with the release name
  (see [Names of the objects](configuration.md#names-of-the-objects)), so
  that several releases can share a namespace. For a release named `tesk`:

    | Object | Before | Now |
    | --- | --- | --- |
    | Deployment and Service of the API | `tesk-api` | `tesk-api` (`<prefix>-api`) |
    | ServiceAccount and Role | `taskmaster` | `tesk-taskmaster` |
    | RoleBinding | `taskmaster-role-binding` | `tesk-taskmaster` |
    | ConfigMap with the service info | `service-info-config` | `tesk-service-info` |
    | Secret with the OIDC client | `oauth-client-secret` | `tesk-oauth-client` |
    | Secret with the FTP credentials | `ftp-secret` (`ftp.classicFtpSecret`) | `tesk-ftp` (if `ftp.classicFtpSecret` is unset) |
    | Ingress | `ingress-rules` | `tesk` |
    | OpenShift Route | `tesk-svc` | `tesk` |
    | StorageClass (`storage: openstack`) | `gold` | `tesk-gold` |
    | Secret with the S3 configuration | `aws-secret` | `aws-secret` (unchanged) |
    | Service and Endpoints of a local FTP server | `ftp` | `ftp` (unchanged) |

    For a release with another name, e.g. `prod`, the prefix is
    `prod-tesk` (`prod-tesk-api`, …). `nameOverride` and `fullnameOverride`
    change the prefix.

- **Selectors:** the Deployment and the Service select the API's pods by
  the standard labels `app.kubernetes.io/name` and
  `app.kubernetes.io/instance` (the release name), instead of `app:
  tesk-api`, which the objects no longer have. Kubernetes doesn't allow
  changing the selector of a Deployment.

- **Values:** the snake_case keys of earlier charts (e.g., `host_name`),
  other keys renamed after Helm's conventions (e.g., `ingress.rules`) and
  `tesk.image` as a string are no longer read. The installation fails if
  your values set any of them, with a list of those in use and their new
  names (see the table below), as do unknown keys (e.g., typos).

#### Migrating a release

The chart's objects hold no data of their own: the secrets are created
from your values files and the files in the chart directory, and the chart
creates no PVCs. The tasks are jobs, pods and PVCs that tesk-api and the
taskmasters create in the namespace, not objects of the release: they stay
when the release is removed. tesk-api reads the tasks from the jobs of its
namespace, so a new release in the same namespace lists the earlier tasks
too (from tesk-api's code; not tested in a migration). To move a release
to this chart:

1. **Rename the values** in your values files (`my-values.yaml`,
   `secrets.yaml`) as in the table below. Check them with
   `helm template tesk charts/tesk -f my-values.yaml -f secrets.yaml`,
   which fails on keys of earlier charts.
2. **Keep the files and values that the secrets are made from**: the FTP
   credentials and the OIDC client ID (`secrets.yaml`), `charts/tesk/ftp/.netrc`
   and `charts/tesk/s3-config/`. If you no longer have them, save the
   secrets before you remove the release, e.g.,
   `kubectl get secret ftp-secret --namespace tesk -o yaml > ftp-secret.yaml`
   (keep these files safe, as they hold credentials).
3. **Wait until no tasks run.** The taskmasters of running tasks use the
   service account `taskmaster`, which is removed with the release, so they
   fail. To stop new tasks from arriving, scale the API down
   (`kubectl scale deployment/tesk-api --replicas=0 --namespace tesk`), and
   wait until `kubectl get jobs --namespace tesk` shows no active jobs.
4. **Remove the release and install it again**, with the same name and
   namespace:

    ```bash
    helm uninstall tesk --namespace tesk
    helm install tesk charts/tesk --namespace tesk \
        -f my-values.yaml -f secrets.yaml
    ```

    The API is unavailable from the uninstallation until the new pod is
    ready (`helm install --wait` waits for it).

If you (or a tool that runs Helm, such as Flux) already ran `helm upgrade`
with this chart, the failed upgrade created some of the new objects and
recorded their names, so `helm uninstall` leaves the objects with the old
names behind (e.g., the Ingress `ingress-rules`, whose host and path then
clash with the new Ingress). Before step 4, roll back to the last revision
that worked (`helm history tesk --namespace tesk`, then
`helm rollback tesk <revision> --namespace tesk`), or delete the objects
with the old names (see the table above) after the uninstallation. Argo
CD applies the rendered objects itself, without a Helm release: delete the
Application with its objects (cascading), then create it again with the
new values.

Things to check:

- **Names that you use outside the chart:** scripts, monitoring or network
  policies that refer to the objects by name (e.g., `taskmaster`,
  `service-info-config`) or by the label `app: tesk-api` need the new names
  and labels. The API's Deployment and Service keep the name `tesk-api` in
  a release named `tesk`.
- **FTP secret:** to keep the name of the FTP secret, set
  `ftp.classicFtpSecret: ftp-secret`; by default, it is `<prefix>-ftp`.
  `ftp.classicFtpSecret: ""` still creates no secret. Put the credentials
  into `ftp.username` and `ftp.password` (in `secrets.yaml`): from
  [0.4.0](#040) on, the chart creates the secret and passes it on to tesk-api only with them, so a secret of that name
  restored by hand isn't used (see [No FTP secret without
  credentials](#no-ftp-secret-without-credentials)).
- **TLS secret:** the secret named in `ingress.tlsSecretName` isn't part of
  the release and stays. With cert-manager, the certificate is issued again
  for the new Ingress if the secret was removed.
- **OpenStack storage class:** with `storage: openstack`, the default
  storage class is `<prefix>-gold` now. The uninstallation deletes the
  storage class `gold`, which was the cluster's default: bound PVCs and
  their volumes keep working, but new PVCs that name `gold`, also those of
  other workloads in the cluster, stay pending. Change them to the new
  name, or leave their class empty to use the default; if your values set
  `storageClass: gold`, do the same there.
- **Releases in one namespace share their tasks:** see [Names of the
  objects](configuration.md#names-of-the-objects).

#### Values renamed to camelCase

The values of the chart follow Helm's conventions now: camelCase names,
`enabled` switches, `image` blocks (`repository`, `tag`, `pullPolicy`), a
`resources` block, and the security contexts of the API as maps. Rename
them in your values files:

| Old name | New name |
| --- | --- |
| `host_name` | `hostName` |
| `tesk.image` (a string with the tag) | `tesk.image.repository` and `tesk.image.tag` (default: the chart's `appVersion`) |
| `tesk.tes_api_base_path` | `tesk.tesApiBasePath` |
| `tesk.taskmaster_image_name` | `tesk.taskmaster.image.repository` |
| `tesk.taskmaster_image_version` | `tesk.taskmaster.image.tag` |
| `tesk.taskmaster_filer_image_name` | `tesk.filer.image.repository` |
| `tesk.taskmaster_filer_image_version` | `tesk.filer.image.tag` |
| `tesk.executor_retries` | `tesk.executorRetries` |
| `tesk.filer_retries` | `tesk.filerRetries` |
| `tesk.limitsCpu` | `tesk.resources.limits.cpu` |
| `tesk.limitsMemory` | `tesk.resources.limits.memory` |
| `tesk.requestsCpu` | `tesk.resources.requests.cpu` |
| `tesk.requestsMemory` | `tesk.resources.requests.memory` |
| `tesk.securityContext.enabled` | `tesk.podSecurityContext` (the pod) and `tesk.securityContext` (the container), maps with the same defaults as before (see below) |
| `transfer.active` | `transfer.enabled` |
| `transfer.wes_base_path` | `transfer.wesBasePath` |
| `transfer.tes_base_path` | `transfer.tesBasePath` |
| `transfer.pvc_name` | `transfer.pvcName` |
| `auth.env_subgroup` | `auth.envSubgroup` |
| `auth.env_basegroup` | `auth.envBaseGroup` |
| `auth.envBasegroup` (a name of the chart on `dev` only) | `auth.envBaseGroup` |
| `auth.service_info_public` | `auth.serviceInfoPublic` |
| `auth.client_id` | `auth.clientId` |
| `auth.client_secret` | none: `auth.clientSecret`, its new name, is deprecated itself; remove it (see [Swagger UI client secret deprecated](#swagger-ui-client-secret-deprecated)) |
| `service.node_port` | `service.nodePort` |
| `ftp.classic_ftp_secret` | `ftp.classicFtpSecret` |
| `ftp.netrc_secret` | `ftp.netrcSecret` |
| `ftp.hostip` | `ftp.hostIp` |
| `ingress.rules` | `ingress.enabled` |
| `ingress.ingressClassName` | `ingress.className` |
| `ingress.tls_secret_name` | `ingress.tlsSecretName` |

For example, these values

```yaml
host_name: tes.example.org
tesk:
  image: docker.io/elixircloud/tesk-api:1.2.0
  limitsMemory: 4Gi
  securityContext:
    enabled: false
ingress:
  rules: true
  ingressClassName: nginx
  tls_secret_name: tesk-tls
```

become

```yaml
hostName: tes.example.org
tesk:
  image:
    tag: 1.2.0
  resources:
    limits:
      memory: 4Gi
  podSecurityContext: null
  securityContext: null
ingress:
  enabled: true
  className: nginx
  tlsSecretName: tesk-tls
```

`tesk.securityContext.enabled: false` was mostly used on OpenShift, which
assigns the user of a pod: there, set only `tesk.podSecurityContext.runAsUser:
null` instead, which keeps the rest of the security contexts. Your values
are merged with the defaults of these maps, so `{}` changes nothing; `null`
removes a field, or the whole context: to drop both, as `enabled: false`
did, set `tesk.podSecurityContext` and `tesk.securityContext` to `null`.

The chart checks the values (`values.schema.json`): e.g., a map where the
chart expects a scalar fails the installation, as do a pull policy other
than `Always`, `IfNotPresent` or `Never`, a value other than `true` or
`false` for `ingress.enabled` and `transfer.enabled`, and unknown keys
(e.g., typos) in the chart's own maps. Maps with Kubernetes' fields
(`tesk.podSecurityContext`, `tesk.securityContext`, the probes,
`tesk.resources.limits` and `requests`, `ingress.annotations`) take
any keys. An empty `ingress.className` now leaves `ingressClassName` out
of the Ingress (it was null before), so the cluster's default class
applies as before.

The template of a TLS secret in the chart directory is now
`tls-secret.yaml-TEMPLATE` (was `tls_secret_name.yml-TEMPLATE`), with a
valid name for the secret (`tesk-tls`).

### Deleting finished tasks and a max queue time

Two new values, empty by default, so upgrading changes nothing:

- `tesk.taskTtlSeconds` lets Kubernetes delete a finished task's jobs and
  pods after that many seconds (see [Deleting finished
  tasks](deployment.md#deleting-finished-tasks)).
- `tesk.maxQueueSeconds` ends a task whose pods can't be scheduled within
  that many seconds (see [Tasks that can't be
  scheduled](deployment.md#tasks-that-cant-be-scheduled)). Set it only with
  tesk-api newer than 1.1; older versions report such tasks as `COMPLETE`.

Both take effect with taskmaster images newer than v0.10.6, for tasks
created after the upgrade; `helm install` and `helm upgrade` print a warning
if the taskmaster or tesk-api image is too old for a value that is set.

### Newer taskmaster images delete the PVCs of failed tasks

With taskmaster images newer than v0.10.6, the taskmaster also deletes the
PVC of a task that fails or is cancelled; before, only tasks that completed
deleted theirs, and the others stayed until someone deleted them by hand. As
for completed tasks, Kubernetes frees the storage once the task's jobs are
deleted (see [#123](https://github.com/elixir-cloud-aai/TESK/issues/123)).
To keep them, e.g. to inspect the files of failed tasks, set the new value
`tesk.keepFailedPvcs` to `true` (see [Configuration](configuration.md)).
PVCs that earlier releases left behind stay: list them with
`kubectl get pvc --namespace tesk`, and delete those of tasks that have
ended (`<task>-pvc`, where `<task>` is the task's ID).

### Executors as non-root users

The new value `tesk.executor.securityContext` (`runAsUser`, `runAsGroup`,
`fsGroup`, `runAsNonRoot`; after chart 0.4.0,
`tesk.executor.podSecurityContext`, see [Security contexts and resources
of task pods](#security-contexts-and-resources-of-task-pods)) sets the
security context of the executors' pods, through the new ConfigMap `<prefix>-executor` (see [Executors as
non-root users](deployment.md#executors-as-non-root-users)). It is empty by
default, which changes nothing; setting or changing it restarts the API's
pod.

### Timeout of the filer's HTTP(S) requests

With taskmaster and filer images newer than v0.10.6, the filer's HTTP(S)
requests time out after 300 seconds without progress (connecting, or
waiting for the next part of a response or upload); before, they could wait
forever. Large files still work: the timeout doesn't limit the whole
transfer. If your HTTP(S) servers take longer to answer, e.g., after large
uploads, raise it with the new value `tesk.filerHttpTimeout` (see
[Configuration](configuration.md)).

### Swagger UI client secret deprecated

**Act on this if you set `auth.clientSecret`.** The Swagger UI is a public
client: its default implicit grant needs no secret, and tesk-api 1.2.0 and
later ignore `auth.clientSecret`. The chart still passes the value on to
older tesk-api images, and its notes warn when it is set; a future release
may remove it. When you upgrade:

- Remove `auth.clientSecret` (or `auth.client_secret`, which fails the
  installation now) from your values (e.g., `secrets.yaml`). The chart then
  sets the secret's `secret` key to empty. If you upgrade a release of this
  chart that had it set, do so with your values files, not with
  `--reuse-values`, which keeps the value (or add
  `--set auth.clientSecret=null`); this clears the value stored before.
  Running pods keep the old value until they restart: if the upgrade
  doesn't change the API's pod (e.g., its image), restart it with
  `kubectl rollout restart deployment/tesk-api --namespace tesk` (the
  Deployment is `<prefix>-api`, here for the release `tesk`).
- Register the Swagger UI's client with your identity provider as a public
  client (implicit grant, or authorisation code if your provider allows it
  for public clients).
- Rotate the secret at your identity provider.

### FTP credentials go only to configured hosts

**Act on this if your tasks use FTP with `ftp.username` and
`ftp.password`.** With taskmaster and filer images newer than v0.10.6, the
filer sends these credentials only to the hosts in the new value `ftp.hosts`
(see [FTP](configuration.md#ftp-ftp)); with `ftp.hosts` empty, it logs in to
every FTP server anonymously, and logs an error that says so. To keep using
the credentials, do one of the following when you upgrade:

- Set `ftp.hosts` to the hosts of the FTP account, e.g.:

  ```yaml
  ftp:
    hosts:
      - ftp.example.org
  ```

- Or put the credentials into a `.netrc` file, with one entry per host
  (`ftp.netrcSecret`; see [FTP](deployment.md#ftp)).

The notes that `helm upgrade` prints warn if `ftp.username` is set,
`ftp.hosts` is empty and `ftp.netrcSecret` is not set. Deployments with a
`.netrc` file, or without FTP credentials, need no change.

### Probes of the API

The API's container has a startup, a readiness and a liveness probe now (see
[Probes](configuration.md#probes)), which request the service info. After
`helm install --wait` or `helm upgrade --wait`, the API answers, and the
Ingress no longer returns `502 Bad Gateway` while it starts. A container that doesn't start within 5 minutes is
restarted (raise `tesk.startupProbe.failureThreshold` on slow nodes). The probes work with your existing values; to turn
one off, set `tesk.<name>Probe.enabled` to `false`.

### Releases and chart versions

Charts are now released from signed `vX.Y.Z` tags as files attached to
[GitHub releases](https://github.com/elixir-cloud-aai/TESK/releases), with
an attestation and a signature (see [Releases](development.md#releases)).
The chart version equals the release version. As tags up to `v0.2` exist
from earlier releases, chart versions continue with 0.3.0, although the
last chart released to the Helm repository at
`https://elixir-cloud-aai.github.io/TESK/` was 0.1.1. That Helm repository
got no new versions and is gone now (see [The old Helm repository is
gone](#the-old-helm-repository-is-gone)): install charts from 0.3.0 on
from their GitHub release (see [From a release](deployment.md#from-a-release)).

### Taskmaster and filer v0.10.6

Charts before 0.3.0 deployed taskmaster and filer v0.10.2 by default; this
chart deploys 0.11.0 (see above), and these changes of v0.10.6 apply to it
too:

- Taskmaster v0.10.2 ends tasks in `SYSTEM_ERROR` on Kubernetes 1.31 or
  later, as it reads only the first condition of a job. If your values set
  `tesk.taskmaster.image.tag` or `tesk.filer.image.tag`, set both to the
  same release, v0.10.6 or later.
- **Resource limits:** v0.10.6 and later set the resources that a task
  requests (`resources.cpu_cores`, `resources.ram_gb`) as the limits of its
  executors too. A task that uses more memory than it requested is now
  killed (OOM), and its CPU is throttled. Tasks that relied on using more
  than they requested must request more.

### Service info from values

The service info comes from the values under `serviceInfo` now, so that it
can be set when installing a packaged chart (see [Service
info](configuration.md#service-info-serviceinfo)). The file
`charts/tesk/service-info/service-info.yaml` is gone, and the chart no
longer reads it. If you edited that file, move its fields into your values
file:

```yaml
serviceInfo:
  id: org.example.tes
  name: TESK
  description: TES of Example
  organization:
    name: Example
    url: https://example.org/
  contactUrl: mailto:tes@example.org
  documentationUrl: https://example.org/tes/
  createdAt: "2026-11-10"
  environment: prod
  storage:
    - s3://example-tes
```

To keep managing the file yourself instead, create a ConfigMap from it
(`kubectl create configmap my-service-info -n tesk
--from-file=service-info.yaml`) and set `serviceInfo.existingConfigMap:
my-service-info`.

The defaults are those of the old file, except for these fields:

- `contactUrl` and `documentationUrl` point to this repository's issues
  and to these docs, not to the former repository.
- The chart now sets `type.version` to `1.0.0` (the TES version that
  tesk-api implements; was `1.0`) and `version` to the tag of tesk-api's
  image (`tesk.image.tag`, by default the chart's `appVersion`; was `1.0`).
  Values can't override either.

All other defaults are unchanged, including `id`, `organization` (EMBL-EBI),
`environment: dev` and `storage`: a release installed without your own
`serviceInfo` still describes no particular deployment. The notes of `helm
install` remind you to describe yours while `serviceInfo.id` is the default. A change of the service info now restarts
the API's pod, so that it takes effect at once.

### Public service info

The new value `auth.serviceInfoPublic` (default `true`) controls whether
`GET /service-info` needs a token with `auth.mode: auth`. It needs tesk-api
1.2.0 or later; earlier versions ignore it and keep the endpoint public.
The default keeps the endpoint public; set it to `false` to require a
token.

### OIDC provider and group names

The new values `auth.userInfoUri`, `auth.groups.*` (`claim`, `prefix`,
`suffix`, `parentGroup`, `adminSubgroup`) and `auth.swaggerOauth.*`
(`authorizationEndpoint`, `tokenEndpoint`, `scopes`) set the OIDC provider
and the names of its groups, e.g., for LS Login (see [LS Login and other
providers](deployment.md#ls-login-and-other-providers)). They are empty by
default, which leaves tesk-api's defaults (ELIXIR AAI), as before. Also:

- `auth.envBaseGroup` and `auth.envSubgroup` are no longer passed on when
  they are empty or null, so that tesk-api's defaults apply (before, they
  were passed on as empty text). Their defaults are unchanged.
  `auth.envBaseGroup` replaces `auth.groups.parentGroup` and
  `auth.envSubgroup` in tesk-api, as before: to make up the environment
  group from those two, set `auth.envBaseGroup: ""`.
- The chart no longer sets the scopes of the Swagger UI itself (it set
  tesk-api's default scopes, in a variable that differed from tesk-api's
  documented one, `TESK_API_SWAGGER_OAUTH_SCOPES`): unless
  `auth.swaggerOauth.scopes` is set, tesk-api's default scopes apply, which
  are the same, and follow `auth.groups.claim`.

### Authorisation by a claim

The new values `auth.claim.enabled`, `auth.claim.name` and
`auth.claim.values` authorise users without groups, by a claim of the user
info (see [Authorisation by a
claim](deployment.md#authorisation-by-a-claim)). They are off by default,
which changes nothing; they need tesk-api 1.2.0 or later.

### Swagger UI with tesk-api 1.2.0

The new value `tesk.swaggerUi.enabled` (default `false`) controls whether
tesk-api serves the Swagger UI (see [Swagger UI](deployment.md#swagger-ui)).
tesk-api before 1.2.0 ignores the value and always serves the Swagger UI;
tesk-api 1.2.0 or later, the chart's default now, serves it only if the
value is `true`. If you use the Swagger UI, set
`tesk.swaggerUi.enabled: true` when you upgrade. Turning it on serves the
Swagger UI publicly; enable it only where needed.
