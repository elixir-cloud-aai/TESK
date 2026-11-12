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
| `tesk.image.tag` | `""` | Tag of the API's image; empty uses the chart's `appVersion` (`1.2.0`). |
| `tesk.image.pullPolicy` | `""` | Pull policy of the API's image: `Always`, `IfNotPresent` or `Never` (anything else fails the installation); empty leaves Kubernetes' default. |
| `tesk.port` | `8080` | Port of the API's container and Service. |
| `tesk.tesApiBasePath` | `/ga4gh/tes/v1` | Base path of the TES API; empty uses tesk-api's default. |
| `tesk.taskmaster.image.repository` | `docker.io/elixircloud/tesk-core-taskmaster` | Image of the taskmaster (tesk-core), without its tag. |
| `tesk.taskmaster.image.tag` | `0.11.0` | Tag of the taskmaster image (see [Upgrading](upgrading.md#tesk-api-120-taskmaster-and-filer-0110)). |
| `tesk.filer.image.repository` | `docker.io/elixircloud/tesk-core-filer` | Image of the filer (tesk-core), without its tag. |
| `tesk.filer.image.tag` | `0.11.0` | Tag of the filer image; the same release as the taskmaster's (with or without `v`). Different releases fail the installation if one of them is 0.11.0 or later; tags that aren't release versions (e.g., `dev`) aren't checked. |
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
| `tesk.podSecurityContext` | `runAsUser: 1000`, `runAsNonRoot: true`, `seccompProfile` `RuntimeDefault` | Security context of the API's pod (fields of a Kubernetes `PodSecurityContext`). Your values are merged with the defaults; null removes a field (e.g., `runAsUser: null` on OpenShift, which assigns the user, and `seccompProfile: null` on clusters that set their own seccomp profile, see [OpenShift and other restricted clusters](deployment.md#openshift-and-other-restricted-clusters)) or, for `tesk.podSecurityContext: null`, the whole context. Applies only to the API's pod; for the executors, see `tesk.executor.securityContext`. |
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
| `auth.userInfoUri` | `""` | User info endpoint of the OIDC provider, at which tesk-api validates tokens and reads the groups or the claim (an HTTP(S) URL), e.g., `https://login.aai.lifescience-ri.eu/oidc/userinfo` for LS Login (see [LS Login and other providers](deployment.md#ls-login-and-other-providers)). Empty uses tesk-api's default, ELIXIR AAI's `https://login.elixir-czech.org/oidc/userinfo`. tesk-api sends every request's token to it: the notes warn about `http://` URLs. |
| `auth.groups.claim` | `""` | Claim of the user info with the user's groups; empty uses tesk-api's default, `eduperson_entitlement`. The default scopes of the Swagger UI (`auth.swaggerOauth.scopes`) follow it. |
| `auth.groups.prefix` | `""` | Text before the group names in the claim, e.g., `urn:geant:lifescience-ri.eu:group:` for LS Login; empty uses tesk-api's default, ELIXIR AAI's `urn:geant:elixir-europe.org:group:elixir:`. |
| `auth.groups.suffix` | `""` | Text after the group names in the claim, e.g., `#aai.lifescience-ri.eu` for LS Login (quote it in YAML); empty uses tesk-api's default, ELIXIR AAI's `#perun.elixir-czech.cz`. |
| `auth.groups.parentGroup` | `""` | Parent group of the environment group, without prefix and suffix; only used if `auth.envBaseGroup` is empty. Empty uses tesk-api's default, `GA4GH:GA4GH-CAP`. |
| `auth.groups.adminSubgroup` | `""` | Name of the admins' subgroups, below the environment group (super admins) and below each team group (team admins); empty uses tesk-api's default, `ADMIN`. |
| `auth.envBaseGroup` | `ECP_CLN` | Full name of the environment group of this deployment, without prefix and suffix, below which the team groups are; replaces `auth.groups.parentGroup` and `auth.envSubgroup`. Empty lets tesk-api make it up as `<auth.groups.parentGroup>:<auth.envSubgroup>`. |
| `auth.envSubgroup` | `CSC` | Name of the environment group below `auth.groups.parentGroup`; only used if `auth.envBaseGroup` is empty. Empty uses tesk-api's default, `EBI`. |
| `auth.serviceInfoPublic` | `true` | With `auth.mode: auth`: `true` lets `GET /service-info` answer without a token, `false` requires a valid token for it. Needs tesk-api 1.2.0 or later; earlier versions ignore it and keep the endpoint public. No effect with `noauth`. |
| `auth.legacyUserLabels` | `false` | With `auth.mode: auth`: `true` also matches tasks created by tesk-api before 1.2.0 to their creators, by the creator label of those versions; for a transition after upgrading to tesk-api 1.2.0 (see [Tasks created before tesk-api 1.2.0](deployment.md#tasks-created-before-tesk-api-120)). Needs tesk-api 1.2.0 or later; no effect with `noauth`. |
| `auth.claim.enabled` | `false` | With `auth.mode: auth`: `true` authorises users without groups, by a claim of the user info (see [Authorisation by a claim](deployment.md#authorisation-by-a-claim)). Needs `auth.claim.name` and `auth.claim.values`, and tesk-api 1.2.0 or later; ignored with `auth.mode: noauth`. |
| `auth.claim.name` | `""` | Name of the claim, e.g., `eduperson_entitlement`. |
| `auth.claim.values` | `[]` | Values of the claim, one of which a user needs (compared exactly); non-blank, without commas. |
| `auth.clientId` | none | ID of the OIDC client of the Swagger UI (with `auth.mode: auth`; put it into `secrets.yaml`). |
| `auth.clientSecret` | none | Deprecated: the Swagger UI is a public client, which needs no secret, and tesk-api 1.2.0 and later ignore it; register its client as a public client and leave this unset (see [Upgrading](upgrading.md#swagger-ui-client-secret-deprecated)). |
| `auth.swaggerOauth.authorizationEndpoint` | `""` | Authorisation endpoint of the OIDC provider for the Swagger UI's login (an HTTP(S) URL); empty uses tesk-api's default, ELIXIR AAI's. |
| `auth.swaggerOauth.tokenEndpoint` | `""` | Token endpoint of the provider for the Swagger UI (an HTTP(S) URL), used only with the authorisation code grant; empty uses tesk-api's default, ELIXIR AAI's. |
| `auth.swaggerOauth.scopes` | `""` | Scopes that the Swagger UI offers, comma-separated, each as `<scope>:<description>`; empty uses tesk-api's default: `openid`, the groups claim, `profile` and `email`. |

The values of the provider and the group model (`auth.userInfoUri`,
`auth.groups.*`, `auth.envBaseGroup`, `auth.envSubgroup`,
`auth.swaggerOauth.*`) are passed on to tesk-api as they are, also with
`auth.mode: noauth` (where tesk-api doesn't use them), and only if they are
set: empty or null values leave tesk-api's defaults (see [Access
control](tesk-api/access-control.md#configuration) of tesk-api).

### Service info (`serviceInfo`)

`GET /service-info` answers with the service info of the deployment, in
the format of the [GA4GH service-info
specification](https://github.com/ga4gh-discovery/ga4gh-service-info),
which registries and clients read to find out what the service is and who
runs it. The chart renders it from these values into a ConfigMap (see
[Names of the objects](#names-of-the-objects)), which it mounts into the
API. The defaults describe no particular deployment, so set at least `id`,
`organization`, `contactUrl` and `environment` for yours; the notes of
`helm install` remind you while `id` is the default.

| Value | Default | Description |
| --- | --- | --- |
| `serviceInfo.id` | `uk.ac.ebi.tsc.tesk` | Unique ID of the deployment, in reverse domain notation, e.g., `org.example.tes`. Required. |
| `serviceInfo.name` | `TESK` | Name of the service. Required. |
| `serviceInfo.description` | `GA4GH TES Server implementation for Kubernetes` | Description of the service. |
| `serviceInfo.organization.name` | `EMBL-EBI` | Name of the organisation that runs the service. Required. |
| `serviceInfo.organization.url` | `https://www.ebi.ac.uk/` | URL of the organisation. Required. |
| `serviceInfo.contactUrl` | `https://github.com/elixir-cloud-aai/TESK/issues` | Where users get support, e.g., `mailto:tes@example.org`. |
| `serviceInfo.documentationUrl` | `https://tesk.readthedocs.io/` | Documentation for users of the service. |
| `serviceInfo.createdAt` | `"2021-04-06"` | When the service was created: a date (`2026-11-10`, with two-digit month and day) or a date and time (`2026-11-10T12:00:00Z`), as YAML timestamps; other text fails the installation, as tesk-api couldn't read it. |
| `serviceInfo.updatedAt` | `""` | When the service was last updated, in the same form. |
| `serviceInfo.environment` | `dev` | Environment of the service, e.g., `test`, `staging` or `prod`. |
| `serviceInfo.storage` | `[ftp://ftp-private.ebi.ac.uk]` | Storage locations that tasks can use, e.g., `[s3://bucket]`. |
| `serviceInfo.existingConfigMap` | `""` | Name of a ConfigMap of your own, in the release's namespace, with the key `service-info.yaml`, instead of the chart's; the fields above are then not used, but still checked against the schema. |

Empty optional fields are left out of the service info; the required ones
fail the installation if they are empty. The chart passes text on as text,
but YAML reads unquoted numbers in values files as numbers first: quote
text that looks like a number (e.g., `id: "1.10"`, which would otherwise
become `1.1`). The chart sets two fields itself:
`type` (group `org.ga4gh`, artifact `tes`, version `1.0.0`, which
tesk-api implements; the ConfigMap holds the artifact as `TES`, the form
that tesk-api reads, and tesk-api serves it as `tes`) and
`version` (the tag of tesk-api's image, `tesk.image.tag`, by default the
chart's `appVersion`). A change of the service info restarts the API's pod
(tesk-api reads the file at startup, and then only every hour); with
`serviceInfo.existingConfigMap`, changes of your ConfigMap take effect within
an hour, or when you restart the pod. Service info is public by default,
also with `auth.mode: auth` (see `auth.serviceInfoPublic`).

```yaml
serviceInfo:
  id: org.example.tes
  name: Example TES
  description: TES of Example for the members of its research groups
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

### Service (`service`)

| Value | Default | Description |
| --- | --- | --- |
| `service.type` | `""` | Type of the API's Service: `NodePort`, `LoadBalancer`, or empty for `ClusterIP`. |
| `service.nodePort` | `""` | Node port with `service.type: NodePort` (30000-32767). |

### FTP (`ftp`)

| Value | Default | Description |
| --- | --- | --- |
| `ftp.classicFtpSecret` | null | Name of the secret with the FTP username and password, created from `ftp.username` and `ftp.password` if one of them is set (none without credentials); null uses `<prefix>-ftp`, empty or `false` creates none. |
| `ftp.netrcSecret` | empty | Name of the secret with a `.netrc` file, created from `charts/tesk/ftp/.netrc`; empty creates none. |
| `ftp.hosts` | `[]` | Hosts that the filer sends the credentials of `ftp.classicFtpSecret` to, e.g. `[ftp.example.org]` (see below); empty sends them to no host. Not needed for `.netrc`. |
| `ftp.username` | none | FTP username (put it into `secrets.yaml`). If neither a username nor a password is set, the chart creates no FTP secret, and tesk-api gets none; either one creates it. |
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
| ConfigMap with the service info (none with `serviceInfo.existingConfigMap`) | `<prefix>-service-info` | `tesk-service-info` | `prod-tesk-service-info` |
| ConfigMap with the executors' security context (`tesk.executor.securityContext`) | `<prefix>-executor` | `tesk-executor` | `prod-tesk-executor` |
| Secret with the OIDC client (`auth.mode: auth`) | `<prefix>-oauth-client` | `tesk-oauth-client` | `prod-tesk-oauth-client` |
| Secret with the FTP credentials (`ftp.username`, `ftp.password`) | `ftp.classicFtpSecret`, or `<prefix>-ftp` if it is null (none if it is empty or `false`) | `tesk-ftp` | `prod-tesk-ftp` |
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
