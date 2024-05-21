# Deployment instructions for TESK
## Requirements
* **A Kubernetes cluster version 1.9 and later**. TESK works well in multi-tenancy clusters such as OpenShift and requires access to only one namespace.
* **A default storage class.** To handle tasks with I/O TESK always requires a default storage class (regardless of the chosen storage backend). TESK uses the class to create temporary PVCs. It should be enough that the storage supports the RWO mode.
* **A storage backend** to exchange I/O with the external world. At the moment TESK supports:
  * FTP. R/W access to a single FTP account.
  * Shared file system. This usually comes in the form of a RWX PVC.
  * S3 (WiP). R/W access to one bucket in S3-like storage

## Installing TESK
### Helm
TESK can be installed using Helm 3 (tested with v3.0.0) using [this chart](/deployment/charts/tesk). It is best to create a dedicated namespace for TESK, although for test or development clusters it is fine to use the `default` namespace.
The documentation of the chart gives a description of all configuration options and below the most common installation scenarios have been described.
TESK installation consists of a single API installed as a K8s deployment and exposed as a K8s service. Additionally, TESK API requires access to the K8s API in order to create K8s Jobs and PVCs. That is why the installation additionally creates objects such as service accounts, roles and role bindings.
The chart does not provide a way to install the default storage class and that needs to be done independently by the cluster administrator.

### Exposing TESK API
After executing the chart with the default values, TESK API will be installed, but will be accessible only inside the cluster. There is a number of options of exposing TESK externally and they depend on the type of the cluster.

#### NodePort and LoadBalancer
The most basic way of exposing TESK on self-managed clusters and a good option for development clusters such as Minikube is to use a NodePort type of service.
In the chart set the values:
```
service.type="NodePort"
## Any values in the range 30000-32767 is fine. 31567 is used as an example
service.node_port: 31567
```
After installing the chart TESK API should be accessible under the external IP of any of your cluster nodes and the node port. For minikube you can obtain the IP by running:
```
minikube ip
```
or open Swagger UI of TESK directly in the browser with:
```
minikube service tesk-api
```
You should be able to see an empty list of tasks by calling
```
http://external_IP_of_a_node:31567/v1/tasks

{
  "tasks" : [ ]
}

```
If your cluster is provided by a Cloud Provider, you may be able to use a LoadBalancer type of service. In the chart set the value:
```
service.type="LoadBalancer"
```
and consult [K8s documentation](https://kubernetes.io/docs/tasks/access-application-cluster/create-external-load-balancer/) on how to find out the IP of your TESK service.

#### OpenShift
The chart handles exposing TESK API as OpenShift Route.

TESK API should be accessible under (Swagger UI):
`https://project-name.openshift-host-name`
and
`https://project-name.openshift-host-name/v1/tasks`
should return an empty list of tasks.

#### Ingress
Recommended way of exposing any public facing API from K8s cluster such as TESK API is to use Ingress.
You need:
* an **Ingress Controller**.
* a **Hostname** - a DNS entry, where you will expose TESK. TESK can be installed at a subpath as well.
* an **Ingress Resource**, which will instruct the Controller where to expose TESK.
* A **TLS certificate** to serve TESK over https. You can obtain one from a certificate authority or automatically obtain one from [Let's Encrypt](https://letsencrypt.org/). The K8s way to do it is by installing [cert-manager](https://cert-manager.io/) and creating an ACME Issuer.
The example values for TESK Helm chart to create Ingress Resource with annotations for cert-manager, but not to install the controller:
```yaml
host_name: tes.ebi.ac.uk
ingress:
  rules: true
  ingressClassName: ""
  path: /
  # If no TLS secret name configured, TLS will be switched off
  tls_secret_name:
  # Annotations for Ingress Resource.
  annotations:
      kubernetes.io/tls-acme: "true"
      # Choose one of the following depending on your setup
      # cert-manager.io/issuer: letsencrypt-production
      cert-manager.io/cluster-issuer: letsencrypt-production
```
List of tasks should be reachable under this URL:
```
https://tes.ebi.ac.uk/v1/tasks
```

### Storage backends

#### Shared file system
TESK can exchange Inputs and Outputs with the external world using the local/shared storage. You need to create a PVC that will be reachable for your workflow manager and for TESK at the same time.
If the workflow manager (or anything else that produces paths to your inputs and outputs) is installed inside the same K8s cluster, you may use a PVC of a storage class providing RWX access and mount it to the pod where the workflow manager is installed in the directory where the manager will be creating/orchestrating inputs/outputs. Depending on the workflow manager, it may be a working directory of your workflow manager process.
If the workflow manager is installed outside of the cluster, you may be able to use a volume mounting storage visible outside of the cluster (hostPath, NFS, etc) and a PVC bound to that volume. We used Minikube with the hostPath type of storage in this secenario successfully.
Creating the shared PVC is not handled by TESK Helm chart.
Finally you have to setup following values in the chart:
```yaml
transfer:
    # If you want local file systems support (i.e. 'file:' urls in inputs and outputs),
    # you have to define these 2 properties.
    active: false

    # wes_base_path: '/data'      # WesElixir via docker-compose
    wes_base_path: '/tmp'         # WesElixir locally
                                  # Change the value of $wesBasePath in minikubeStart accordingly
    tes_base_path: '/transfer'
    pvc_name: 'transfer-pvc'  
```    

#### FTP
TESK can exchange Inputs and Outputs with the external world using an FTP account. Currently TLS is not supported in TESK, but if you plan to use TESK with cwl-tes and FTP, cwl-tes requires TLS for FTP. The solution is to enable TLS on your FTP server, but not enforce it.
In the Helm chart provide your credentials in one of 2 ways. The old way has been in TESK for a long time, but will be finally superseded by `.netrc`. Provide a name for a secret, which will store credentials (you can keep the default). An empty name switches off the creation of the old-style credentials secret.
```yaml
ftp:
    classic_ftp_secret: ftp-secret
```
and additionally provide your username and password in the `secrets.yaml`, as describe [here](/deployment/charts/tesk/README.md).

Alternatively, you can use a `.netrc` file, which will allow storing credentials for more than one FTP server.
Provide a name for a secret, which will store .netrc file:
```yaml
ftp:
    netrc_secret: ftp-secret
```
and additionally place a `.netrc` file in the folder `ftp` in the chart (the template of the file is already there).
Keeping both secret names empty switches off FTP support altogether.

#### S3
TESK can also utilize S3 object storage for exchanging Inputs & Outputs. If you have an S3 endpoint (AWS, minio, etc) that you want to use, simply add the necessary `config` and `credentials` files (see [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)) under a folder named **s3-config**. You can use the templates provided in *charts/tesk/s3-config* as a point of reference.

### Authentication and Authorisation
TESK supports OAuth2/OIDC to authorise API requests. Authentication and authorisation are optional and can be turned off completely. When turned on, TESK API expects an OIDC access token in Authorization Bearer header. TESK can be integrated with any standard OIDC provider, but the solution has been designed to support Elixir AAI in the first place and the authorisation part relies on Elixir's group model. For details, please see [Authentication and Authorisation document](https://github.com/EMBL-EBI-TSI/tesk-api/blob/master/auth.md).
To enable authentication set the following value in the chart:
```
auth:
    mode: auth
```
At the moment enabling authentication also enables authorisation. Consult [this document](https://github.com/EMBL-EBI-TSI/tesk-api/blob/master/auth.md) for details of authorisation.  
The support for authorisation configuration in the chart and its documentation is in progress.
### Additional configuration
The Helm chart has been a fairly recent addition to TESK and TESK owes its to its fantastic contributors. There might be more options that are available for configuration in TESK that have not been reflected in the chart, yet. Have a look [here](https://github.com/EMBL-EBI-TSI/tesk-api) for more configuration options.
