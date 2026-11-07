# Configuration

TESK is configured with the values of its Helm chart
([`charts/tesk/values.yaml`](https://github.com/elixir-cloud-aai/TESK/blob/dev/charts/tesk/values.yaml)
has the defaults) and with a few files in the chart directory. See
[Deployment](deployment.md) for the common setups.

!!! note "Deprecated names of values"
    The values follow Helm's conventions (camelCase, `image` and
    `resources` blocks). The snake_case names of earlier versions of the
    chart (e.g., `host_name`) still work, and take precedence over the new
    names, but are deprecated and will be removed in a later release; the
    notes of `helm install` and `helm upgrade` list those in use. See
    [Upgrading](upgrading.md#values-renamed-to-camelcase) for the old and new
    names.

The chart checks the structure of the values with a JSON schema
(`charts/tesk/values.schema.json`): maps where the chart expects maps,
scalars (of any type) where it expects scalars, and the pull policy of the
image. It accepts unknown keys, and the deprecated names.

## Values

### General

| Value | Default | Description |
| --- | --- | --- |
| `hostName` | `""` | Host name (FQDN) of the API, for the Ingress or the OpenShift Route. |
| `storageClass` | empty | Storage class of the tasks' PVCs; empty uses the cluster's default storage class. |
| `storage` | `none` | `s3` creates the secret `aws-secret` from `charts/tesk/s3-config/` (see [S3](deployment.md#s3)); `openstack` creates a default storage class `gold` for OpenStack Cinder. Anything else adds nothing. |

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
| `tesk.debug` | `false` | Debug logging in the taskmasters. |
| `tesk.executorRetries` | `2` | Retries of an executor's job on errors (its `backoffLimit`). |
| `tesk.filerRetries` | `2` | Retries of a filer's job on errors, while staging inputs or outputs. |
| `tesk.resources` | 1 CPU and `2048Mi` memory, as requests and limits | Resources of the API's container (`requests` and `limits`, as in Kubernetes; further resources, e.g., `ephemeral-storage`, are passed on too). |
| `tesk.startupProbe` | every 5 s, 5 s timeout, up to 60 failures (5 minutes) | Startup probe of the API's container: it holds off the other probes while the API starts, which takes about a minute (see [Probes](#probes)). |
| `tesk.readinessProbe` | every 10 s, 5 s timeout, 3 failures | Readiness probe: the Service and Ingress send requests to the pod, and `helm install --wait` returns, once it succeeds (see [Probes](#probes)). |
| `tesk.livenessProbe` | every 20 s, 5 s timeout, 3 failures | Liveness probe: Kubernetes restarts the container if it fails (see [Probes](#probes)). |
| `tesk.securityContext.enabled` | `true` | Runs the API as a non-root user (UID 1000) with the `RuntimeDefault` seccomp profile, no privilege escalation and no capabilities. |
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
| `transfer.active` | `false` | Enables `file://` inputs and outputs on a shared PVC (see [Shared file system](deployment.md#shared-file-system)). |
| `transfer.wesBasePath` | `/tmp` | Path where the workflow engine sees the shared volume; `file://` URLs must be below it. |
| `transfer.tesBasePath` | `/transfer` | Path where the filer mounts the shared PVC. |
| `transfer.pvcName` | `transfer-pvc` | Name of the shared PVC (not created by the chart). |

### Authentication (`auth`)

| Value | Default | Description |
| --- | --- | --- |
| `auth.mode` | `noauth` | `auth` requires OIDC access tokens (see [Authentication and authorisation](deployment.md#authentication-and-authorisation)); `noauth` leaves all endpoints open. |
| `auth.envBasegroup` | `ECP_CLN` | Base group of the LS Login (ELIXIR AAI) group model that grants access. |
| `auth.envSubgroup` | `CSC` | Subgroup of the base group for this deployment. |
| `auth.serviceInfoPublic` | `true` | With `auth.mode: auth`: `true` lets `GET /service-info` answer without a token, `false` requires a valid token for it. Needs tesk-api 1.2.0 or later; earlier versions ignore it and keep the endpoint public. No effect with `noauth`. |
| `auth.clientId` | none | ID of the OIDC client of the Swagger UI (with `auth.mode: auth`; put it into `secrets.yaml`). |
| `auth.clientSecret` | none | Secret of that client (put it into `secrets.yaml`). |

### Service (`service`)

| Value | Default | Description |
| --- | --- | --- |
| `service.type` | `""` | Type of the API's Service: `NodePort`, `LoadBalancer`, or empty for `ClusterIP`. |
| `service.nodePort` | `""` | Node port with `service.type: NodePort` (30000-32767). |

### FTP (`ftp`)

| Value | Default | Description |
| --- | --- | --- |
| `ftp.classicFtpSecret` | `ftp-secret` | Name of the secret with the FTP username and password, created from `ftp.username` and `ftp.password`; empty creates none. |
| `ftp.netrcSecret` | empty | Name of the secret with a `.netrc` file, created from `charts/tesk/ftp/.netrc`; empty creates none. |
| `ftp.hosts` | `[]` | Hosts that the filer sends the credentials of `ftp.classicFtpSecret` to, e.g. `[ftp.example.org]` (see below); empty sends them to no host. Not needed for `.netrc`. |
| `ftp.username` | none | FTP username (put it into `secrets.yaml`). |
| `ftp.password` | none | FTP password (put it into `secrets.yaml`). |
| `ftp.hostip` | empty | IP of an FTP server outside the cluster, as pods see the host; creates a Service `ftp` for it, so that tasks can use `ftp://ftp/...` (see [Local FTP server](local_ftp.md)). |

Each entry of `ftp.hosts` is `host` or `host:port`, with IPv6 addresses in
brackets. Hosts match exactly, ignoring case, without wildcards; an entry
without a port matches any port of the host. With `ftp.hosts` empty, the
filer logs in to every FTP server anonymously (see
[Filer](tesk-core/filer.md#ftp)). `ftp.hosts` takes effect with taskmaster
and filer images newer than v0.10.6 (`tesk.taskmaster.image.tag`,
`tesk.filer.image.tag`); earlier ones ignore it and send the credentials to
every FTP host.

### Ingress (`ingress`)

| Value | Default | Description |
| --- | --- | --- |
| `ingress.rules` | `true` | Creates an Ingress for `hostName`; `false` creates an OpenShift Route instead, on OpenShift. |
| `ingress.ingressClassName` | `""` | Ingress class. |
| `ingress.path` | `/` | Path of the Ingress, and the context path of the API: the TES API is served at `<path>` + `tesk.tesApiBasePath`. |
| `ingress.tlsSecretName` | empty | Secret with the TLS certificate of `hostName`; empty switches TLS off. With cert-manager, the secret is created automatically. |
| `ingress.annotations` | cert-manager annotations | Annotations of the Ingress, e.g., for cert-manager. |

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
| `secrets.yaml` (passed with `-f`) | `ftp.username`, `ftp.password`, `auth.clientId`, `auth.clientSecret`. |
| `charts/tesk/ftp/.netrc` | FTP credentials as a `.netrc` file, with `ftp.netrcSecret`. |
| `charts/tesk/s3-config/config`, `credentials` | S3 configuration and credentials, with `storage: s3`. |
| `charts/tesk/tls_secret_name.yml-TEMPLATE` | Template of a TLS secret, if you create it yourself. |

The chart quotes the four `secrets.yaml` values, so any character is allowed and a numeric value (e.g., a numeric client ID) becomes a string. Numbers of 2^53 or more can't be read exactly from a values file: quote them (`"12345678901234567890"`) or use `--set-string`. Quote IDs with leading zeros or in hex or exponent form too, because YAML reads them as other numbers. The files are used as they are.

## Environment variables

The chart configures tesk-api through environment variables of its
container (`charts/tesk/templates/common/tesk-deployment.yaml`); the API
passes some on to the taskmasters. See the [tesk-api
section](tesk-api/index.md) for options of the API that the chart doesn't
expose yet.
