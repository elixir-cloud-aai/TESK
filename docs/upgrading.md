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
  `ftp.classicFtpSecret: ""` still creates no secret.
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
`fsGroup`, `runAsNonRoot`) sets the security context of the executors'
pods, through the new ConfigMap `<prefix>-executor` (see [Executors as
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
keeps charts 0.1.0 and 0.1.1, so existing `helm repo add` setups still
resolve, but gets no new versions: install charts from 0.3.0 on from their
GitHub release (see [From a release](deployment.md#from-a-release)).

### Taskmaster and filer v0.10.6

The default taskmaster and filer are now v0.10.6 (were v0.10.2):

- Taskmaster v0.10.2 ends tasks in `SYSTEM_ERROR` on Kubernetes 1.31 or
  later, as it reads only the first condition of a job. If your values set
  `tesk.taskmaster.image.tag`, set it to v0.10.6 or later.
- **Resource limits:** v0.10.6 sets the resources that a task requests
  (`resources.cpu_cores`, `resources.ram_gb`) as the limits of its executors
  too. A task that uses more memory than it requested is now killed (OOM),
  and its CPU is throttled. Tasks that relied on using more than they
  requested must request more.

### Public service info

The new value `auth.serviceInfoPublic` (default `true`) controls whether
`GET /service-info` needs a token with `auth.mode: auth`. It needs tesk-api
1.2.0 or later; earlier versions ignore it and keep the endpoint public.
The default keeps the endpoint public; set it to `false` to require a
token.

### Authorisation by a claim

The new values `auth.claim.enabled`, `auth.claim.name` and
`auth.claim.values` authorise users without groups, by a claim of the user
info (see [Authorisation by a
claim](deployment.md#authorisation-by-a-claim)). They are off by default,
which changes nothing; they need tesk-api 1.2.0 or later.

### Swagger UI with tesk-api 1.2.0

The new value `tesk.swaggerUi.enabled` (default `false`) controls whether
tesk-api serves the Swagger UI (see [Swagger UI](deployment.md#swagger-ui)).
Upgrading the chart alone changes nothing: tesk-api before 1.2.0 (the
chart's default `tesk.image.tag` is still 1.1.0) ignores the value and always
serves the Swagger UI. tesk-api 1.2.0 or later serves it only if the value
is `true`. If you use the Swagger UI, set `tesk.swaggerUi.enabled: true`
when you upgrade to tesk-api 1.2.0 or later. Turning it on serves the
Swagger UI publicly; enable it only where needed.
