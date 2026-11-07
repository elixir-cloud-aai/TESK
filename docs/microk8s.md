# TESK on a single node with MicroK8s

This guide installs TESK on one machine, e.g., a VM or a workstation, with
[MicroK8s](https://microk8s.io/), a lightweight Kubernetes that runs on
Ubuntu and other Linux distributions with snap. It is meant for trying out
TESK or for a small test setup, not for production; for the latter, see
[Deployment](deployment.md).

!!! note "What was verified"

    The TESK part of this guide (from [Install TESK](#install-tesk) on) was
    run end to end on a single-node Minikube cluster (Kubernetes 1.34) with
    the NGINX Ingress controller and a default storage class, which MicroK8s
    provides, too, with its addons. The steps that are specific to MicroK8s
    ([Install MicroK8s](#install-microk8s), the class name `public` of its
    Ingress and [Remove everything](#remove-everything)) follow the MicroK8s
    documentation and were **not run** for this guide. If a step doesn't work
    on your version of MicroK8s, please [open an
    issue](https://github.com/elixir-cloud-aai/TESK/issues).

## Requirements

- A machine with Linux, [snap](https://snapcraft.io/docs/installing-snapd),
  `sudo` rights, at least 2 CPU cores and 4 GB of memory, and ports 80 and
  443 that are free (the Ingress of MicroK8s uses them).
- [Helm](https://helm.sh/) 3 and [curl](https://curl.se/) on the same
  machine, and a checkout of this repository:

  ```bash
  git clone https://github.com/elixir-cloud-aai/TESK.git
  cd TESK
  ```

The commands are for Bash or Zsh (not Fish, which has no here-documents or
subshells with `( )`).

## Install MicroK8s

Install MicroK8s, and let your user run it without `sudo`:

```bash
sudo snap install microk8s --classic
sudo usermod -a -G microk8s $USER
newgrp microk8s  # or log out and in again, to join the group
microk8s status --wait-ready
```

Enable the addons that TESK needs:

```bash
microk8s enable dns hostpath-storage ingress
```

- `dns` resolves the names of Services inside the cluster, which the
  components of TESK and the pods of tasks rely on.
- `hostpath-storage` provides the default storage class,
  `microk8s-hostpath`, which TESK needs for the temporary volumes of tasks
  with inputs or outputs (see [Deployment](deployment.md#requirements)). It
  stores them on the node, which suits a single node.
- `ingress` runs the NGINX Ingress controller on the ports 80 and 443 of the
  node, with the Ingress class `public`.

Give Helm and `kubectl` access to the cluster through a kubeconfig file of
its own, outside the checkout and readable only by you (it holds the
credentials of the cluster's administrator), so that your other clusters stay
untouched. Do this in a terminal that you close at the end of the guide, as
`KUBECONFIG` replaces your own setting in it, and check that the node and
the storage class are ready:

```bash
mkdir -p ~/.kube
(umask 077; microk8s config > ~/.kube/microk8s-tesk)
export KUBECONFIG=~/.kube/microk8s-tesk
microk8s kubectl get nodes
microk8s kubectl get storageclass
```

Use `microk8s kubectl` where this guide says `kubectl` if you don't have
`kubectl` installed.

## Install TESK

Install the chart from the checkout, into its own namespace, with a minimal
values file (read from the standard input here) that serves the API on the
Ingress of MicroK8s without a host name or TLS:

```bash
helm upgrade --install tesk charts/tesk \
    --namespace tesk --create-namespace -f - <<'YAML'
ingress:
  rules: true
  ingressClassName: public
  # The chart's defaults ask cert-manager for a certificate, which MicroK8s
  # doesn't have; `null` removes them
  annotations: null
YAML
```

To keep the values, save the YAML in a file of your choice and pass it with
`-f <file>`.

The storage backend of the chart is `none` by default, which is enough for
tasks without inputs and outputs, and for those with `http://` and
`https://` URLs (see [Storage backends](deployment.md#storage-backends)).

Wait until the API runs. It needs about a minute to start, and until it has
started, the Ingress answers `502 Bad Gateway` (the pod shows as ready
earlier, as the chart has no readiness probe). Poll the service info until
it answers:

```bash
until curl -sf http://localhost/ga4gh/tes/v1/service-info; do sleep 5; done
```

The service info shows that the API is up. The API is served at
`http://localhost/ga4gh/tes/v1/`; from another machine, use the IP address
or name of the node instead of `localhost`.

!!! warning

    With `auth.mode: noauth` (the default), everybody who can reach the node
    can run tasks on it. Don't expose the node to the Internet this way (see
    [Authentication and authorisation](deployment.md#authentication-and-authorisation)).

## Run a task

Submit a hello-world task, which runs `echo` in an Alpine container, and
note its ID:

```bash
curl -s -X POST http://localhost/ga4gh/tes/v1/tasks \
    -H 'Content-Type: application/json' \
    -d '{"executors": [{"image": "alpine", "command": ["echo", "Hello, TESK!"]}]}'
```

The response is `{"id": "task-…"}`. Poll the task with its ID until the state
is `COMPLETE`. It goes through `QUEUED` and `RUNNING`, which takes some seconds
the first time, as the images are pulled:

```bash
curl -s http://localhost/ga4gh/tes/v1/tasks/task-XXXXXXXX
```

Then look at the output of the executor:

```bash
curl -s 'http://localhost/ga4gh/tes/v1/tasks/task-XXXXXXXX?view=FULL'
```

In the response, `logs[0].logs[0].stdout` is `Hello, TESK!`. A state of
`SYSTEM_ERROR` or `EXECUTOR_ERROR` means that something went wrong: see the
logs of the API (`kubectl logs -n tesk deploy/tesk-api`) and the pods of the
task (`kubectl get pods -n tesk`).

## Next steps

- Add an [FTP](deployment.md#ftp), [shared file
  system](deployment.md#shared-file-system) or [S3](deployment.md#s3) backend
  for tasks with inputs and outputs, and turn on authentication
  (see [Deployment](deployment.md)).
- Look up all values of the chart in [Configuration](configuration.md).

## Remove everything

Remove TESK, with the namespace of the tasks, and then MicroK8s:

```bash
helm uninstall tesk --namespace tesk
kubectl delete namespace tesk
rm ~/.kube/microk8s-tesk
sudo snap remove microk8s --purge
```

`snap remove --purge` deletes the cluster and all its data, including the
volumes of the tasks. Close the terminal in which you set `KUBECONFIG`, or
restore its previous value. To keep MicroK8s but stop it, use `microk8s stop`.
