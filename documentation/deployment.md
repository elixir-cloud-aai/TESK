# Deployment instructions for Tesk
The deployment of Tesk can be executed in any Kubernetes environment, with a minimal configuration required for setting up the API access point.

We provide templates - that can easily produce static `yaml` files - for three deployment scenarios:
- exposing Tesk service directly; should work on each environment, tested for Minikube (NodePort) and GCP (LoadBalancer)
- exposing Tesk via Ingress; should work on each environment, tested for On-Premises VMs in `OpenStack`
- exposing Tesk via OpenShift Route; will work only on `OpenShift`, recommended scenario for `OpenShift`

The templates are written using the "Jinja2" syntax and are available in `deployment` folder. For each of the scenarios you will need files from `common` subfolder. Additionally:
- exposing Tesk API service directly - only files from `common`
- exposing Tesk via Ingress - files from `common` and `ingress`
- exposing Tesk via OpenShift Route - files from `common` and `openshift`

## Compiling template

To compile the template use a Jinja2 Command Line Tool, we suggest [shinto-cli](https://github.com/istrategylabs/shinto-cli).
Go to `deployment/common` directory:
```
cd deployment/common
```
Edit the `config.ini` file, setting up the few variables specific to your deployment.  
In general, the only variables that have to be edited are just the fields that follow the comment:  
`# the following variables are specific to each deployment`. Make sure that the variable `auth.mode` is set to `noauth` as in the snippet below or absent from the `config.ini` file. This will switch off authentication via OAuth2 and make testing TESK deployment easier. You can switch on authentication later on (for more on the topic, see [Authentication and Authorisation](https://github.com/EMBL-EBI-TSI/tesk-api/blob/master/auth.md)).  
```
[auth]
# the following variables are specific to each deployment
mode=noauth
```

Compile the `yaml` file using the following command:

```
j2 -g "*.j2" config.ini
```

This will produce a set of `.yaml` files, one for each `.j2` file, present in the local folder, customized using the values present in the `config.ini` file.

If you chose Ingress or OpenShift scenario, then change directory to `deployment/ingress` or `deployment/openshift` accordingly and repeat all the above steps to obtain additional `.yaml` files. 

## Deploy Tesk

Once you have all needed `yaml` files, deploying **Tesk** is just a single command.
Change directory to `deployment/common` and run:

```
kubectl create -f .
```

or in the case of `OpenShift`:

```
oc create -f .
```
If you chose Ingress or OpenShift scenario, then change directory once again to `deployment/ingress` or `deployment/openshift` accordingly and run the same command once again:
```
kubectl create -f .
```
or for `OpenShift`
```
oc create -f .
```

## Testing Tesk

### Submit a demo task

Run a `curl` console command with a POST message:

```
 curl \
 -X POST \
 -s \
 --header 'Content-Type: application/json' \
 --header 'Accept: application/json' \
 -d @../../examples/success/stdout.json \
 '[tesk-end-point]/v1/tasks'
```

where:

-   [`stdout.json`](https://github.com/EMBL-EBI-TSI/TESK/blob/master/examples/success/stdout.json) is a file from the `examples` folder, set its path according to the local working directory.
-   `[tesk-end-point]` has to be replaced with an appropriate value, which can be an `hostname` or a `IP` depending on your installation (i.e. `http://193.62.55.44` or `https://tesk-api.c01.k8s-popup.csc.fi`) In minikube the endpoint can be obtained with the command `minikube service tesk-api --url`

This should respond with the body containing the task `id`:

```
{
  "id" : "task-123a4b56"
}
```

### Check if the task is successful

The second part of the test is to see, if task completed successfully.  
This can be achieved using a web-browser pointing to:

`[tesk-end-point]/v1/tasks`

This address offers a monitoring page for all the submitted tasks.  
When a task is successfully completed, the output will contain the task id from previous step together with the string: `"state": "COMPLETE"`

```
{
  "tasks" : [ {
    "id" : "task-123a4b56",
    "state" : "COMPLETE"
  }, {
  ...
  } ]
}
```

It can take a couple of minutes: just refresh the browser if the state is `"INITIALIZING"` or `"QUEUED"`.

## Requirements:

### OpenShift client
This is a requirement only if you use OpenShift: [https://github.com/openshift/origin/releases](https://github.com/openshift/origin/releases)

Form Mac users:

```
brew install openshift-cli
```
