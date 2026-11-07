# TESK Helm chart

Helm chart that deploys [TESK](https://github.com/elixir-cloud-aai/TESK), the
GA4GH Task Execution Service on Kubernetes.

The documentation is on [Read the Docs](https://tesk.readthedocs.io/):

- [Deployment](https://tesk.readthedocs.io/en/latest/deployment/): requirements
  (including the tested Kubernetes versions), installation, exposing the API,
  storage backends and authentication.
- [Configuration](https://tesk.readthedocs.io/en/latest/configuration/): all
  values of this chart, the service info, and the files and secrets it reads.
- [Upgrading](https://tesk.readthedocs.io/en/latest/upgrading/): changes that
  affect existing deployments (e.g., the names of the objects derive from
  the release name, so releases of earlier charts must be installed again;
  since taskmaster v0.10.6, a task that uses more memory than it requested
  is killed).

The default values are in [`values.yaml`](values.yaml). In short, from a
checkout of the repository:

```bash
helm upgrade --install tesk charts/tesk \
    --namespace tesk --create-namespace \
    -f my-values.yaml
```
