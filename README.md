<!-- markdownlint-disable MD033 MD041 -- logo first; <picture> for dark mode -->
<a href="https://elixir-on.cloud/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/logo_elixir_on_cloud_night.png">
    <img src="docs/images/logo_elixir_on_cloud.png" alt="ELIXIR On-Cloud">
  </picture>
</a>
<!-- markdownlint-enable MD033 MD041 -->

# TESK

[![License][badge-license]][badge-url-license]
[![Build_status][badge-build-status]][badge-url-build-status]
[![Docs][badge-docs]][badge-url-docs]
[![Coverage][badge-coverage]][badge-url-coverage]

An implementation of the [GA4GH Task Execution Service (TES)
API](https://github.com/ga4gh/task-execution-schemas) on
[Kubernetes](https://kubernetes.io/), brought to you by [ELIXIR
On-Cloud](https://elixir-on.cloud/). Workflow engines and Workflow Execution
Service (WES) implementations send it tasks: one or more containers that run
one after the other, with inputs and outputs. TESK runs each task as
Kubernetes jobs in one namespace, staging inputs and outputs in a temporary
volume, and needs no database or other services of its own; where inputs
come from and outputs go to (HTTP(S), FTP, S3 or a shared file system)
depends on the storage that a deployment configures. It is deployed with a
Helm chart.

TESK is made of three repositories:

- **TESK** (this one): the Helm chart in [`charts/tesk/`][chart] and the
  documentation.
- [tesk-api](https://github.com/elixir-cloud-aai/tesk-api): the service that
  implements the TES API and turns tasks into Kubernetes jobs.
- [tesk-core](https://github.com/elixir-cloud-aai/tesk-core): the taskmaster,
  which runs the jobs of a task, and the filer, which stages its inputs and
  outputs.

**Read the [documentation][docs]** for the architecture, the deployment with
the Helm chart, its configuration, the API, upgrades and development.

## Quick start

With a Kubernetes cluster with a default storage class, and
[Helm](https://helm.sh/docs/intro/install/) 3 installed:

```bash
git clone https://github.com/elixir-cloud-aai/TESK.git
cd TESK
helm install tesk charts/tesk --namespace tesk --create-namespace
```

The API is then served by the service `tesk-api` in namespace `tesk`, without
authentication (the chart's default), so anyone who can reach the service can
run tasks: use this on a cluster that only you use, and enable
authentication on shared clusters. See [Deployment][docs-deployment] for
exposing the API, storage backends and authentication.

## Citation

The citation metadata is in [`CITATION.cff`](CITATION.cff): on GitHub, "Cite
this repository" in the sidebar of the repository formats it as APA or
BibTeX.

## Contributing

Contributions are welcome! See [Development][docs-development] in the
documentation and the organisation's [contributing guide][contributing], and
mind our [code of conduct][code-of-conduct].

## License

This project is covered by the [Apache License 2.0][badge-url-license], also
[shipped with this repository](LICENSE).

[badge-build-status]: <https://github.com/elixir-cloud-aai/TESK/actions/workflows/ci.yml/badge.svg?branch=dev>
[badge-coverage]: <https://codecov.io/gh/elixir-cloud-aai/TESK/branch/dev/graph/badge.svg?branch=dev>
[badge-docs]: <https://img.shields.io/readthedocs/tesk>
[badge-license]: <https://img.shields.io/badge/license-Apache%202.0-blue.svg>
[badge-url-build-status]: <https://github.com/elixir-cloud-aai/TESK/actions/workflows/ci.yml?query=branch%3Adev>
[badge-url-coverage]: <https://codecov.io/gh/elixir-cloud-aai/TESK?branch=dev>
[badge-url-docs]: <https://tesk.readthedocs.io/en/latest/>
[badge-url-license]: <https://www.apache.org/licenses/LICENSE-2.0>
[chart]: charts/tesk/
[code-of-conduct]: <https://github.com/elixir-cloud-aai/.github/blob/main/CODE_OF_CONDUCT.md>
[contributing]: <https://github.com/elixir-cloud-aai/.github/blob/main/CONTRIBUTING.md>
[docs]: <https://tesk.readthedocs.io/en/latest/>
[docs-deployment]: <https://tesk.readthedocs.io/en/latest/deployment/>
[docs-development]: <https://tesk.readthedocs.io/en/latest/development/>
