# Upgrading

Changes that affect existing deployments, newest first. Upgrade a release
with the same values files as before, adapted as described here:

```bash
helm upgrade tesk charts/tesk --namespace tesk -f my-values.yaml -f secrets.yaml
```

## Unreleased

### Swagger UI client secret deprecated

**Act on this if you set `auth.clientSecret`.** The Swagger UI is a public
client: its default implicit grant needs no secret, and tesk-api 1.2.0 and
later ignore `auth.clientSecret`. The chart still passes the value on to
older tesk-api images, and its notes warn when it is set; a future release
may remove it. When you upgrade:

- Remove `auth.clientSecret` (or `auth.client_secret`) from your values
  (e.g., `secrets.yaml`). The chart then sets the secret's `secret` key to
  empty, which also clears the value stored before. Running pods keep the
  old value until they restart: if the upgrade doesn't change the API's
  pod (e.g., its image), restart it with
  `kubectl rollout restart deployment/tesk-api --namespace tesk`.
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
Ingress no longer returns `502 Bad Gateway` while it starts. The pod's
selector and names are unchanged, so `helm upgrade` works as before, and
restarts the pod once. A container that doesn't start within 5 minutes is
restarted (raise `tesk.startupProbe.failureThreshold` on slow nodes). The probes work with your existing values; to turn
one off, set `tesk.<name>Probe.enabled` to `false`.

### Values renamed to camelCase

The values of the chart follow Helm's conventions now: camelCase names,
`image` blocks (`repository`, `tag`, `pullPolicy`) and a `resources` block.
**Your values files keep working unchanged:** the old names still work, and
render the same objects as before. They are deprecated, though, and will be
removed in a later release; the notes that `helm upgrade` prints list those
that your values use. Rename them in your values files at your convenience:

| Old name (deprecated) | New name |
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
| `transfer.wes_base_path` | `transfer.wesBasePath` |
| `transfer.tes_base_path` | `transfer.tesBasePath` |
| `transfer.pvc_name` | `transfer.pvcName` |
| `auth.env_subgroup` | `auth.envSubgroup` |
| `auth.env_basegroup` | `auth.envBasegroup` |
| `auth.service_info_public` | `auth.serviceInfoPublic` |
| `auth.client_id` | `auth.clientId` |
| `auth.client_secret` | `auth.clientSecret` (deprecated itself: remove it, see [Swagger UI client secret deprecated](#swagger-ui-client-secret-deprecated)) |
| `service.node_port` | `service.nodePort` |
| `ftp.classic_ftp_secret` | `ftp.classicFtpSecret` |
| `ftp.netrc_secret` | `ftp.netrcSecret` |
| `ingress.tls_secret_name` | `ingress.tlsSecretName` |

For example, these values

```yaml
host_name: tes.example.org
tesk:
  image: docker.io/elixircloud/tesk-api:1.2.0
  limitsMemory: 4Gi
ingress:
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
ingress:
  tlsSecretName: tesk-tls
```

Things to know:

- **An old name takes precedence** over its new name if a values file sets
  both, even if the old one is empty or null. Remove the old names when you
  add the new ones.
- **`--reuse-values`:** `helm upgrade --reuse-values` keeps the values of
  the installed release, including the defaults of the earlier chart with
  the old names, which then take precedence over new names set with
  `--set` (except `tesk.image.tag` and `tesk.image.pullPolicy`), and which
  the notes list as deprecated. Upgrade with your values files (`-f`)
  instead, without `--reuse-values`, once you have renamed the values.
- **Labels:** all objects get the standard labels of Helm charts
  (`app.kubernetes.io/name`, `app.kubernetes.io/instance`,
  `app.kubernetes.io/version`, `app.kubernetes.io/managed-by`,
  `helm.sh/chart`); the API's pods get the first two. The selectors are
  unchanged (`app: tesk-api`), so `helm upgrade` works as before; the new
  pod labels restart the API's pod once.
- **Schema:** the chart checks the structure of the values
  (`values.schema.json`): e.g., a map where the chart expects a scalar fails
  the installation, as does a pull policy other than `Always`,
  `IfNotPresent` or `Never`. It accepts scalars of any type, unknown keys
  and the old names, so values that worked before still pass.
- The resource names don't change. Names derived from the release name, so
  that several releases can share a namespace, will follow in a release of
  their own
  ([#248](https://github.com/elixir-cloud-aai/TESK/issues/248)).

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

### Swagger UI with tesk-api 1.2.0

The new value `tesk.swaggerUi.enabled` (default `false`) controls whether
tesk-api serves the Swagger UI (see [Swagger UI](deployment.md#swagger-ui)).
Upgrading the chart alone changes nothing: tesk-api before 1.2.0 (the
chart's default `tesk.image.tag` is still 1.1.0) ignores the value and always
serves the Swagger UI. tesk-api 1.2.0 or later serves it only if the value
is `true`. If you use the Swagger UI, set `tesk.swaggerUi.enabled: true`
when you upgrade to tesk-api 1.2.0 or later. Turning it on serves the
Swagger UI publicly; enable it only where needed.
