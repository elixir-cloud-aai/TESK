## How to install (Legacy version)
-   Clone the repo to your kube-master and cd into the folder
-   Find out what is the external IP for the cluster. E.g. with the command `minikube ip`
-   Edit the following line in `specs/ingress/nginx-ingress-lb.yaml` with that IP:

```yaml
 spec:
  type: NodePort
  externalIPs:
-   127.0.0.1 <--- replace this with your cluster's external ip address

```

-   Create the services necessary to run the API:

```
kubectl create -f specs/ingress/
kubectl create -f specs/core/
```
-   This will expose the API service on a port in your cluster, run `kubectl get services` to see where.
-   Send an [example TESK request](https://github.com/EMBL-EBI-TSI/TESK/blob/master/specs/task_example.json), replacing `127.0.0.1:30977` with your services' ip and port:

```bash
curl -H "Content-Type: application/json" -d @specs/task_example.json http://127.0.0.1:30977/v1/tasks
```
-   Watch `kubectl get pods` to see the tasks appear and complete.
