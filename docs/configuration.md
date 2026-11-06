# Configuration

TESK is configured with the values of its Helm chart
([`charts/tesk/values.yaml`](https://github.com/elixir-cloud-aai/TESK/blob/dev/charts/tesk/values.yaml)
has the defaults) and with a few files in the chart directory. See
[Deployment](deployment.md) for the common setups.

!!! note "Names of values"
    Most values use snake_case, unlike the camelCase that Helm recommends.
    They will be renamed in a later release, with upgrade notes
    ([#228](https://github.com/elixir-cloud-aai/TESK/issues/228)).

## Values

### General

| Value | Default | Description |
| --- | --- | --- |
| `host_name` | `""` | Host name (FQDN) of the API, for the Ingress or the OpenShift Route. |
| `storageClass` | empty | Storage class of the tasks' PVCs; empty uses the cluster's default storage class. |
| `storage` | `none` | `s3` creates the secret `aws-secret` from `charts/tesk/s3-config/` (see [S3](deployment.md#s3)); `openstack` creates a default storage class `gold` for OpenStack Cinder. Anything else adds nothing. |

### API and tasks (`tesk`)

| Value | Default | Description |
| --- | --- | --- |
| `tesk.image` | `docker.io/elixircloud/tesk-api:1.1.0` | Image of the API (tesk-api), with its tag. |
| `tesk.port` | `8080` | Port of the API's container and Service. |
| `tesk.tes_api_base_path` | `/ga4gh/tes/v1` | Base path of the TES API; empty uses tesk-api's default. |
| `tesk.taskmaster_image_name` | `docker.io/elixircloud/tesk-core-taskmaster` | Image of the taskmaster (tesk-core), without its tag. |
| `tesk.taskmaster_image_version` | `v0.10.6` | Tag of the taskmaster image (see [Upgrading](upgrading.md#taskmaster-and-filer-v0106)). |
| `tesk.taskmaster_filer_image_name` | `docker.io/elixircloud/tesk-core-filer` | Image of the filer (tesk-core), without its tag. |
| `tesk.taskmaster_filer_image_version` | `v0.10.6` | Tag of the filer image. |
| `tesk.debug` | `false` | Debug logging in the taskmasters. |
| `tesk.executor_retries` | `2` | Retries of an executor's job on errors (its `backoffLimit`). |
| `tesk.filer_retries` | `2` | Retries of a filer's job on errors, while staging inputs or outputs. |
| `tesk.limitsCpu` | `1` | CPU limit of the API's container. |
| `tesk.limitsMemory` | `2048Mi` | Memory limit of the API's container. |
| `tesk.requestsCpu` | `1` | CPU request of the API's container. |
| `tesk.requestsMemory` | `2048Mi` | Memory request of the API's container. |
| `tesk.securityContext.enabled` | `true` | Runs the API as a non-root user (UID 1000) with the `RuntimeDefault` seccomp profile, no privilege escalation and no capabilities. |
| `tesk.swaggerUi.enabled` | `false` | `true` serves the Swagger UI (at the root path of the deployment, `ingress.path`, see [Swagger UI](deployment.md#swagger-ui)). Turning it on serves the Swagger UI publicly; enable it only where needed. `true` or `false` only (also as strings, in any case; anything else fails the installation); null leaves tesk-api's default (off). Needs tesk-api 1.2.0 or later; earlier versions ignore it and always serve the Swagger UI. |

### Shared file system (`transfer`)

| Value | Default | Description |
| --- | --- | --- |
| `transfer.active` | `false` | Enables `file://` inputs and outputs on a shared PVC (see [Shared file system](deployment.md#shared-file-system)). |
| `transfer.wes_base_path` | `/tmp` | Path where the workflow engine sees the shared volume; `file://` URLs must be below it. |
| `transfer.tes_base_path` | `/transfer` | Path where the filer mounts the shared PVC. |
| `transfer.pvc_name` | `transfer-pvc` | Name of the shared PVC (not created by the chart). |

### Authentication (`auth`)

| Value | Default | Description |
| --- | --- | --- |
| `auth.mode` | `noauth` | `auth` requires OIDC access tokens (see [Authentication and authorisation](deployment.md#authentication-and-authorisation)); `noauth` leaves all endpoints open. |
| `auth.env_basegroup` | `ECP_CLN` | Base group of the LS Login (ELIXIR AAI) group model that grants access. |
| `auth.env_subgroup` | `CSC` | Subgroup of the base group for this deployment. |
| `auth.service_info_public` | `true` | With `auth.mode: auth`: `true` lets `GET /service-info` answer without a token, `false` requires a valid token for it. Needs tesk-api 1.2.0 or later; earlier versions ignore it and keep the endpoint public. No effect with `noauth`. |
| `auth.client_id` | none | ID of the OIDC client of the Swagger UI (with `auth.mode: auth`; put it into `secrets.yaml`). |
| `auth.client_secret` | none | Secret of that client (put it into `secrets.yaml`). |

### Service (`service`)

| Value | Default | Description |
| --- | --- | --- |
| `service.type` | `""` | Type of the API's Service: `NodePort`, `LoadBalancer`, or empty for `ClusterIP`. |
| `service.node_port` | `""` | Node port with `service.type: NodePort` (30000-32767). |

### FTP (`ftp`)

| Value | Default | Description |
| --- | --- | --- |
| `ftp.classic_ftp_secret` | `ftp-secret` | Name of the secret with the FTP username and password, created from `ftp.username` and `ftp.password`; empty creates none. |
| `ftp.netrc_secret` | empty | Name of the secret with a `.netrc` file, created from `charts/tesk/ftp/.netrc`; empty creates none. |
| `ftp.username` | none | FTP username (put it into `secrets.yaml`). |
| `ftp.password` | none | FTP password (put it into `secrets.yaml`). |
| `ftp.hostip` | empty | IP of an FTP server outside the cluster, as pods see the host; creates a Service `ftp` for it, so that tasks can use `ftp://ftp/...` (see [Local FTP server](local_ftp.md)). |

### Ingress (`ingress`)

| Value | Default | Description |
| --- | --- | --- |
| `ingress.rules` | `true` | Creates an Ingress for `host_name`; `false` creates an OpenShift Route instead, on OpenShift. |
| `ingress.ingressClassName` | `""` | Ingress class. |
| `ingress.path` | `/` | Path of the Ingress, and the context path of the API: the TES API is served at `<path>` + `tesk.tes_api_base_path`. |
| `ingress.tls_secret_name` | empty | Secret with the TLS certificate of `host_name`; empty switches TLS off. With cert-manager, the secret is created automatically. |
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
| `secrets.yaml` (passed with `-f`) | `ftp.username`, `ftp.password`, `auth.client_id`, `auth.client_secret`. |
| `charts/tesk/ftp/.netrc` | FTP credentials as a `.netrc` file, with `ftp.netrc_secret`. |
| `charts/tesk/s3-config/config`, `credentials` | S3 configuration and credentials, with `storage: s3`. |
| `charts/tesk/tls_secret_name.yml-TEMPLATE` | Template of a TLS secret, if you create it yourself. |

## Environment variables

The chart configures tesk-api through environment variables of its
container (`charts/tesk/templates/common/tesk-deployment.yaml`); the API
passes some on to the taskmasters. See the [tesk-api
section](tesk-api/index.md) for options of the API that the chart doesn't
expose yet.
