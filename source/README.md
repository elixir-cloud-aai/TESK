## Introduction

This project is part of the [TESK](https://github.com/EMBL-EBI-TSI/TESK) initiative.
It contains the Dockerfiles needed to generate 2 types of agents that reside in kubernetes:
* The taskmaster, which spins up the containers needed to complete tasks as defined by TESK
* The filer, which populates volumes and input files and uploads output files

## How to use

You can easily build the two types of agents

To build the taskmaster container, run:

```
docker build . -f taskmaster.Dockerfile -t taskmaster:latest
```

The command is similar for the filer container:

```
docker build . -f filer.Dockerfile -t filer:latest
```

> [!NOTE]  
> The file [setup.py](https://github.com/elixir-cloud-aai/tesk-core/blob/4dd5c6ab10eac3d7ecc8834c93128137d77b3550/setup.py#L78) in [tesk-core](https://github.com/elixir-cloud-aai/tesk-core) uses `setuptools_scm` to calculate the project version from Git tags.  
> When building Docker images, we need the repository tesk-core to include the `.git/` folder.  
> The two Dockerfiles have an instruction that will clone the repository in order to build the images

## More information

For more information about the source code, please refer to the [tesk-core repository](https://github.com/elixir-cloud-aai/tesk-core)