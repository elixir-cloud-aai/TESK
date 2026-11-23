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
  taskmaster and filer, 0.12.0, need Kubernetes 1.23 or later, and their
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

Each change of the API's pod (e.g., `helm upgrade` with a new image or new
settings) stops the old pod before the new one starts, so the API is down
until the new pod is ready, usually about a minute: the API's Deployment
uses the update strategy `Recreate` (`tesk.strategy`). See [API update
strategy Recreate](upgrading.md#api-update-strategy-recreate) for why, and
when `RollingUpdate` is safe.

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

    The Helm repository at `https://elixir-cloud-aai.github.io/TESK/` is
    gone. Charts from 0.3.0 on are attached to the [GitHub
    releases](https://github.com/elixir-cloud-aai/TESK/releases): install
    them as shown above. The old charts 0.1.0 and 0.1.1 are attached to the
    releases `tesk-0.1.0` and `tesk-0.1.1`, without an attestation or a
    signature, and are installed from their URLs instead (see [The old Helm
    repository is gone](upgrading.md#the-old-helm-repository-is-gone)).

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

### Checking a deployment

Once the API is reachable (see [Exposing the API](#exposing-the-api)),
check the deployment from outside the cluster, e.g., after each
installation or upgrade, with
[`tests/smoke/deployment.sh`](https://github.com/elixir-cloud-aai/TESK/blob/dev/tests/smoke/deployment.sh)
from a checkout of this repository (the script isn't part of the
packaged chart). It needs Bash, curl and jq, and takes the base URL of the
TES API. It checks, in this order:

1. `GET /service-info` answers with the service info of a TES.
2. Access control: with an access token in `TOKEN`, requests to `/tasks`
   without a token and with an invalid one are refused (401), and requests
   with the token answer. Without `TOKEN`, these checks are skipped, for
   instances with `auth.mode: noauth`; the script then stops with a hint if
   the instance needs a token, and warns if an `https` URL serves the task
   list without one (see [Authentication and
   authorisation](#authentication-and-authorisation)).
3. A task that runs `echo` ends `COMPLETE`, with exit code 0 and its output
   in the executor's log (`GET /tasks/{id}?view=FULL`).
4. A task with an input ends `COMPLETE`, with the input's content in the
   executor's log. The input has its content inline (no URL), so it needs
   no network and no storage backend, but it gets a PVC (of
   `storageClass`, or the cluster's default class) and starts the inputs
   filer, a pod with the filer's security contexts (`tesk.filer.*`) that
   writes the input to the PVC. This is the check that filer pods are
   admitted and can write to the task's PVC, e.g., after changing the
   filer's security contexts or the taskmaster and filer images.
5. A task that runs `sleep` is cancelled once it is `RUNNING`, and the API
   reports it `CANCELED`. tesk-api 2.0.0 (TES 1.1) reports `CANCELING`
   until the task's jobs have stopped, and `CANCELED` after that; earlier
   versions report `CANCELED` as soon as they have marked the task's
   taskmaster job as cancelled, while its pods may still be stopping.

The tasks end in `COMPLETE`, `EXECUTOR_ERROR`, `SYSTEM_ERROR`, `CANCELED`
or `PREEMPTED`; any of them other than the expected one fails the check at
once. While it waits for a state, `SYSTEM_ERROR` only counts as the end of
a task once it has lasted 10 seconds, as tesk-api reports it for a moment
while Kubernetes updates the status of a task's jobs.

It prints one line per check and stops with a non-zero exit code at the
first check that fails, with the response that failed it. For an instance
with `auth.mode: auth`, put an access token of a user who may run tasks
into `TOKEN`, in the environment rather than on the command line, so that
it stays out of the shell history and the process list (`read -s` prompts
for it without showing it):

```bash
read -rs TOKEN && export TOKEN  # paste the token, then press Enter
tests/smoke/deployment.sh https://tes.example.org/ga4gh/tes/v1
unset TOKEN
```

For an instance without auth, e.g., through the port forward above:

```bash
tests/smoke/deployment.sh http://localhost:8080/ga4gh/tes/v1
```

- The script sends `TOKEN` over HTTPS only; set `ALLOW_HTTP=true` to send
  it to an `http` URL, e.g., through a port forward.
- It waits about `TASK_TIMEOUT` seconds (default 600) for each state of a
  task, polling every 2 s and once more after the last pause, even if that
  ends past the timeout; the first task on a node may wait for the images
  of the taskmaster and the executor (`alpine`) to be pulled, and the task
  with the input for the filer's image and its PVC.
- `IMAGE` replaces the executor image of the tasks (Alpine, pinned by
  digest), e.g., with an image of a non-root user if
  `tesk.executor.podSecurityContext` sets `runAsNonRoot` but no `runAsUser`,
  which Alpine's root user doesn't pass. It needs `echo`, `cat` and
  `sleep`.
- The three tasks (named `deployment check: complete`, `deployment check:
  input` and `deployment check: cancel`) stay in the namespace, as the TES
  API can't delete tasks:
  see [Deleting finished tasks](#deleting-finished-tasks). If the script
  stops early, it cancels the task that hasn't ended yet (and warns if
  that fails). With a `tesk.taskTtlSeconds` of less than a few minutes,
  a task can be gone from the API before the script has read its final
  state and logs, and the check fails.

CI runs the script against the chart's default values on a kind cluster,
and checks that the inputs filer's job completed with the filer's default
security contexts (see [Continuous
integration](development.md#continuous-integration)).

## Exposing the API

With the default values, the chart creates an Ingress (`ingress.enabled`)
without a host name (`hostName`), an Ingress class (`ingress.className`) or
TLS (`ingress.tlsSecretName`). An Ingress rule without a host matches every
host name: the Ingress controller that takes the Ingress serves the API at
`ingress.path` to every request that reaches it, under any host name or IP
address, without a TLS certificate of its own (over plain HTTP, or with the
controller's default certificate). The notes of `helm install` and `helm
upgrade` warn about an empty `hostName`. Without a class, the Ingress goes to
the cluster's default Ingress class; on a cluster without one, it depends on
the controller whether the Ingress is served at all (many ignore Ingresses
without a class). Set `hostName` (see [Ingress](#ingress)), or switch the
Ingress off and use one of the other options below.

`hostName` only routes requests: it doesn't keep anyone out. As the default
`auth.mode` is `noauth`, anyone who reaches an exposed API, under its host
name or otherwise, can run tasks. Set `auth.mode: auth` for an API that is
reachable from outside the cluster, or restrict who can reach it (see
[Authentication and authorisation](#authentication-and-authorisation)).

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

### OpenShift and other restricted clusters

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

By default, the API's pod asks for the `RuntimeDefault` seccomp profile
(`tesk.podSecurityContext.seccompProfile`). Some clusters (e.g., CSC
Rahti) set their own seccomp profile for pods and reject pods that ask
for another one: there,
the API's Deployment gets no pod, and the events of its ReplicaSet
(`kubectl describe replicaset --namespace tesk -l
app.kubernetes.io/instance=tesk`) name the seccomp profile as the reason.
On such clusters, remove the profile, so that the cluster's own profile
applies:

```yaml
tesk:
  podSecurityContext:
    seccompProfile: null
```

Keep the fixed user unless the cluster assigns the user too: then (e.g., on
OpenShift) set `runAsUser: null` next to `seccompProfile: null`, as above.
The rest of the security contexts (non-root, no privilege escalation, no
capabilities) stays as it is. Before installing, check that the rendered
manifests ask for no seccomp profile: with your values, the following
commands print `0` (with the defaults, `1`); the count runs only if the
chart rendered:

```bash
helm template tesk charts/tesk --namespace tesk \
    -f my-values.yaml > rendered.yaml && grep -ci seccomp rendered.yaml
```

This covers the API's pod only. The filer pods of taskmaster and filer
0.12.0, the chart's default, ask for the `RuntimeDefault` profile too (see
the [filer's pod security](tesk-core/filer.md#pod-security)); on such
clusters, e.g., CSC Rahti, replace the filer's pod security context:

```yaml
tesk:
  filer:
    podSecurityContext:
      runAsNonRoot: true
```

`tesk.filer.podSecurityContext` and `tesk.filer.securityContext` replace
the taskmaster's defaults for the filer's pod and container (repeat those
that you want to keep; `{}` leaves a context out; set each context in one
values file, as Helm merges maps of several). The chart passes them on as
they are; the taskmaster checks them for each task, and logs an invalid
one and uses its default instead. Otherwise, only tasks with inputs or
outputs fail (tasks without them start no filer). So check the deployment
after the upgrade (see [Checking a deployment](#checking-a-deployment)):
its task with an input starts a filer pod and must end `COMPLETE`.

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

By default (`auth.mode: noauth`), all endpoints are open: use it only on
local or trusted networks, as anyone who reaches the API can run tasks in
the cluster. With `auth.mode: auth`, the API requires an OIDC access
token (`Authorization: Bearer`) for every endpoint except
`GET /service-info`, which stays public unless `auth.serviceInfoPublic` is
`false` (tesk-api 1.2.0 or later), the API description
(`GET /v3/api-docs`, and `/v2/api-docs`, which serves the same OpenAPI 3
description in tesk-api 2.0.0), and the [Swagger UI](#swagger-ui) if it
is on. tesk-api validates tokens at the user info endpoint of the OIDC
provider (`auth.userInfoUri`) and authorises users by their groups in a
claim of the user info, following a group model of nested groups
(`auth.groups.*`, `auth.envBaseGroup`, `auth.envSubgroup`), or by a claim
(see [Authorisation by a claim](#authorisation-by-a-claim)); tokens of
allow-listed services can be checked without the user info (see [Tokens
of services](#tokens-of-services)). Values left empty use tesk-api's
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

### Tokens of services

Gateways and other services call TESK with access tokens of their own,
obtained with the OAuth 2.0 client credentials grant (e.g., a TES gateway
in front of several TES instances). Such tokens have no user, so the user
info endpoint may refuse them and releases no groups. With
`auth.tokenClients`, tesk-api accepts the access tokens of the clients that
you list, each at its own audiences, without the user info (tesk-api 2.1.0
or later; off by default, and needs `auth.mode: auth`):

```yaml
auth:
  mode: auth
  tokenClients:
    enabled: true
    # Compared exactly with the claim iss of the tokens
    issuer: https://login.example.org/oidc/
    # Client ID to the client's settings
    clients:
      my-gateway:
        # The token's aud must be or contain one of them
        audiences: [https://tes.example.org]
      my-smoke-tests:
        audiences: [https://tes.example.org, tesk-smoke-tests]
```

tesk-api checks a bearer token that is a JWT itself first: its signature
against the keys of the issuer (from `auth.tokenClients.jwksUri`, or by
default from the issuer's discovery document,
`<issuer>/.well-known/openid-configuration`), the issuer, the expiry, the
audience (one of the client's `audiences` in `auth.tokenClients.clients`),
the type `at+jwt` in the header (RFC 9068; `auth.tokenClients.requireAtJwt:
false` turns this off for providers that don't set it), the client ID in
the claim `auth.tokenClients.claim` (default `client_id`; some providers
use `azp`), and that the claim `sub` is the client ID too, as in tokens of
the client credentials grant (RFC 9068). If all hold, the request is the
client's: it may create tasks, and list, get and cancel the tasks it
created; no group rules apply. Other tokens (not a JWT, of another issuer,
of a client that isn't listed, or with another `sub`, such as tokens of
users obtained through a listed client) go to the user info endpoint as
before, so users' tokens keep working. For providers whose client tokens
have another `sub` (e.g., the ID of a service account user), set
`auth.tokenClients.requireClientSubject: false`; then tokens of users
obtained through a listed client count as the client's too, so list only
clients that users can't log in with. The chart fails if the setting is on
without an issuer, without a client, with a client without `audiences`
(unless it has `allowAnyAudience: true`), with both, with a blank audience
or a blank or duplicate client ID (after trimming), or with an `auth.mode`
other than `auth`; the issuer and the JWKS URI must be HTTPS URLs. Quote
client IDs and audiences that YAML reads as numbers or booleans (e.g.,
`"012345":`, `"1e3":`, `"yes":`): Helm turns such keys into other text
(`5349`, `1000`, `true`) before the chart sees them, so that another client
ID would be listed. The chart passes the clients on as one JSON object
(`TESK_API_AUTHORISATION_SERVICE_CLIENTS_CLIENTS`), which tesk-api reads
from 2.1.0 on: with an older image (`tesk.image.tag` as a version number,
by default the chart's `appVersion`), the chart fails, as tesk-api 2.0.0
reads the clients in another form and doesn't start, and earlier versions
ignore the setting. The form of chart 0.4.0 (one shared `audience` and
`clients` as a list) fails with a hint; see
[Upgrading](upgrading.md#audiences-per-client-of-tokenclients).

Every holder of a listed client's credentials can run any image with any
command on the cluster: list only clients that you trust, such as your own
gateway, and keep their secrets as safe as an admin's login. Whoever
controls the issuer's discovery document or keys can sign tokens for a
listed client, which is why the chart accepts only HTTPS URLs for them.
Give each client `audiences` that the provider puts into its tokens for
this deployment only (e.g., its URL), so that tokens which the same client
gets for other services are refused; providers such as LS Login let you
configure the audience per client. Each client is checked against its own
audiences only: listing an audience for one client doesn't make other
clients' tokens for it valid, so a gateway's tokens aren't accepted at the
audience of, e.g., a client for smoke tests. Only if your provider can't
set an audience, give the client `allowAnyAudience: true` instead of
`audiences`: then every service that this client calls with its tokens
can use them to run tasks here.

To revoke a client, remove it from `auth.tokenClients.clients` and upgrade
the release: tesk-api reads the clients at startup, so the old pod keeps
accepting the client's tokens until the rollout has completed and the old
pod is gone (`kubectl rollout status deployment/<prefix>-api`). Also
disable the client or rotate its secret at the provider, so that it gets
no new tokens; those it already has stay valid at other services that
accept them until they expire. See [Access
control](tesk-api/access-control.md) in the docs of tesk-api for the rules.

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
(`tesk.swaggerUi.enabled: false`); the API description (`/v3/api-docs`;
`/v2/api-docs` before tesk-api 2.0.0) is served either way, without a
token. Turning it on serves the Swagger UI publicly, also with `auth.mode: auth`; enable it only where needed:

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

## Browser clients (CORS)

Browsers let a web app call the API from another origin only if the API
allows it with CORS headers. tesk-api sends none by default, so clients
that call TESK from their servers, or through a gateway such as proTES,
need no setting. To let a browser app call TESK directly, list the app's
origins in `tesk.cors.allowedOrigins` (tesk-api 2.0.0 or later):

```yaml
tesk:
  cors:
    allowedOrigins:
      - https://client.example.org
      - http://localhost:3000
```

The chart passes them on to tesk-api, joined by commas
(`TESK_API_CORS_ALLOWED_ORIGINS`).

- **Origins:** list each one exactly as the browser sends it: the scheme,
  the host, and the port unless it is the default
  (`https://client.example.org`, not `https://client.example.org:443`),
  and every variant that you serve the app from (e.g., with and without
  `www.`): `http` or `https`, an ASCII host name (punycode for
  international ones, without `_`), an IPv4 address as four decimal
  numbers or an IPv6 address in brackets, and a port from 1 to 65535
  without leading zeros. Other origins (e.g., wildcards, paths, default
  ports) fail the installation, as tesk-api would stop at startup on them,
  and the API would be down after the upgrade. The chart is a little
  stricter than tesk-api: it also refuses IPv6 zone IDs, which browsers
  don't send, and single-label host names that start with a digit.
- **IPv6 addresses:** write them in the short, lower-case form that
  browsers send (`http://[::1]:3000`). tesk-api compares origins as text
  (ignoring case and a trailing `/`), so it accepts a long form such as
  `http://[0:0:0:0:0:0:0:1]:3000`, but no browser request ever matches
  it.
- **Tokens:** every request but the browsers' preflight requests still
  needs a token with `auth.mode: auth`; CORS only lets browsers read the
  answers. List only origins that you trust with your users' tokens.
- **Details:** what tesk-api answers to the listed and to other origins
  is in its [configuration
  reference](tesk-api/configuration.md#cross-origin-requests-cors).
- **Versions:** tesk-api before 2.0.0 ignores the setting; `helm install`
  and `helm upgrade` print a warning if it is set with such an image
  (`tesk.image.tag` as a version number, by default the chart's
  `appVersion`).

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

The resources of the executors come from each task. With tesk-api 2.1.0
or later, `resources.cpu_cores` and `resources.ram_gb` are both requests
and limits, so a task that uses more memory than it asked for is killed
(OOM), and its CPU is throttled; executors of tasks without `cpu_cores`
get `tesk.executor.defaultCpu` (default: 1 CPU) as request and limit.
Before 2.1.0, the limits depended on the fields that a task set: the
taskmaster set the limits to the requests only for tasks without
`cpu_cores`, and executors of tasks with `cpu_cores` had no memory limit
(or a `LimitRange`'s default, which could be below the request, so that
they never started; see
[tesk-core#160](https://github.com/elixir-cloud-aai/tesk-core/issues/160)).
The disk space of a task (`resources.disk_gb`) sets the size of its PVC.

The taskmasters' and the filers' containers get `tesk.taskmaster.resources`
and `tesk.filer.resources` (see [Configuration](configuration.md#api-and-tasks-tesk)
for the defaults), e.g., for namespaces with quotas (see [Restricted
namespaces and quotas](#restricted-namespaces-and-quotas)).

## Restricted namespaces and quotas

Namespaces that enforce the `restricted` [Pod Security
Standard](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
(label `pod-security.kubernetes.io/enforce: restricted`) refuse pods without
a non-root user, the `RuntimeDefault` (or `Localhost`) seccomp profile, no
privilege escalation and no capabilities. The API's pod meets the standard
with the chart's defaults, and so do the filers' pods of taskmaster 0.12.0;
the taskmasters' and the executors' pods need these values. Without them,
the taskmaster's job is created but never gets a pod, and the task stays
`QUEUED` (the job's events name the reason). Namespaces with a
`ResourceQuota` on `limits.cpu` (or `requests.cpu`) refuse containers
without a CPU limit (or request) in the same way: tesk-api 2.1.0 gives the
taskmasters and the executors CPU limits by default, and the filers get
theirs from `tesk.filer.resources`. Such namespaces need tesk-api 2.1.0 or
later (`tesk.image.tag`) and taskmaster and filer 0.12.0 or later:

```yaml
tesk:
  taskmaster:
    podSecurityContext:
      runAsNonRoot: true
      seccompProfile:
        type: RuntimeDefault
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
  filer:
    # The default of the taskmaster after 0.12.0 (tesk-core#164); 0.12.0
    # sets none
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 1
        memory: 512Mi
  executor:
    podSecurityContext:
      runAsNonRoot: true
      # The filer's user, which owns the files that it stages on the
      # task's volume
      runAsUser: 100
      seccompProfile:
        type: RuntimeDefault
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
```

These are the values that CI installs into such a namespace on kind
(`tests/smoke/restricted/values.yaml`, with `quota.yaml` next to it), with
the [deployment checks](#checking-a-deployment) passing.

- **Executors' user:** the standard needs a non-root user. With `runAsUser:
  100`, the filer's user, executors can read the inputs and write the
  outputs that the filers stage on the task's volume, also on volumes
  whose ownership Kubernetes doesn't manage; with another user, add an
  `fsGroup` (see [Executors as non-root
  users](#executors-as-non-root-users)). Images that need root don't run
  in such a namespace. On clusters that assign users themselves (e.g.,
  OpenShift), leave `runAsUser` out.
- **Seccomp:** on clusters that refuse pods asking for `RuntimeDefault` or
  set their own security contexts (e.g., CSC Rahti), leave these values
  out (see [OpenShift and other restricted
  clusters](#openshift-and-other-restricted-clusters)).
- **CPU and memory:** the executors of tasks without `resources.cpu_cores`
  get `tesk.executor.defaultCpu` (default: 1 CPU); lower it if the quota is
  small, as each running task takes that much of it. Tasks that ask for
  more than the quota leaves wait: their pods are never created, and
  `tesk.maxQueueSeconds` doesn't end them (see [Tasks that can't be
  scheduled](#tasks-that-cant-be-scheduled)). Memory limits come from the
  task's `resources.ram_gb`, or from a `LimitRange`'s default.
- **Older versions:** tesk-api before 2.1.0 ignores these values (but the
  executors' `runAsUser`, `runAsGroup`, `fsGroup` and `runAsNonRoot`), and
  the chart's notes warn; taskmasters before 0.12.0 ignore
  `tesk.filer.resources`, and the notes warn too.

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
    podSecurityContext:
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
as Kubernetes wouldn't start such executors. All versions of tesk-api read
these four fields; the other fields of `tesk.executor.podSecurityContext`
and the container's context, `tesk.executor.securityContext`, need tesk-api
2.1.0 or later (see [Restricted namespaces and
quotas](#restricted-namespaces-and-quotas)). `runAsUser`, `runAsGroup` and
`runAsNonRoot` of the container's context go into the ConfigMap too, and
win over the pod's, as in Kubernetes. The taskmasters and the
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
