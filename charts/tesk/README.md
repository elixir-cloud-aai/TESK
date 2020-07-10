# Deployment instructions for TESK

Helm chart and config to deploy the TESK service. Tested with Helm v3.0.0.

## Usage

First you must create a namespace in Kubernetes in which to deploy TESK. The
command below creates all deployments in the context of this namespace. How
the namespace is created depends on the cluster, so it is not documented here.

To deploy the application:
 * modify [`values.yaml`](values.yaml)
 * Create a `secrets.yaml` file. You need to fill up the `username` and `password` of the ftp server configured in WES. If you activated authentication (auth.mode == 'auth' in `values.yaml`), optionally you may activate as well he OICD client. To do so, supply the `client_id` and `client_secret` values, otherwise the auth section must be removed. This is independent of the fact that after activating auth mode, TESK will require a valid TOKEN:

 ```
 ftp:
   username: <username>
   password: <password>

 auth:
   client_id: <client_id>
   client_secret: <client_secret>
 ```

 * finaly execute:

```bash
$ helm upgrade --install tesk-release . -f secrets.yaml -f values.yaml
```

then you can check it all went as expected:

```bash
$ helm list -n tesk
NAME	        NAMESPACE  REVISION	UPDATED                                 	STATUS  	CHART     	APP VERSION
tesk-release	tesk	     16      	2020-05-14 11:38:45.521995325 +0300 EEST	deployed	tesk-0.1.0	dev
```

The first time running this command, the chart will be installed. Afterwards, it will apply any change in the chart.

*IMPORTANT:* In kubernetes, if you want to install TESK in a namespace different than `default`, it must be specified by using `-n <namespace>`, so the final command would be something like this:

```bash
$ helm upgrade -n tesk --install tesk-release . -f secrets.yaml -f values.yaml
```

##  Description of values

See [`values.yaml`](values.yaml) for default values.

| Key | Type | Description |
| --- | --- | --- |
| host_name | string | FQDN to expose the application |
| clusterType | string |type of Kubernetes cluster; either 'kubernetes' or 'openshift'|
| wes-tes_enabled | boolean | Enables the wes-tes deployment. |
| tesk.image | string | container image to be used to run TESK |
| tesk.port | integer | |
| tesk.taskmaster_image_version | string | |
| tesk.taskmaster_filer_image_version | string | |
| tesk.debug | boolean | Activates the debugging mode |
| transfer.wes_base_path | string | WesElixir locally Change the value of $wesBasePath in minikubeStart accordingly |
| transfer.tes_base_path | string | |
| transfer.pvc_name | string | |
| auth.mode | string | Can be 'noauth' to disable authentication, or 'auth' to enable it |
| auth.env_subgroup | string | Can be 'EBI' or 'CSC' |
| service.type | string | Can be 'NodePort' or 'ClusterIp' |
| service.node_port | integer | Only used if service.type is 'NodePort', specifies the port |
| ftp.active | boolean | Activates or disables the local ftp |
| ftp.virtualboxip | string | IP for the endpoint of the ftp |
| ftp.username | string | Username of the ftp server |
| ftp.password | string | Password of the ftp server |
| kubernetes.nginx_image | string | Image to use for the nginx ingress |
| kubernetes.external_ip | string | We used externalIP to expose Ingress on 80/443 port. On OpenStack internal IP of masternode (10.x.x.x) worked for us. Could be any node, but calls to the service have to be using it. In our case DNS entry is assigned to master's external IP. Use NodePort as an alternative.|
| kubernetes.node_port | integer | |
| kubernetes.tls_secret_name | string |  If no TLS secret name configured, TLS will be switched off. A template can be found at [deployment/tls_secret_name.yml-TEMPLATE](deployment/tls_secret_name.yml-TEMPLATE). |
| kubernetes.scope | string | The following variables are specific to each deployment. Use "Cluster" if you want Ingress to listen to all namespaces (requires ClusterAdmin). Leave it blank if you want Ingress to listen only to its own namespace. |

