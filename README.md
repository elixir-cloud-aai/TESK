# TESK
An implementation of a task execution engine based on the [TES standard](https://github.com/ga4gh/task-execution-schemas) running on Kubernetes. 

## Architecture
Details of architecture are here: https://docs.google.com/a/ebi.ac.uk/document/d/1Fjewd16qO0DvK77S-XWAQVJ4LdldBbaLgOBeDKOt62g/edit?usp=sharing.

For organisational reasons, this project is split into 2 repositories: One containing the API and associated docker images ([here](https://github.com/EMBL-EBI-TSI/tesk-api)) and one containing the actual task execution service and associated Docker images (this one). If the API is running on your cluster it will pull the images from this repository automatically, so it is not necessary to install anything from here. In that vein, see below under 'How to install' to get TESK up and running on your kubernetes.

## Requirements
 - A working Kubernetes cluster (e.g. [Minikube](https://github.com/kubernetes/minikube))

## How to install
 - First, install and run the TESK deployment: 
  ```kubectl create -f https://raw.githubusercontent.com/EMBL-EBI-TSI/TESK/master/specs/ingress/tesk-deployment.yaml```
 - Then install and run the TESK service:
```kubectl create -f https://raw.githubusercontent.com/EMBL-EBI-TSI/TESK/specs/ingress/tesk-svc.yaml```
 - This will expose the API service on a port in your cluster, run `kubectl get services` to see where.
 - Send an [example TESK request](https://github.com/EMBL-EBI-TSI/TESK/blob/master/specs/task_example.json) to the api port, and watch `kubectl get pods` to see the tasks appear and complete.
