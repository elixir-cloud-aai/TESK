[![codecov](https://codecov.io/gh/elixir-cloud-aai/TESK/branch/main/graph/badge.svg)](https://codecov.io/gh/elixir-cloud-aai/TESK)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-311/)
[![Development Status](https://img.shields.io/badge/status-beta-yellow.svg)](https://github.com/elixir-cloud-aai/TESK)
[![GitHub contributors](https://img.shields.io/github/contributors/elixir-cloud-aai/TESK)](https://github.com/elixir-cloud-aai/TESK/graphs/contributors)
[![Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://bandit.readthedocs.io/en/latest/)
[![Safety](https://img.shields.io/badge/security-safety-orange.svg)](https://safetycli.com/product/safety-cli)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

<img src="/images/TESKlogowfont.png" height="200">

An implementation of a task execution engine based on the [TES standard](https://github.com/ga4gh/task-execution-schemas) running on `Kubernetes`. For more details on `TES`, see the (very) brief [introduction to TES](/docs/documentation/tesintro.md).

For organisational reasons, this project is split into 3 repositories:

- This one, which contains documentation and deployment files
- [tesk-api](https://github.com/elixir-cloud-aai/tesk-api): Contains the service that implements the TES API and translates tasks into kubernetes batch calls
- [tesk-core](https://github.com/elixir-cloud-aai/tesk-core): Contains the code that is launched as images into the kubernetes cluster by tesk-api.

If the API is running on your cluster it will pull the images from our `docker.io` repository automatically.

`TESK` is designed with the goal to support any `Kubernetes` cluster, for its deployment please refer to the [deployment](/docs/documentation/deployment.md) page.

The technical documentation is available in the [documentation](/docs/documentation) folder.

## Architecture

<!-- TODO: Change the image remove tomcat, change naming etc -->

**Description**: The first pod in the task lifecycle is the API pod, a pod which runs a web server (`Tomcat`) and exposes the `TES` specified endpoints. It consumes `TES` requests, validates them and translates them to `Kubernetes` jobs. The API pod then creates a `task controller` pod, or `taskmaster`.

The `taskmaster` consumes the executor jobs, inputs and outputs. It first creates `filer` pod, which creates a persistent volume claim (PVC) to mount as scratch space. All mounts are initialized and all files are downloaded into the locations specified in the TES request; the populated PVC can then be used by each executor pod one after the other. After the `filer` has finished, the taskmaster goes through the executors and executes them as pods one by one. **Note**: Each TES task has a separate taskmaster, PVC and executor pods belonging to it; the only 'singleton' pod across tasks is the API pod.

After the last executor, the `filer` is called once more to process the outputs and push them to remote locations from the PVC. The PVC is the scrubbed, deleted and the taskmaster ends, completing the task.

## Requirements

- A working [Kubernetes](https://kubernetes.io/) cluster version 1.9 and later.
- If you want TESK to handle tasks with I/O (and you probably want), you additionally need:
- A default storage class, which TESK will use to create temporary PVCs. It is enough that the storage class supports the RWO mode.
- And, if you want TESK to integrate with workflow managers, you additionally need either an FTP account or a PVC that can be accessed from within or from outside of the cluster by the workflow manager (more in the [deployment](/docs/documentation/deployment.md) page).
