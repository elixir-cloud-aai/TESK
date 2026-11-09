# Configuration

TESK is configured with the values of its Helm chart
([`charts/tesk/values.yaml`](https://github.com/elixir-cloud-aai/TESK/blob/dev/charts/tesk/values.yaml)
has the defaults) and with a few files in the chart directory. See
[Deployment](deployment.md) for the common setups.

!!! note "Names of values of earlier versions"
    The values follow Helm's conventions (camelCase, `enabled` switches,
    `image`, `resources` and security context blocks). The names of earlier
    versions of the chart (e.g., `host_name` or `ingress.rules`) fail the
    installation, with a list of those in use and their new names; see
    [Upgrading](upgrading.md#resource-names-from-the-release-name) for all
    of them.

The chart checks the values with a JSON schema
(`charts/tesk/values.schema.json`): maps where the chart expects maps,
scalars where it expects scalars (mostly of any type, as tools may set
strings; `true` or `false` for `ingress.enabled` and `transfer.enabled`),
the pull policy of the image, and the ranges of some values. Unknown keys
(e.g., typos) in the chart's own maps fail the installation; maps with
Kubernetes' fields (`tesk.podSecurityContext`, `tesk.securityContext`,
the probes, `tesk.resources.limits` and `requests`, `ingress.annotations`)
take any keys.

## Values

### General

| Value | Default | Description |
| --- | --- | --- |
| `nameOverride` | `""` | Replaces the chart's name (`tesk`) in the names of the objects and in the label `app.kubernetes.io/name` (see [Names of the objects](#names-of-the-objects)). |
| `fullnameOverride` | `""` | Replaces the prefix of the names of the objects (see [Names of the objects](#names-of-the-objects)). |
| `hostName` | `""` | Host name (FQDN) of the API, for the Ingress or the OpenShift Route. |
| `storageClass` | empty | Storage class of the tasks' PVCs; empty uses the cluster's default storage class. |
| `storage` | `none` | `s3` creates the secret `aws-secret` from `charts/tesk/s3-config/` (see [S3](deployment.md#s3)); `openstack` creates a default storage class `<prefix>-gold` for OpenStack Cinder (one release per cluster may do so). Anything else adds nothing. |

### API and tasks (`tesk`)

| Value | Default | Description |
| --- | --- | --- |
| `tesk.image.repository` | `docker.io/elixircloud/tesk-api` | Image of the API (tesk-api), without its tag. |
| `tesk.image.tag` | `""` | Tag of the API's image; empty uses the chart's `appVersion` (`1.1.0`). |
| `tesk.image.pullPolicy` | `""` | Pull policy of the API's image: `Always`, `IfNotPresent` or `Never` (anything else fails the installation); empty leaves Kubernetes' default. |
| `tesk.port` | `8080` | Port of the API's container and Service. |
| `tesk.tesApiBasePath` | `/ga4gh/tes/v1` | Base path of the TES API; empty uses tesk-api's default. |
| `tesk.taskmaster.image.repository` | `docker.io/elixircloud/tesk-core-taskmaster` | Image of the taskmaster (tesk-core), without its tag. |
| `tesk.taskmaster.image.tag` | `v0.10.6` | Tag of the taskmaster image (see [Upgrading](upgrading.md#taskmaster-and-filer-v0106)). |
| `tesk.filer.image.repository` | `docker.io/elixircloud/tesk-core-filer` | Image of the filer (tesk-core), without its tag. |
| `tesk.filer.image.tag` | `v0.10.6` | Tag of the filer image. |
| `tesk.executor.securityContext` | `{}` | Security context of the executors' pods: `runAsUser`, `runAsGroup`, `fsGroup` (integers from 0 to 2147483647) and `runAsNonRoot` (`true` or `false`); other fields fail the schema check. Empty leaves the executors as their images say. Applies only to the executors, not to the API (`tesk.podSecurityContext`, `tesk.securityContext`), the taskmasters or the filers. See [Executors as non-root users](deployment.md#executors-as-non-root-users). |
| `tesk.debug` | `false` | Debug logging in the taskmasters. |
| `tesk.executorRetries` | `2` | Retries of an executor's job on errors (its `backoffLimit`). |
| `tesk.filerRetries` | `2` | Retries of a filer's job on errors, while staging inputs or outputs. |
| `tesk.filerHttpTimeout` | empty | Timeout of the filer's HTTP(S) requests, in seconds, a positive number up to 1000000 (strings as plain decimals, e.g. `"600"`): for connecting and for each read, not for the whole transfer. Empty uses the filer's default, 300 seconds. Takes effect with taskmaster and filer images newer than v0.10.6 (see [Filer](tesk-core/filer.md#https)). |
| `tesk.keepFailedPvcs` | `false` (the taskmaster's default) | `true` keeps the PVCs of tasks that fail or are cancelled, e.g. to inspect their files; delete them by hand then. `false` lets the taskmaster delete them. Applies to tasks created after the API pod restarted with it (tasks keep the settings of the pod that created them). Takes effect with taskmaster images newer than v0.10.6; older ones always keep them (see [Upgrading](upgrading.md#newer-taskmaster-images-delete-the-pvcs-of-failed-tasks)). Also as the strings `"true"` and `"false"`, or empty (false); other values fail the schema check. |
| `tesk.taskTtlSeconds` | empty | Seconds (0 to 2147483647) after which Kubernetes deletes a finished task's jobs and pods; the task is then gone from the API. Empty keeps finished tasks. Applies to tasks created after the API's pod restarted with it. Recommended: hours or days, e.g., `86400` (a day). Needs taskmaster images newer than v0.10.6. See [Deleting finished tasks](deployment.md#deleting-finished-tasks). |
| `tesk.maxQueueSeconds` | empty | Seconds (1 to 2147483647) that a pod of a task may wait for a node before the task fails with `SYSTEM_ERROR`. Empty waits forever. Applies to tasks created after the API's pod restarted with it. Needs taskmaster images newer than v0.10.6 and tesk-api newer than 1.1. See [Tasks that can't be scheduled](deployment.md#tasks-that-cant-be-scheduled). |
| `tesk.resources` | 1 CPU and `2048Mi` memory, as requests and limits | Resources of the API's container (`requests` and `limits`, as in Kubernetes; further resources, e.g., `ephemeral-storage`, are passed on too). |
| `tesk.startupProbe` | every 5 s, 5 s timeout, up to 60 failures (5 minutes) | Startup probe of the API's container: it holds off the other probes while the API starts, which takes about a minute (see [Probes](#probes)). |
| `tesk.readinessProbe` | every 10 s, 5 s timeout, 3 failures | Readiness probe: the Service and Ingress send requests to the pod, and `helm install --wait` returns, once it succeeds (see [Probes](#probes)). |
| `tesk.livenessProbe` | every 20 s, 5 s timeout, 3 failures | Liveness probe: Kubernetes restarts the container if it fails (see [Probes](#probes)). |
| `tesk.podSecurityContext` | `runAsUser: 1000`, `runAsNonRoot: true`, `seccompProfile` `RuntimeDefault` | Security context of the API's pod (fields of a Kubernetes `PodSecurityContext`). Your values are merged with the defaults; null removes a field (e.g., `runAsUser: null` on OpenShift, which assigns the user) or, for `tesk.podSecurityContext: null`, the whole context. Applies only to the API's pod; for the executors, see `tesk.executor.securityContext`. |
| `tesk.securityContext` | `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]` | Security context of the API's container (fields of a Kubernetes `SecurityContext`), merged with the defaults like `tesk.podSecurityContext`. |
| `tesk.swaggerUi.enabled` | `false` | `true` serves the Swagger UI (at the root path of the deployment, `ingress.path`, see [Swagger UI](deployment.md#swagger-ui)). Turning it on serves the Swagger UI publicly; enable it only where needed. `true` or `false` only (also as strings, in any case; anything else fails the installation); null leaves tesk-api's default (off). Needs tesk-api 1.2.0 or later; earlier versions ignore it and always serve the Swagger UI. |

#### Probes

`tesk.startupProbe`, `tesk.readinessProbe` and `tesk.livenessProbe` take the
fields of a [Kubernetes
probe](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
(e.g., `periodSeconds`, `timeoutSeconds`, `failureThreshold`,
`initialDelaySeconds`), which are merged with the defaults listed above.
`enabled: false` leaves a probe out:

```yaml
tesk:
  readinessProbe:
    periodSeconds: 5
  livenessProbe:
    enabled: false
```

By default, the probes request `GET <ingress.path><tesk.tesApiBasePath>/service-info`
on the API's port (`/ga4gh/tes/v1/service-info` with the default values). The
API answers it from a local file, so it doesn't need the Kubernetes API or a
token. If you set `auth.mode: auth` and `auth.serviceInfoPublic: false`, the
endpoint needs a token, so the probes check that the port accepts connections
instead. An `exec` or `grpc` field (or a `tcpSocket` where the default is
`httpGet`, and the reverse) of your own replaces the default request; `httpGet`
fields (or `tcpSocket` fields, where that is the default) are merged with it,
e.g., `httpGet.httpHeaders` keeps the default path and port.

The startup probe gives the API 5 minutes to start (5 s times 60 failures);
the container is restarted after that. Raise `tesk.startupProbe.failureThreshold`
on slow nodes.

As the readiness probe fails until the API answers, `helm install --wait`
(and `helm upgrade --wait`) returns only then, and the Ingress doesn't send
requests to a pod that isn't ready.

### Shared file system (`transfer`)

| Value | Default | Description |
| --- | --- | --- |
| `transfer.enabled` | `false` | Enables `file://` inputs and outputs on a shared PVC (see [Shared file system](deployment.md#shared-file-system)). |
| `transfer.wesBasePath` | `/tmp` | Path where the workflow engine sees the shared volume; `file://` URLs must be below it. |
| `transfer.tesBasePath` | `/transfer` | Path where the filer mounts the shared PVC. |
| `transfer.pvcName` | `transfer-pvc` | Name of the shared PVC (not created by the chart). |

### Authentication (`auth`)

| Value | Default | Description |
| --- | --- | --- |
| `auth.mode` | `noauth` | `auth` requires OIDC access tokens (see [Authentication and authorisation](deployment.md#authentication-and-authorisation)); `noauth` leaves all endpoints open. |
| `auth.envBaseGroup` | `ECP_CLN` | Base group of the LS Login (ELIXIR AAI) group model that grants access. |
| `auth.envSubgroup` | `CSC` | Subgroup of the base group for this deployment. |
| `auth.serviceInfoPublic` | `true` | With `auth.mode: auth`: `true` lets `GET /service-info` answer without a token, `false` requires a valid token for it. Needs tesk-api 1.2.0 or later; earlier versions ignore it and keep the endpoint public. No effect with `noauth`. |
| `auth.legacyUserLabels` | `false` | With `auth.mode: auth`: `true` also matches tasks created by tesk-api before 1.2.0 to their creators, by the creator label of those versions; for a transition after upgrading to tesk-api 1.2.0 (see [Tasks created before tesk-api 1.2.0](deployment.md#tasks-created-before-tesk-api-120)). Needs tesk-api 1.2.0 or later; no effect with `noauth`. |
| `auth.claim.enabled` | `false` | With `auth.mode: auth`: `true` authorises users without groups, by a claim of the user info (see [Authorisation by a claim](deployment.md#authorisation-by-a-claim)). Needs `auth.claim.name` and `auth.claim.values`, and tesk-api 1.2.0 or later; ignored with `auth.mode: noauth`. |
| `auth.claim.name` | `""` | Name of the claim, e.g., `eduperson_entitlement`. |
| `auth.claim.values` | `[]` | Values of the claim, one of which a user needs (compared exactly); non-blank, without commas. |
| `auth.clientId` | none | ID of the OIDC client of the Swagger UI (with `auth.mode: auth`; put it into `secrets.yaml`). |
| `auth.clientSecret` | none | Deprecated: the Swagger UI is a public client, which needs no secret, and tesk-api 1.2.0 and later ignore it; register its client as a public client and leave this unset (see [Upgrading](upgrading.md#swagger-ui-client-secret-deprecated)). |

### Service (`service`)

| Value | Default | Description |
| --- | --- | --- |
| `service.type` | `""` | Type of the API's Service: `NodePort`, `LoadBalancer`, or empty for `ClusterIP`. |
| `service.nodePort` | `""` | Node port with `service.type: NodePort` (30000-32767). |

### FTP (`ftp`)

| Value | Default | Description |
| --- | --- | --- |
| `ftp.classicFtpSecret` | null | Name of the secret with the FTP username and password, created from `ftp.username` and `ftp.password`; null uses `<prefix>-ftp`, empty or `false` creates none. |
| `ftp.netrcSecret` | empty | Name of the secret with a `.netrc` file, created from `charts/tesk/ftp/.netrc`; empty creates none. |
| `ftp.hosts` | `[]` | Hosts that the filer sends the credentials of `ftp.classicFtpSecret` to, e.g. `[ftp.example.org]` (see below); empty sends them to no host. Not needed for `.netrc`. |
| `ftp.username` | none | FTP username (put it into `secrets.yaml`). |
| `ftp.password` | none | FTP password (put it into `secrets.yaml`). |
| `ftp.hostIp` | empty | IP of an FTP server outside the cluster, as pods see the host; creates a Service `ftp` for it, so that tasks can use `ftp://ftp/...` (see [Local FTP server](local_ftp.md)). |

Each entry of `ftp.hosts` is `host` or `host:port`, with IPv6 addresses in
brackets. Hosts match exactly, ignoring case, without wildcards; an entry
without a port matches port 21 only (and URLs without a port), so list other
ports explicitly, e.g. `data.example.org:2121`. With `ftp.hosts` empty, the
filer sends the credentials of `ftp.classicFtpSecret` to no host, and logs
in anonymously unless a `.netrc` file has credentials for the host (see
[Filer](tesk-core/filer.md#ftp)). `ftp.hosts` takes effect with taskmaster
and filer images newer than v0.10.6 (`tesk.taskmaster.image.tag`,
`tesk.filer.image.tag`); earlier ones ignore it and send the credentials to
every FTP host.

### Ingress (`ingress`)

| Value | Default | Description |
| --- | --- | --- |
| `ingress.enabled` | `true` | Creates an Ingress for `hostName`; `false` creates an OpenShift Route instead, on OpenShift. |
| `ingress.className` | `""` | Ingress class (`ingressClassName` of the Ingress); empty uses the cluster's default class. |
| `ingress.path` | `/` | Path of the Ingress, and the context path of the API: the TES API is served at `<path>` + `tesk.tesApiBasePath`. |
| `ingress.tlsSecretName` | empty | Secret with the TLS certificate of `hostName`; empty switches TLS off. With cert-manager, the secret is created automatically. |
| `ingress.annotations` | cert-manager annotations | Annotations of the Ingress, e.g., for cert-manager. |

## Names of the objects

The names of the chart's objects start with a prefix derived from the
release name, as in charts made with `helm create`: the release name, if it
contains the chart's name (`tesk`), else `<release>-tesk`.
`fullnameOverride` replaces the whole prefix, `nameOverride` the chart's
name in it. The prefix is cut to 50 characters, so that all names fit the
63 characters that Kubernetes allows. It must be a valid start of a Service
name (a lowercase letter first, then lowercase letters, digits and dashes):
release names that start with a digit or contain dots, which Helm accepts,
and a `nameOverride` with capital letters, fail the installation unless
`fullnameOverride` is set.

| Object | Name | Release `tesk` | Release `prod` |
| --- | --- | --- | --- |
| Deployment and Service of the API | `<prefix>-api` | `tesk-api` | `prod-tesk-api` |
| ServiceAccount, Role and RoleBinding of the API and the taskmasters | `<prefix>-taskmaster` | `tesk-taskmaster` | `prod-tesk-taskmaster` |
| ConfigMap with the service info | `<prefix>-service-info` | `tesk-service-info` | `prod-tesk-service-info` |
| ConfigMap with the executors' security context (`tesk.executor.securityContext`) | `<prefix>-executor` | `tesk-executor` | `prod-tesk-executor` |
| Secret with the OIDC client (`auth.mode: auth`) | `<prefix>-oauth-client` | `tesk-oauth-client` | `prod-tesk-oauth-client` |
| Secret with the FTP credentials | `ftp.classicFtpSecret`, or `<prefix>-ftp` if it is null (none if it is empty or `false`) | `tesk-ftp` | `prod-tesk-ftp` |
| Ingress, or OpenShift Route | `<prefix>` | `tesk` | `prod-tesk` |
| StorageClass (`storage: openstack`) | `<prefix>-gold` | `tesk-gold` | `prod-tesk-gold` |
| Secret with the `.netrc` file | `ftp.netrcSecret` | | |
| Secret with the S3 configuration (`storage: s3`) | `aws-secret` (fixed) | | |
| Service and Endpoints of a local FTP server (`ftp.hostIp`) | `ftp` (fixed) | | |

The chart passes the names that the taskmasters need (service account, FTP
secret, `.netrc` secret) on to tesk-api. Two names are fixed, because others
read them by name: the filer mounts the secret `aws-secret`, and tasks
reach a local FTP server as `ftp://ftp/`. So several releases can share a
namespace, but only one of them can use `storage: s3` or `ftp.hostIp`, and
the secrets named in the values (`ftp.classicFtpSecret`, `ftp.netrcSecret`)
need names of their own in each release. `storage: openstack` creates a
default storage class for the whole cluster: use it in one release only.
Each release also needs a `hostName` (or `ingress.path`) of its own, as
Ingresses with the same host and path clash, and a release name that gives
a prefix of its own: e.g., the releases `prod` and `prod-tesk` both get the
prefix `prod-tesk`, so Helm refuses to install the second one.

The API's pods have the labels `app.kubernetes.io/name` and
`app.kubernetes.io/instance` (the release name), which the Deployment and
the Service select them by; all objects also have the other standard labels
of Helm charts (`app.kubernetes.io/version`, `app.kubernetes.io/managed-by`,
`helm.sh/chart`). List the objects of a release with, e.g.,
`kubectl get all -n tesk -l app.kubernetes.io/instance=tesk`.

!!! warning "Releases in one namespace share their tasks"
    tesk-api lists, reads and cancels the tasks (jobs) of its namespace,
    not only those that it created. Releases in one namespace therefore
    see each other's tasks, and users of one release can read and cancel
    tasks of another, within the limits of authentication (`auth.mode`).
    Install releases that must be kept apart in namespaces of their own.

## Files

### Service info

The response of `GET /service-info` comes from
`charts/tesk/service-info/service-info.yaml`, mounted into the API. Edit it
for your deployment before installing: at least `id` (unique, in reverse
domain notation), `name`, `organization`, `contactUrl` and `environment`.
See the [TES
specification](https://github.com/ga4gh/task-execution-schemas) for its
fields.

### Secrets

| File | For |
| --- | --- |
| `secrets.yaml` (passed with `-f`) | `ftp.username`, `ftp.password`, `auth.clientId`. |
| `charts/tesk/ftp/.netrc` | FTP credentials as a `.netrc` file, with `ftp.netrcSecret`. |
| `charts/tesk/s3-config/config`, `credentials` | S3 configuration and credentials, with `storage: s3`. |
| `charts/tesk/tls-secret.yaml-TEMPLATE` | Template of a TLS secret, if you create it yourself. |

The chart quotes the four `secrets.yaml` values, so any character is allowed and a numeric value (e.g., a numeric client ID) becomes a string. Numbers of 2^53 or more can't be read exactly from a values file: quote them (`"12345678901234567890"`) or use `--set-string`. Quote IDs with leading zeros or in hex or exponent form too, because YAML reads them as other numbers. The files are used as they are.

## Environment variables

The chart configures tesk-api through environment variables of its
container (`charts/tesk/templates/common/tesk-deployment.yaml`); the API
passes some on to the taskmasters. See the [tesk-api
section](tesk-api/index.md) for options of the API that the chart doesn't
expose yet.
