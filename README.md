# TESK
An implementation of a task execution engine based on the [TES standard](https://github.com/ga4gh/task-execution-schemas) running on Kubernetes. 

## Architecture
Details of architecture are here: https://docs.google.com/a/ebi.ac.uk/document/d/1Fjewd16qO0DvK77S-XWAQVJ4LdldBbaLgOBeDKOt62g/edit?usp=sharing

## Requirements
 - A working Kubernetes cluster (e.g. [Minikube](https://github.com/kubernetes/minikube))

## How to install
 - Download the [main API yml]() to your cluster
 - Run `kubectl create -f tesk-service.yaml`
 - This will expose the API service on a port in your cluster, run `kubectl get services` to see where.
 - Send an [example TESK request](https://github.com/EMBL-EBI-TSI/TESK/blob/master/specs/task_example.json) to the api port, and watch `kubectl get pods` to see the tasks appear and complete.
