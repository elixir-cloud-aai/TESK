# TESK
An implementation of a task execution engine based on the [TES standard](https://github.com/ga4gh/task-execution-schemas) running on Kubernetes. 

For organisational reasons, this project is split into 2 repositories: One containing the API and associated docker images ([here](https://github.com/EMBL-EBI-TSI/tesk-api)) and one containing the actual task execution service and associated Docker images (this one). If the API is running on your cluster it will pull the images from our gcr.io repository automatically, so it is not necessary to clone this repo in full. In that vein, see below under 'How to install' to get TESK up and running on your Kubernetes cluster.

## Requirements
 - A working Kubernetes cluster (e.g. [Minikube](https://github.com/kubernetes/minikube))

## How to install
 - First, install and run the TESK deployment: 
```
kubectl create -f https://raw.githubusercontent.com/EMBL-EBI-TSI/TESK/master/specs/ingress/tesk-deployment.yaml
```
 - Then install and run the TESK service:
```
kubectl create -f https://raw.githubusercontent.com/EMBL-EBI-TSI/TESK/master/specs/ingress/tesk-svc.yaml
```
 - This will expose the API service on a port in your cluster, run `kubectl get services` to see where.
 - Send an [example TESK request](https://github.com/EMBL-EBI-TSI/TESK/blob/master/specs/task_example.json) to the api port, and watch `kubectl get pods` to see the tasks appear and complete.
 
 ## Architecture
As a diagram:

![TESK architecture](docs/architecture.png)

Description: The main work is performed by 2 pods. First is the API pod, a pod which runs a web server (NGINX) and exposes the TES specified endpoints. It consumes TES requests, validates them and translates them to Kubernetes jobs. The API pod then creates a task controller pod, or Taskmaster. The taskmaster consumes the executor jobs, inputs and outputs. It creates Persistent Volume Claims to mount as scratch space, input / output file space and (optionally) additional mounts specified in the TES request.It then creates a pre-task job to populate PVC’s (downloading inputs). It then loops through the executor jobs, waiting for each one to complete before moving on to the next one.

