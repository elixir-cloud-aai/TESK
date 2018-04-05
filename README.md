## Introduction

This project is part of the [TESK](https://github.com/EMBL-EBI-TSI/TESK) initiative.
It contains the code needed to generate 2 types of agents that reside in kubernetes:
* The task masters, which spins up the containers needed to complete tasks as defined by TESK
* The filers, which ??? [not described in the other readme]

## How to use
Since the code is meant to be in kubernetes pods, the code needs to be packaged into containers.
Their descriptions can be found in `containers/`.
The root folder assumed to build the containers is the root of this package.

## Unit testing
Unit testing needs the `tox` package, although `detox` is recommended and it parallelizes the workload:

```
  pip install detox
```

This software will take care of instancing virtual environments and installing dependencies in them before running the actual tests and generating the coverage reports

```
  detox
```
