# Deployment

TESK is deployed on Kubernetes with its Helm chart, `charts/tesk/`. The
chart installs the API (tesk-api) as a Deployment with a Service, the
service account and role that the API and the taskmasters use to manage
jobs and PVCs, the service info, and, depending on the values, an
Ingress or an OpenShift Route and the secrets of the storage backends. The
taskmasters, filers and executors are created by the API and the
taskmasters for each task (see [Architecture](architecture.md)).

This page covers the installation and the most common setups;
[Configuration](configuration.md) lists all values of the chart.

## Requirements

- **A Kubernetes cluster.** TESK needs access to one namespace only, and
  works in multi-tenant clusters such as OpenShift. The chart's default
  taskmaster and filer, 0.11.0, need Kubernetes 1.23 or later, and their
  end-to-end tests run on Kubernetes 1.37 (see the [upgrade notes of
  tesk-core](tesk-core/upgrading.md)). If you pin older images, set both
  tags to the same release; on Kubernetes 1.31 or later, it must be v0.10.6
  or later, which was tested on Kubernetes 1.30 and 1.36 (see
  [Upgrading](upgrading.md#taskmaster-and-filer-v0106)).
- **[Helm](https://helm.sh/) 3.**
- **A default storage class.** TESK creates a temporary PVC for each task
  with I/O, with the cluster's default storage class (or the one in
  `storageClass`). ReadWriteOnce is enough. The chart doesn't install a
  storage class.
- **A storage backend** to exchange inputs and outputs with the outside
  world, if tasks have I/O over anything but HTTP(S): an FTP account, a
  shared file system (a ReadWriteMany PVC), or S3 (see [Storage
  backends](#storage-backends)).

## Installation

Install the chart from a checkout of this repository, or from the chart
attached to a release (see [From a release](#from-a-release)), into a
namespace of its own:

```bash
git clone https://github.com/elixir-cloud-aai/TESK.git
cd TESK
helm upgrade --install tesk charts/tesk \
    --namespace tesk --create-namespace \
    -f my-values.yaml -f secrets.yaml
```

- `my-values.yaml` holds your settings (see [Configuration](configuration.md)),
  e.g., the host name and the Ingress.
- `secrets.yaml` holds the credentials that the chart puts into secrets: the
  FTP account (`ftp.username`, `ftp.password`) and the OIDC client of the
  Swagger UI (`auth.clientId`). Keep it out of version control. It is
  optional: leave out `-f secrets.yaml` if you need none of these.
- Describe your deployment in the service info that `GET /service-info`
  answers with (`serviceInfo` in `my-values.yaml`, see [Service
  info](configuration.md#service-info-serviceinfo)): at least its `id`,
  `organization`, `contactUrl` and `environment`.
- Some settings are files in the chart directory rather than values: the
  `.netrc` file for FTP (`charts/tesk/ftp/.netrc`) and the S3 configuration
  (`charts/tesk/s3-config/`). Edit or add them before installing.

The names of the objects start with the release name (e.g., `tesk-api` and
`tesk-taskmaster` for the release `tesk`, `prod-tesk-api` for the release
`prod`; see [Names of the objects](configuration.md#names-of-the-objects)),
and they have the standard labels of Helm charts (`app.kubernetes.io/name:
tesk`, `app.kubernetes.io/instance: <release>`, …), e.g., to list them with
`kubectl get all -n tesk -l app.kubernetes.io/instance=tesk`. Several
releases can share a namespace, but they then see each other's tasks:
install releases that must be kept apart into namespaces of their own. The
commands on this page assume the release `tesk` in the namespace `tesk`.

### From a release

Each [release](https://github.com/elixir-cloud-aai/TESK/releases) from
chart version 0.3.0 on has the chart attached, with a GitHub artifact
attestation and a Sigstore bundle. Download the chart, check that TESK's
release workflow built and signed it from the release tag (with the
[GitHub CLI](https://cli.github.com/) and
[cosign](https://docs.sigstore.dev/cosign/system_config/installation/)),
and install it with your values; the files of the chart directory
mentioned above are inside the downloaded chart (`tar -xzf` it to edit
them):

```bash
set -e  # stop if a check fails (Bash; in Fish, run the commands one by one)
gh release download vX.Y.Z --repo elixir-cloud-aai/TESK --pattern 'tesk-*'
gh attestation verify tesk-X.Y.Z.tgz --repo elixir-cloud-aai/TESK \
    --signer-workflow elixir-cloud-aai/TESK/.github/workflows/release.yml \
    --source-ref refs/tags/vX.Y.Z
cosign verify-blob tesk-X.Y.Z.tgz --bundle tesk-X.Y.Z.tgz.sigstore.json \
    --certificate-identity https://github.com/elixir-cloud-aai/TESK/.github/workflows/release.yml@refs/tags/vX.Y.Z \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com
helm upgrade --install tesk tesk-X.Y.Z.tgz \
    --namespace tesk --create-namespace \
    -f my-values.yaml -f secrets.yaml
```

!!! note "Old Helm repository"

    The Helm repository at `https://elixir-cloud-aai.github.io/TESK/`
    (`helm repo add tesk https://elixir-cloud-aai.github.io/TESK/`) holds
    only charts 0.1.0 and 0.1.1 and gets no new versions; it stays
    available so that existing setups still resolve. Charts from 0.3.0 on
    are only attached to the [GitHub
    releases](https://github.com/elixir-cloud-aai/TESK/releases): install
    them as shown above.

For a single machine, see [TESK on a single node with MicroK8s](microk8s.md).

Check the installation:

```bash
helm list -n tesk
kubectl get all -n tesk
kubectl port-forward -n tesk service/tesk-api 8080:8080 &
sleep 2
curl http://localhost:8080/ga4gh/tes/v1/service-info
kill %1  # stop the port forward
```

## Exposing the API

With the default values, the chart creates an Ingress (`ingress.enabled`), but
without a host name and an Ingress class it isn't reachable from outside the
cluster. Choose one of the following.

### Ingress

The recommended way to expose TESK. You need an [Ingress
controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/),
a host name (DNS entry) pointing to it, and a TLS certificate, e.g., from
[Let's Encrypt](https://letsencrypt.org/) with
[cert-manager](https://cert-manager.io/):

```yaml
hostName: tes.example.org
ingress:
  enabled: true
  className: nginx
  path: /
  # The secret that cert-manager creates; empty switches TLS off
  tlsSecretName: tesk-tls
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-production
```

The API is then served at `https://tes.example.org/ga4gh/tes/v1/`, e.g.,
`https://tes.example.org/ga4gh/tes/v1/tasks`.

### NodePort and LoadBalancer

On development clusters such as Minikube or kind, a NodePort Service is the
simplest option:

```yaml
ingress:
  enabled: false
service:
  type: NodePort
  # Any port in the range 30000-32767
  nodePort: 31567
```

The API is then served at port 31567 of every node, e.g.,
`http://<node IP>:31567/ga4gh/tes/v1/tasks` (`minikube ip` prints the IP on
Minikube). On clusters of cloud providers, `service.type: LoadBalancer` gets
an external IP (see the [Kubernetes
docs](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/)).

### OpenShift

On OpenShift, set `ingress.enabled: false`: the chart then creates a Route
for `hostName`, with TLS terminated at the router. OpenShift assigns the
user of the API's pod, so remove the chart's fixed user (UID 1000) too:

```yaml
ingress:
  enabled: false
tesk:
  podSecurityContext:
    runAsUser: null
```

## Storage backends

Inputs and outputs with `http://` and `https://` URLs need no backend. For
the others, set up one or more of the following.

### FTP

TESK reads and writes `ftp://` URLs with the credentials of an FTP account.
TLS is not supported by TESK; if you use it with cwl-tes, which requires TLS
for FTP, enable TLS on the FTP server without enforcing it. Provide the
credentials in one of two ways:

- **Username and password** (default): the chart creates the secret named in
  `ftp.classicFtpSecret` (by default `<prefix>-ftp`, e.g., `tesk-ftp`)
  from `ftp.username` and `ftp.password` (in `secrets.yaml`), if either
  is set; if neither is, it creates no FTP secret. List the
  hosts of the account in `ftp.hosts` (e.g., `[ftp.example.org]`): the
  filer sends the credentials only to them, and logs in anonymously
  elsewhere.
- **`.netrc` file**, which can hold credentials for several servers: set
  `ftp.netrcSecret` (e.g., `netrc-secret`) and `ftp.classicFtpSecret: ""`,
  and put the file at `charts/tesk/ftp/.netrc` (template:
  `charts/tesk/ftp/.netrc-TEMPLATE`).

With both names empty, FTP is off. For an FTP server on the host of a
development cluster, see [Local FTP server](local_ftp.md).

### Shared file system

TESK can read and write `file://` URLs on a PVC that a workflow engine
shares with it: e.g., a ReadWriteMany PVC that a workflow engine in the same
cluster mounts too, or a volume that is visible outside the cluster
(hostPath, NFS) for an engine outside of it. Create the PVC yourself, then
set:

```yaml
transfer:
  enabled: true
  # Where the workflow engine sees the shared volume
  wesBasePath: /data
  # Where the filer mounts it
  tesBasePath: /transfer
  pvcName: transfer-pvc
```

See [Integration with WES](integrated_wes_tes.md) for an example.

### S3

TESK reads and writes `s3://` URLs of S3-compatible object storage (AWS,
MinIO, …). Set `storage: s3` and put the AWS CLI's [`config` and
`credentials`
files](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
into `charts/tesk/s3-config/` (templates: `config-TEMPLATE`,
`credentials-TEMPLATE`); the chart creates the secret `aws-secret` from them.
The filer reads the secret by this fixed name, so only one release per
namespace can use S3.

## Authentication and authorisation

By default (`auth.mode: noauth`), all endpoints are open. With `auth.mode:
auth`, the API requires an OIDC access token (`Authorization: Bearer`) for
every endpoint except `GET /service-info`, which stays public unless
`auth.serviceInfoPublic` is `false` (tesk-api 1.2.0 or later), the API
description (`GET /v2/api-docs`), and the [Swagger UI](#swagger-ui) if it is
on. tesk-api validates tokens at the user info endpoint of the OIDC provider
(`auth.userInfoUri`) and authorises users by their groups in a claim of the
user info, following a group model of nested groups (`auth.groups.*`,
`auth.envBaseGroup`, `auth.envSubgroup`), or by a claim (see [Authorisation
by a claim](#authorisation-by-a-claim)). Values left empty use tesk-api's
defaults, which are those of ELIXIR AAI (`login.elixir-czech.org`, the
provider before LS Login); for any other provider, set them as in [LS Login
and other providers](#ls-login-and-other-providers). See the [tesk-api
section](tesk-api/index.md), in particular [Access
control](tesk-api/access-control.md), for the group model.

### LS Login and other providers

For LS Login, set the user info endpoint and the form of the group names
that LS Login releases in the claim `eduperson_entitlement`:
`urn:geant:lifescience-ri.eu:group:<group>#aai.lifescience-ri.eu`. Here,
`<group>` is the short name of the virtual organisation, then the full name
of the group in it, with `:` between the levels (e.g., `my-vo:tesk:my-team`).
For the Swagger UI's login, also set its endpoints. All endpoints are in LS
Login's [discovery
document](https://login.aai.lifescience-ri.eu/oidc/.well-known/openid-configuration):

```yaml
auth:
  mode: auth
  userInfoUri: https://login.aai.lifescience-ri.eu/oidc/userinfo
  groups:
    claim: eduperson_entitlement
    prefix: "urn:geant:lifescience-ri.eu:group:"
    suffix: "#aai.lifescience-ri.eu"
  # The environment group of this deployment, without prefix and suffix:
  # its team groups are below it (e.g., my-vo:tesk:my-team), and its
  # admins in my-vo:tesk:ADMIN
  envBaseGroup: my-vo:tesk
  swaggerOauth:
    authorizationEndpoint: https://login.aai.lifescience-ri.eu/oidc/authorize
    tokenEndpoint: https://login.aai.lifescience-ri.eu/oidc/token
```

Quote the prefix and the suffix, as YAML reads a value that starts with `#`
as a comment. LS Login releases a group only to services that the group is
assigned to, and only to clients with the scope `eduperson_entitlement`:
check the claim in the user info of a test user. Assign the environment
group itself (`my-vo:tesk`), its team groups and the `ADMIN` groups to the
service's resource in Perun: users need the environment group in the claim
and a team group below it to create and cancel tasks (see [Endpoint
permissions](tesk-api/access-control.md#endpoint-permissions)). Give the
group names as they appear in the claim, where LS Login URL-encodes them
(e.g., `%20` for a space), as tesk-api compares them as plain text. For
access without the group model, see [Authorisation by a
claim](#authorisation-by-a-claim).

`auth.envBaseGroup` is the full name of the environment group; if it is
empty, tesk-api makes it up from `auth.groups.parentGroup` and
`auth.envSubgroup` (`<parentGroup>:<envSubgroup>`); the notes of `helm
install` warn if `auth.groups.parentGroup` is set while `auth.envBaseGroup`
replaces it. `auth.groups.adminSubgroup` renames the admin subgroups
(default `ADMIN`). The chart doesn't set tesk-api's delimiter of the group
levels, as tesk-api recognises team groups by `:` whatever it is.

The Swagger UI offers the scopes of `auth.swaggerOauth.scopes`, a
comma-separated list of `<scope>:<description>`; by default, those of
tesk-api: `openid`, the groups claim (`auth.groups.claim`), `profile` and
`email`. The same settings work for other providers: their discovery
document (`<issuer>/.well-known/openid-configuration`) has the endpoints, and
their docs say how they name groups.

### Authorisation by a claim

Providers whose groups don't fit that model (e.g., LS Login without the
group structure) can authorise users by a claim of the user info instead
(tesk-api 1.2.0 or later). It is off by default, and needs `auth.mode:
auth`:

```yaml
auth:
  mode: auth
  claim:
    enabled: true
    name: eduperson_entitlement
    values:
      - urn:geant:example.org:group:tesk#example.org
```

Users with one of the values in the claim may create tasks, which belong to
them only, without a team, and list, get and cancel their own tasks; group
rules still apply first. Their tokens must come from a client that the
provider allows to release the claim; without it, requests are refused
(`403 Forbidden`). The chart fails if the setting is on without a name or
without values, as tesk-api wouldn't start; values are compared exactly and
mustn't contain commas.

Everyone who has one of the values can run any image with any command on
the cluster. Choose a claim and values that an administrator grants per
user and users can't set themselves, e.g., an entitlement of your
community, not a value that every account has. See [Authorisation
without groups][claim-docs] in the docs of tesk-api for the rules and their
security implications.

[claim-docs]: tesk-api/access-control.md#authorisation-without-groups

To let users log in from the Swagger UI, register a public OIDC client
(without a secret; implicit grant, or authorisation code if your provider
allows it for public clients) with your provider and put its ID into
`auth.clientId` (in `secrets.yaml`). `auth.clientSecret` is deprecated:
tesk-api 1.2.0 and later ignore it (see
[Upgrading](upgrading.md#swagger-ui-client-secret-deprecated)).

### Tasks created before tesk-api 1.2.0

tesk-api 1.2.0 records the creator of a task without loss, in labels other
than those of earlier versions. With `auth.mode: auth`, tasks created by an
earlier version therefore no longer belong to their creators, who can't
list, get or cancel them any more. Either upgrade when no tasks run and the
old ones are no longer needed, or, so that tesk-api also matches the old
tasks to their creators for a transition after the upgrade, set:

```yaml
auth:
  legacyUserLabels: true
```

While it is on, tesk-api filters lists of tasks itself rather than letting
Kubernetes select them by creator, which takes longer the more tasks there
are. Set it back to `false` once the old tasks are no longer needed (e.g.,
after `tesk.taskTtlSeconds`). It is off by default (unset, so tesk-api's
default applies) and has no effect with `auth.mode: noauth`. tesk-api
before 1.2.0 ignores it; `helm install` and `helm upgrade` print a warning
if it is on with such an image (`tesk.image.tag`). See
[Creator labels][creator-labels] in the upgrade notes of tesk-api, also for
how to list and delete the old tasks.

[creator-labels]: tesk-api/upgrading.md

## Swagger UI

tesk-api can serve a Swagger UI, at the root path of the deployment (`/`
redirects to `/swagger-ui/index.html`). It is off by default
(`tesk.swaggerUi.enabled: false`); the API description (`/v2/api-docs`) is
served either way, without a token. Turning it on serves the Swagger UI
publicly, also with `auth.mode: auth`; enable it only where needed:

```yaml
tesk:
  swaggerUi:
    enabled: true
```

The value must be `true` or `false`: anything else fails the installation,
as tesk-api wouldn't start with it (tools that set values only as strings
can use `"true"` and `"false"`). It needs tesk-api 1.2.0 or later
(`tesk.image.tag`); earlier versions ignore it and always serve the Swagger UI.
Users log in from the Swagger UI with the OIDC client of
`auth.clientId` (see [Authentication and
authorisation](#authentication-and-authorisation)), at the provider's
endpoints of `auth.swaggerOauth` (see [LS Login and other
providers](#ls-login-and-other-providers); ELIXIR AAI's by default).

## Resources

The API's container gets the requests and limits of `tesk.resources`
(default: 1 CPU and 2048 MiB of memory, as both requests and limits):

```yaml
tesk:
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1
      memory: 2Gi
```

The resources of the executors come from each task (`resources.cpu_cores`,
`resources.ram_gb`); taskmaster v0.10.6 sets them as both requests and
limits, so a task that uses more memory than it requested is killed (OOM),
and its CPU is throttled. The disk space of a task (`resources.disk_gb`)
sets the size of its PVC.

## Deleting finished tasks

By default, finished tasks stay: their jobs and pods remain in the
namespace until you delete them. With `tesk.taskTtlSeconds`,
Kubernetes deletes a task's jobs and pods that many seconds after the task
finished (completed, failed, or cancelled once its taskmaster had started):

```yaml
tesk:
  taskTtlSeconds: 86400  # a day
```

TESK keeps no database: a task whose jobs are deleted is gone from the API
(`ListTasks` doesn't list it, `GetTask` doesn't find it). Leave the clients
of the API (e.g., workflow engines) enough time to read the final state and
logs of their tasks: hours or days rather than seconds or minutes, e.g.,
`86400` (a day) or `604800` (a week). With `0`, a task disappears as soon as
it finishes. While Kubernetes deletes a task's jobs, the API can briefly
report a task that completed as `SYSTEM_ERROR`; a long TTL makes it
unlikely that clients still read it then.

The TTL applies to tasks created after the API's pod restarted with it;
delete older tasks by hand. `kubectl delete job <task>` deletes a task's
other jobs with it only if its taskmaster image was newer than v0.10.6.
For tasks of older taskmasters, also delete the executors' jobs
(`kubectl delete job -l taskmaster-name=<task>`), the filers' jobs
(`<task>-inputs-filer`, `<task>-outputs-filer`) and the ConfigMap
(`<task>`). Some objects of a task stay: PVCs that
`tesk.keepFailedPvcs` keeps, and, with tesk-api 1.1 and older, the
ConfigMap with the task's JSON; newer versions delete it with the task
([tesk-api#117](https://github.com/elixir-cloud-aai/tesk-api/issues/117)).
The value needs taskmaster images newer than v0.10.6; older ones ignore it,
and the chart's notes warn. See [Deleting finished
tasks](tesk-core/taskmaster.md#deleting-finished-tasks) in the docs of the
taskmaster.

## Tasks that can't be scheduled

By default, a pod that the scheduler can't place, e.g., one that requests
more CPU or memory than any node has, waits forever, and its task stays
`QUEUED`. With `tesk.maxQueueSeconds`, the task ends once such a pod has
waited that many seconds:

```yaml
tesk:
  maxQueueSeconds: 3600  # an hour
```

- An executor that never ran is deleted, and the task ends as
  `SYSTEM_ERROR`. An executor whose earlier attempt ran (a retry,
  `tesk.executorRetries`) ends as `EXECUTOR_ERROR`, a filer as
  `SYSTEM_ERROR`. The taskmaster's log names the job and the scheduler's
  message.
- **Only with tesk-api newer than 1.1** (`tesk.image.tag`), which derives
  the task's state from all of its jobs
  ([tesk-api#104](https://github.com/elixir-cloud-aai/tesk-api/issues/104)):
  tesk-api 1.1 and older report such a task as `COMPLETE`. The chart's notes
  warn about this.
- The taskmaster checks the pods about once a minute, so a task can end up
  to about a minute later than the max queue time.
- Not covered: the taskmaster's own pod, and pods that a `ResourceQuota`
  keeps from being created (they never exist, so they are never
  unschedulable).
- Pick a time longer than nodes need to scale up, if the cluster has an
  autoscaler. The value needs taskmaster images newer than v0.10.6; older
  ones ignore it. It applies to tasks created after the API's pod restarted
  with it.

See [What it does](tesk-core/taskmaster.md#what-it-does) in the docs of the
taskmaster.

## Executors as non-root users

The executors run the tasks' commands with the user of their images, often
root. To run them as another user, set their pods' security context:

```yaml
tesk:
  executor:
    securityContext:
      runAsUser: 1000
      runAsGroup: 1000
      # Group of the files on the task's PVC, so that the executors can
      # read and write those that the filer staged
      fsGroup: 1000
      # Refuse to start executors that would run as root
      runAsNonRoot: true
```

The chart puts these fields into a ConfigMap (`<prefix>-executor`), which
tesk-api reads at startup and applies to the pods of the executors it
creates; changing them restarts the API's pod, and applies to tasks created
afterwards. While the new pod starts, the old one keeps creating tasks with
the old settings. `runAsUser: 0` with `runAsNonRoot: true` fails the chart,
as Kubernetes wouldn't start such executors. tesk-api reads only these four fields. The taskmasters and the
filers aren't affected: their images run them as UID 100. The API's own
pod has separate security contexts (`tesk.podSecurityContext`,
`tesk.securityContext`).

- **`fsGroup`:** the filer writes the inputs to the task's PVC as UID
  100, readable but not writable for others. With `fsGroup`, Kubernetes
  makes the volume's files group-owned by that group and writable for it
  when it mounts the PVC into an executor, so
  executors that run as other users can read and write them (see
  [#113](https://github.com/elixir-cloud-aai/TESK/issues/113)). This works
  for volume types whose ownership Kubernetes manages, e.g., most block
  storage; not for NFS, hostPath, or CSI drivers that don't support it
  (`fsGroupPolicy: None`). With those, set the permissions on the storage
  side.
- **Images:** an executor image that needs root (e.g., to install packages
  at runtime) fails with `runAsUser`; with `runAsNonRoot: true` and no
  `runAsUser`, images whose user is root, or a name rather than a numeric
  ID, don't start; setting `runAsUser` as well avoids that. Set these
  values only if the tasks' images work as other users.
- **Running as root by default:** a non-root default is tracked in
  [#128](https://github.com/elixir-cloud-aai/TESK/issues/128).
