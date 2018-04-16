# TESK API

The API part of the TESK project. For a general overview of the project, please visit [TESK core project page](https://github.com/EMBL-EBI-TSI/TESK)

TESK is an implementation of [GA4GH TES](https://github.com/ga4gh/task-execution-schemas) standard for [Kubernetes](https://kubernetes.io) and TESK API exposes TES-compliant endpoints.

## Design
TESK uses Kubernetes Batch API ([Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion)) to schedule execution of a new TES task. The result of task execution is stored in and retrieved directly from Kubernetes API objects (Jobs and Pods objects); TESK currently does not use any other storage (DB) than Kubernetes itself. [Persistent Volume Claims](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims) are used as a temporary storage to handle input and output files of a task and pass it over between executors of a task and are destroyed immediately after task completion.

### Creating a new task
When API gets a request to create a new TES task, TESK performs following steps:
1. API creates a Taskmaster - a new single Kubernetes Job per task, that handles the logic of processing inputs, outputs and running task's executors in a sequence. Detailed taskmaster's job object description can be seen [here](#taskmaster-job-object).
API passes to Taskmaster a JSON object composed of - unchanged - TES Inputs/Outputs/Volumes and TES executors packaged as Kubernetes Job objects (more about [taskmaster parameters](#taskmaster-parameters)). Request finishes immediately without waiting for the task completion. Auto-generated task ID is returned as a response.
2. If any Inputs/Outputs/Volumes are present Taskmaster creates a single PVC per task.
3. Taskmaster creates Inputs Filer, yet another Kubernetes Job (one per task), adds PVC from step 2. to it and maps Input/Output/Volume directories as volume mounts pointing to subpaths of the PVC.
4. Inputs Filer downloads input files (currently supports HTTP and FTP), places them at paths inside PVC and finishes.
5. Taskmaster for each executor in a list: adds PVC as a volume, maps Inputs/Outputs/Volumes as volume mounts (the same way as for Filer), creates Kubernetes Job and waits until job's completion (by polling get job endpoint). If job fails, Taskmaster finishes. If Executor job succeeds, Taskmaster repeats all the steps for next executor in the list. Taskmaster's loop can be interrupted by cancelling a task. If Taskmaster detects task cancellation, it immediately finishes.
6. Each Executor runs actual computation and records its results in mounted PVC.
7. After successful completion of all Executors, Taskmaster creates Outputs Filer, yet another Kubernetes Job (one per task), adds PVC as its volume and maps Inputs/Ooutputs/Volumes as in previous steps.
8. Outputs Filer upload output files from PVC to external storage (currently FTP) and finishes.
9. Taskmaster deletes PVC and finishes.
### Getting task details
When API gets a request to get details of a single task or a list of tasks, than it calls Kubernetes API endpoints, to retrieve: K8s Job objects corresponding to Taskmaster, Executors and Filers (of a single task or a list of tasks) and K8s Pod objects created by those Jobs. It also gets taskmaster's and executors' pod logs. Matching API objects (Jobs and Pods) and TES tasks heavily relies on the use of K8s [labels](). After retrieving all needed objects API uses its own logic to combine them in TES task details response. 
### Cancelling a task
When API gets a request to cancel a task, it labels both Taskmaster's Job and Pod objects with cancelled status. API then uses Job label to determine task's CANCELED status. Pod's label gets populated to Downward API file, which changes Taskmaster listens to. If Taskmaster detects a change in labels, it stops an execution of a currently running  executor and finishes.

### HTTP Error Codes
TES spec does not define expected behaviour in case of errors. TESK API uses following HTTP codes:

HTTP Status Code | Meaning
------------ | -------------
200 | OK - successful request
400 | Bad request: validation error, cancellation of not running task
404 | (Task) with a given ID not found
500 | Something else (possibly configuration) went wrong

### Taskmaster job object
TODO
### Taskmaster parameters
TODO

## Tools
* TESK API is a Maven Spring Boot (currently 1.5.*) application written in Java.
* API server stub is generated automatically with Swagger Code Generator (specifically [Swagger Codegen Maven Plugin](https://github.com/swagger-api/swagger-codegen/blob/master/modules/swagger-codegen-maven-plugin)).
* Official [Kuberneres API Java Client](https://github.com/kubernetes-client/java) is used to communicate with Kubernetes API.
## Setup  
API can run both from outside and inside of Kubernetes cluster. To run API locally, run:
 
```mvn spring-boot:run```

then point your browser to [http://localhost:8080](http://localhost:8080), which should present Swagger UI page with API endpoints list.

To run from inside Kubernetes, API has to be packaged as a Docker image. Dockerfile is available [here](/Dockerfile).
Current version of the image is hosted at GCR: `eu.gcr.io/tes-wes/tesk-api:v0.2`
 
Deployment descriptors for different K8s environments reside in [TESK core project](https://github.com/EMBL-EBI-TSI/TESK/tree/master/deployment) and description of how to install TESK at Kubernetes (including API) also lives [there](https://github.com/EMBL-EBI-TSI/TESK/blob/master/documentation/deployment.md). Detailed explanation of TESK API deployment parameters [below](#deployment-parameters)

Authentication and authorisation at Kubernetes API are done by Kubernetes API Client (not well documented, refer to [source code](https://github.com/kubernetes-client/java/blob/master/util/src/main/java/io/kubernetes/client/util/Config.java) instead). When running API outside of Kubernetes, we used KUBECONFIG file succesfully. When run from within the cluster, service account is used. In both cases (in/external) API needs to run with permissions sufficient to create and query Jobs and Pods. We used built-in `admin` and `edit` roles successfully, more refined roles are on the way.   

### Deployment parameters
TODO
### Generating new API version stub
TODO



      
     
      

    
