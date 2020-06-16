[![Build Status](https://travis-ci.org/EMBL-EBI-TSI/tesk-core.svg?branch=master)](https://travis-ci.org/EMBL-EBI-TSI/tesk-core)
[![codecov](https://codecov.io/gh/EMBL-EBI-TSI/tesk-core/branch/master/graph/badge.svg)](https://codecov.io/gh/EMBL-EBI-TSI/tesk-core)

## Introduction

This project is part of the [TESK](https://github.com/EMBL-EBI-TSI/TESK) initiative.
It contains the code needed to generate 2 types of agents that reside in kubernetes:
* The taskmaster, which spins up the containers needed to complete tasks as defined by TESK
* The filer, which populates volumes and input files and uploads output files

## How to use

Since the code is meant to be in kubernetes pods, the code needs to be packaged into containers.
Their descriptions can be found in `containers/`.
The root folder assumed to build the containers is the root of this package.

## Unit testing

Unit testing needs the `tox` package.
This software will take care of creating virtual environments and installing dependencies in them before running the actual tests and generating the coverage reports.

```
$ tox
```
