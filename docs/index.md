[![ELIXIR On-Cloud](images/logo_elixir_on_cloud.png)](https://elixir-on.cloud/)

# TESK

TESK is an implementation of the [GA4GH Task Execution Service
(TES)](https://github.com/ga4gh/task-execution-schemas) API on
[Kubernetes](https://kubernetes.io/). Each TES task runs as Kubernetes jobs
in one namespace, with its inputs and outputs staged in a temporary volume.
TESK is deployed with a Helm chart and needs no other services.

TESK is made of three repositories:

- [TESK](https://github.com/elixir-cloud-aai/TESK): the Helm chart that
  deploys TESK, and this documentation.
- [tesk-api](https://github.com/elixir-cloud-aai/tesk-api): the service that
  implements the TES API and turns tasks into Kubernetes jobs.
- [tesk-core](https://github.com/elixir-cloud-aai/tesk-core): the taskmaster,
  which runs the jobs of a task, and the filer, which stages its inputs and
  outputs.

## Contents

- [Introduction to TES](tesintro.md): what a TES task looks like.
- [Architecture](architecture.md): the components and the life of a task.
- [Deployment](deployment.md): install TESK with its Helm chart, expose it,
  and set up storage backends and authentication.
- [Configuration](configuration.md): all values of the chart, the service
  info and the secrets.
- [API](api.md): the endpoints and how to send tasks.
- [Upgrading](upgrading.md): changes that affect existing deployments.
- Guides: [Integration with WES](integrated_wes_tes.md) (TESK next to a
  workflow engine in the same cluster) and [Local FTP
  server](local_ftp.md) (an FTP server on the host of a development
  cluster).
- [tesk-api](tesk-api/index.md) and [tesk-core](tesk-core/index.md): the docs
  of these components, from their repositories.
- [Development](development.md): development setup, checks, the
  documentation and releases.

## License

This project is covered by the [Apache License
2.0](https://www.apache.org/licenses/LICENSE-2.0) also [shipped with this
repository](https://github.com/elixir-cloud-aai/TESK/blob/dev/LICENSE).

## Contact

The project is a collaborative effort under the umbrella of [ELIXIR
On-Cloud](https://elixir-on.cloud/). Follow the link to get in touch with us
via chat or email. Please mention the name of this service for any inquiry,
proposal, question etc.
