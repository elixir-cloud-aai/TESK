## Set up Ingress external IP
-   Clone the TESK repository where you plan to install the Kubernetes CLI.
-   Find out what is the external IP for the cluster. E.g. with the command `minikube ip`
-   Edit the `external_ip` value in `deployment/ingress/config.ini` with that IP

```ini
# the following variables are specific to each deployment
external_ip=127.0.0.1
node_port=30977
```
`127.0.0.1` <-- replace this with your cluster's external ip address

## Deploy TESK
Follow the [deployment instructions for TESK](deployment.md).

## Testing
-   This will expose the API service on a port in your cluster, run `kubectl get services` to see where.
-   Send an [example TESK request](https://github.com/EMBL-EBI-TSI/TESK/blob/master/specs/examples/task_example.json), replacing `127.0.0.1:30977` with your services' ip and port:

```bash
curl -H "Content-Type: application/json" -d @specs/examples/task_example.json http://127.0.0.1:30977/v1/tasks
```
-   Watch `kubectl get pods` to see the tasks appear and complete.
