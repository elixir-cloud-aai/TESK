[![Build Status](https://travis-ci.com/EMBL-EBI-TSI/tesk-api.svg?branch=master)](https://travis-ci.com/EMBL-EBI-TSI/tesk-api) [![codecov](https://codecov.io/gh/EMBL-EBI-TSI/tesk-api/branch/master/graph/badge.svg)](https://codecov.io/gh/EMBL-EBI-TSI/tesk-api)
# TESK API

The API part of the TESK project. For a general overview of the project, please visit [TESK core project page](https://github.com/EMBL-EBI-TSI/TESK)

TESK is an implementation of [GA4GH TES](https://github.com/ga4gh/task-execution-schemas) standard for [Kubernetes](https://kubernetes.io) and TESK API exposes TES-compliant endpoints.

## Design
TESK uses Kubernetes Batch API ([Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion)) to schedule execution of TES tasks. The result of task execution is stored in and retrieved directly from Kubernetes API objects (Jobs and Pods objects); TESK currently does not use any other storage (DB) than Kubernetes itself. [Persistent Volume Claims](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims) are used as a temporary storage to handle input and output files of a task and pass it over between executors of a task and are destroyed immediately after task completion.

### Creating a new task
When API gets a request to create a new TES task, TESK performs following steps:
1. API creates a Taskmaster - a new single Kubernetes Job per task, that handles the logic of processing inputs, outputs and running task's executors in a sequence. API passes a parameter to Taskmaster - a JSON object composed of - unchanged - TES Inputs/Outputs/Volumes and TES executors packaged as Kubernetes Job objects. Request finishes immediately without waiting for the task completion. Auto-generated task ID is returned as a response.
2. If any Inputs/Outputs/Volumes are present Taskmaster creates a single PVC per task.
3. Taskmaster creates Inputs Filer, yet another Kubernetes Job (one per task), adds PVC from step 2. to it and maps Input/Output/Volume directories as volume mounts pointing to subpaths of the PVC.
4. Inputs Filer downloads input files (currently supports HTTP and FTP), places them at paths inside PVC and finishes.
5. Taskmaster for each executor in a list: adds PVC as a volume, maps Inputs/Outputs/Volumes as volume mounts (the same way as for Filer), creates Kubernetes Job and waits until job's completion (by polling get job endpoint). If job fails, Taskmaster finishes. If Executor job succeeds, Taskmaster repeats all the steps for next executor in the list. Taskmaster's loop can be interrupted by cancelling a task. If Taskmaster detects task cancellation, it immediately finishes.
6. Each Executor runs actual computation and records its results in mounted PVC (or in stdout only).
7. After successful completion of all Executors, Taskmaster creates Outputs Filer, yet another Kubernetes Job (one per task), adds PVC as its volume and maps Inputs/Outputs/Volumes as in previous steps.
8. Outputs Filer upload output files from PVC to external storage (currently FTP) and finishes.
9. Taskmaster deletes PVC and finishes.
### Getting task details
When API gets a request to get details of a single task or a list of tasks, than it calls Kubernetes API endpoints, to retrieve: K8s Job objects corresponding to Taskmaster, Executors and Filers (of a single task or a list of tasks) and K8s Pod objects created by those Jobs. It also gets taskmaster's and executors' pod logs. Matching API objects (Jobs and Pods) and TES tasks heavily relies on the use of K8s [labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/). After retrieving all needed objects API uses its own logic to combine them in TES task details response. 
### Cancelling a task
When API gets a request to cancel a task, it labels both Taskmaster's Job and Pod objects with cancelled status. API then uses Job label to determine task's CANCELED status. Pod's label gets populated to Downward API file, which changes Taskmaster listens to. If Taskmaster detects a change in labels, it stops an execution of a currently running  executor and finishes.
### Authentication and authorisation
TESK supports OAuth2/OIDC to authorise API requests. Authentication and authorisation are optional and can be turned off completely. When turned on, TESK API expects an OIDC access token in Authorization Bearer header. TESK can be integrated with any standard OIDC provider, but the solution has been designed to support Elixir AAI in the first place and the authorisation part relies on Elixir's group model. For details, please see [Authentication and Authorisation](auth.md)
### HTTP Error Codes
TES spec does not define expected behaviour in case of errors. TESK API uses following HTTP codes:

HTTP Status Code | Meaning
------------ | -------------
200 | OK - successful request
400 | Bad request: validation error, cancellation of not running task
401 | Unauthorized - no access token in request, or the token is invalid
403 | Forbidden - user is not authorised to perform API call (usually it means, user does not belong to the required Eixir group) 
404 | (Task) with a given ID not found
500 | Something else (possibly configuration) went wrong

## Tools
* TESK API is a Maven Spring Boot (currently 2.0.1) application written in Java.
* API server stub is generated automatically with Swagger Code Generator (specifically [Swagger Codegen Maven Plugin](https://github.com/swagger-api/swagger-codegen/blob/master/modules/swagger-codegen-maven-plugin)).
* Official [Kuberneres API Java Client](https://github.com/kubernetes-client/java) is used to communicate with Kubernetes API.
## Setup  
API can run both from outside and inside of Kubernetes cluster. To run API locally, run:
 
```mvn spring-boot:run```

then point your browser to [http://localhost:8080](http://localhost:8080), which should present Swagger UI page with API endpoints list.

To run from inside Kubernetes, API has to be packaged as a Docker image. Dockerfile is available [here](/Dockerfile).
Current version of the image is hosted at GCR: `eu.gcr.io/tes-wes/tesk-api:v0.3.0.2`
 
Deployment descriptors for different K8s environments reside in [TESK core project](https://github.com/EMBL-EBI-TSI/TESK/tree/master/deployment) and description of how to install TESK at Kubernetes (including API) also lives [there](https://github.com/EMBL-EBI-TSI/TESK/blob/master/documentation/deployment.md). Detailed explanation of TESK API configuration [below](#externalized-configuration)

Authentication and authorisation at Kubernetes API are done by Kubernetes API Client (not well documented, refer to [source code](https://github.com/kubernetes-client/java/blob/master/util/src/main/java/io/kubernetes/client/util/Config.java) instead). When running API outside of Kubernetes, we used KUBECONFIG file succesfully. When run from within the cluster, service account is used. In both cases (in/external) API needs to run with permissions sufficient to create and query Jobs and Pods. We used built-in `admin` and `edit` roles successfully, more refined roles are on the way. When running from inside of the cluster, service account is defined in `spec.template.spec.serviceAccountName` parameter of [TESK API deployment file](https://github.com/EMBL-EBI-TSI/TESK/blob/master/deployment/ingress/tesk-deployment.yaml.j2)   

### Externalized Configuration
TESK API contains a set of properties listed in [application.properties](/src/main/resources/application.properties) file, that can be changed using any of the methods supported by [Spring Boot](https://docs.spring.io/spring-boot/docs/current/reference/html/boot-features-external-config.html). We usually use environment variables. When run from within the cluster, API should be deployed as K8s Deployment such as defined in [TESK Core project](https://github.com/EMBL-EBI-TSI/TESK/blob/master/deployment/ingress/tesk-deployment.yaml.j2) and environment variables can be defined there ( `spec.template.spec.containers[0].env`).
The meaning of chosen environment variables:

 Environment variable | Meaning
 ------------ | -------------
 `TESK_API_TASKMASTER_DEBUG` | If `true` will switch on more verbose logs of the taskmaster (that will appear in a TESK task FULL response). `false` by default.
 `TESK_API_TASKMASTER_SERVICE_ACCOUNT_NAME` | Service account with which each new taskmaster job will be created. Needs to have sufficient privileges granted (default `edit` role can be used). If not set, defaults to `default`.
 `TESK_API_TASKMASTER_IMAGE_NAME` | The full name of taskmaster image, the API will use, when creating new taskmaster jobs. If not set, `eu.gcr.io/tes-wes/taskmaster` will be used.
 `TESK_API_TASKMASTER_IMAGE_VERSION` | Version of taskmaster image, the API will use, when creating new taskmaster jobs. If not set, should default to stable version of taskmaster.
 `TESK_API_TASKMASTER_FILER_IMAGE_NAME` | The full name of filer image, passed on as a parameter to the taskmaster. The taskmaster will create Inputs/Outputs filers using this image. If omitted, `eu.gcr.io/tes-wes/filer` will be used.
 `TESK_API_TASKMASTER_FILER_IMAGE_VERSION` | Version of filer image, passed on as a parameter to taskmaster. Taskmaster will create Inputs/Outputs filer using the image in this version. If omitted, should default to latest stable version.
 `TESK_API_K8S_NAMESPACE` | K8s namespace, where all the Job objects will be created. If omitted, defaults to `default`.
 `TESK_API_TASKMASTER_FTP_SECRET_NAME` | Name of K8s secret storing credentials to a single FTP account. FTP account is used to demonstrate uploading output files to external storage. If ENV variable is set, FTP username and password will be included by API as taskmaster ENV variables. Otherwise (TESK_API_TASKMASTER_FTP_SECRET_NAME env variable not set), TESK should still work, but without the ability to upload files to a private FTP server.
 `TESK_API_TASKMASTER_ENVIRONMENT_*` | Variables passed through to taskmaster as environment variables (the prefix `TESK_API_TASKMASTER_ENVIRONMENT_` is stripped, so when you define `TESK_API_TASKMASTER_ENVIRONMENT_XXX`, the taskmaster will get `XXX`). Of those currently implemented in taskmaster: `TRANSFER_PVC_NAME`, `HOST_BASE_PATH`, `CONTAINER_BASE_PATH` have been used to implement TESK using shared filesystem instead of FTP to exchange inputs and outputs. `EXECUTOR_BACKOFF_LIMIT` and `FILER_BACKOFF_LIMIT` decide how many times executor/filer jobs will retry pods on error. 
 `TESK_API_TASKMASTER_EXECUTOR_SECRET_NAME` | A name of a secret that (if variable not empty) will be mounted to each executor as a volume. The secret can contain multiple files.
 `TESK_API_TASKMASTER_EXECUTOR_SECRET_MOUNT_PATH` | A path, where a secret named `TESK_API_TASKMASTER_EXECUTOR_SECRET_NAME` will be mounted. Defaults to `/secret`. 
 `SPRING_PROFILES_ACTIVE` | (default) `noauth` - authN/Z switched off. `auth` - authN/Z switched on.
 `TESK_API_AUTHORISATION_*` | A set of env variables configuring authorisation using Elixir group membership
 `TESK_API_SWAGGER_OAUTH_*` | A set of env variables configuring OAuth2/OIDC client built in Swagger UI
 
 
### Generating new API version stub
Current version of TES specification (v0.3) lives locally in the project as a [Swagger JSON file](/src/main/resources/task_execution.swagger.json). In case of the specification upgrade, this file needs to be replaced with a new version. Then you need to run

```mvn clean generate-sources -P generate-swagger```

That will generate new versions of [model](/src/main/java/uk/ac/ebi/tsc/tesk/model) and [API](/src/main/java/uk/ac/ebi/tsc/tesk/api) stub files. As project model objects contain necessary [Bean Validation](http://beanvalidation.org) annotations that need to be manually restored in auto-generated code and problematic `consumes = { "application/json" }` for GET methods need to be removed from auto-generated API interface, manual reconciliation of changes is always necessary after model regeneration.
    
