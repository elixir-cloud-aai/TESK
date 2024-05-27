# Deployment of TESK integrated with WES-ELIXIR

In this scenario TESK and a workflow engine are deployed together in one K8s cluster and exchange input/output/intermediate files via shared file system and not FTP. In this setting TESK is an internal service and is not exposed at a boundary of the system.

## Deployment descriptors

Example deployment descriptors for the use case reside in [wes-tes directory](/deployment/wes-tes).

### RWX PVC

WES and TESK exchange files over ReadWriteMany PVC. [An example descriptor](/deployment/wes-tes/userstorage/rwx-pvc.yaml) assumes the existence of a default storage class supporting Read Write Many PVCs.

### WES

The workflow engine that was used is [this fork](https://github.com/EMBL-EBI-TSI/WES-ELIXIR/tree/dev) of [WES-ELIXIR](https://github.com/elixir-europe/WES-ELIXIR) adapted for the use case. It consists of 2 services: [API](/deployment/wes-tes/wes/wes-elixir-deployment.yaml) - exposed externally via Ingress definition and [a celery worker](/deployment/wes-tes/wes/wes-celery-deployment.yaml). Both use the same image. WES-ELIXIR has a requirement of MongoDB and RabbitMQ. In the example we assumed both are available, under `mongo` and `rabbitmq` URLs accordingly. We deployed both inside the same cluster, but that is not a requirement.

### TES

TESK is an internal service in this scenario. Newly introduced environment variables describe, how the shared PVC is visible to different components of the system:
* `TESK_API_TASKMASTER_ENVIRONMENT_HOST_BASE_PATH` - the path, where the shared PVC is mounted at WES side
* `TESK_API_TASKMASTER_ENVIRONMENT_CONTAINER_BASE_PATH` - the path, where the shared PVC will be dynamically mounted in filer containers.
* `TESK_API_TASKMASTER_ENVIRONMENT_TRANSFER_PVC_NAME` - the name of the shared PVC.

In this use case - as usually - TESK requires a dynamic storage class (not necessarily the same that was used for producing shared storage, but we assumed so).

### User and Site storage

In our PoC [Caddy](https://caddyserver.com) server plays a role of both user and site storage. We used [this image](https://github.com/abiosoft/caddy-docker) with an additional [upload plugin](https://github.com/wmark/http.upload). When used as a [User Workspace](/deployment/wes-tes/userstorage/userworkspace.yaml) Caddy is exposed externally via Ingress, serves files from the shared storage and lets users upload files therein. When used as [Site Storage](/deployment/wes-tes/sitestorage/sitestorage.yaml), it has a separate file storage attached and the service is visible only internally.

