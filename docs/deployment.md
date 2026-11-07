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
  taskmaster and filer, v0.10.6, were tested on Kubernetes 1.30 and 1.36;
  earlier versions of Kubernetes were not tested with them. On Kubernetes
  1.31 or later, the taskmaster must be v0.10.6 or later (see
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
- Some settings are files in the chart directory rather than values: the
  service info (`charts/tesk/service-info/service-info.yaml`, see [Service
  info](configuration.md#service-info)), the `.netrc` file for FTP
  (`charts/tesk/ftp/.netrc`) and the S3 configuration
  (`charts/tesk/s3-config/`). Edit or add them before installing.

The resources have fixed names (`tesk-api`, `taskmaster`, …), so install one
release per namespace. They have the standard labels of Helm charts
(`app.kubernetes.io/name: tesk`, `app.kubernetes.io/instance: <release>`,
…), e.g., to list them with `kubectl get all -n tesk -l
app.kubernetes.io/instance=tesk`; the selectors of the Deployment and the
Service still use only `app: tesk-api`.

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

With the default values, the chart creates an Ingress (`ingress.rules`), but
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
  rules: true
  ingressClassName: nginx
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
  rules: false
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

On OpenShift, set `ingress.rules: false`: the chart then creates a Route for
`hostName`, with TLS terminated at the router.

## Storage backends

Inputs and outputs with `http://` and `https://` URLs need no backend. For
the others, set up one or more of the following.

### FTP

TESK reads and writes `ftp://` URLs with the credentials of an FTP account.
TLS is not supported by TESK; if you use it with cwl-tes, which requires TLS
for FTP, enable TLS on the FTP server without enforcing it. Provide the
credentials in one of two ways:

- **Username and password** (default): the chart creates the secret named in
  `ftp.classicFtpSecret` (default `ftp-secret`) from `ftp.username` and
  `ftp.password` (in `secrets.yaml`). List the hosts of the account in
  `ftp.hosts` (e.g., `[ftp.example.org]`): the filer sends the credentials
  only to them, and logs in anonymously elsewhere.
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
  active: true
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

## Authentication and authorisation

By default (`auth.mode: noauth`), all endpoints are open. With `auth.mode:
auth`, the API requires an OIDC access token (`Authorization: Bearer`) for
every endpoint except `GET /service-info`, which stays public unless
`auth.serviceInfoPublic` is `false` (tesk-api 1.2.0 or later), the API
description (`GET /v2/api-docs`), and the [Swagger UI](#swagger-ui) if it is
on. TESK works with any OIDC provider; authorisation follows the group model
of LS Login (formerly ELIXIR AAI), configured with `auth.envBasegroup` and
`auth.envSubgroup`. See the [tesk-api section](tesk-api/index.md) and the
[authentication and authorisation
guide](https://github.com/elixir-cloud-aai/tesk-api/blob/master/auth.md) of
tesk-api.

To let users log in from the Swagger UI, register a public OIDC client
(without a secret; implicit grant, or authorisation code if your provider
allows it for public clients) with your provider and put its ID into
`auth.clientId` (in `secrets.yaml`). `auth.clientSecret` is deprecated:
tesk-api 1.2.0 and later ignore it (see
[Upgrading](upgrading.md#swagger-ui-client-secret-deprecated)).

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
authorisation](#authentication-and-authorisation)).

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
