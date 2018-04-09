# Deployment instructions for Tesk
The deployment of Tesk can be executed in any Kubernetes environment, with a minimal configuration required for setting up the API access point.

We provide two deployment scenario that can easily produce the static `yaml` files specific for your environment.

The templates are written using the "Jinja2" syntax and are available in the templates folder, there are two versions, one for `OpenShift` and one for `OpenStack`, which make use of a `Nginx-ingress`.


## Compiling template

Jinja2 templates are very simple, they can be edit with any text editor, substituting the variables with the syntax `{{ variable }}` with the appropriate `value`, or used in combination with python or other languages.

The simplest way to compile the template is to make use of a Jinja2 Command Line Tool, you can find more information of the suggested one here:
[shinto-cli](https://github.com/istrategylabs/shinto-cli)


Chose the type of deployment:
```
cd deployment/openshift
```

or:

```
cd deployment/ingress
```

Edit the `config.ini` file, setting up the few variables specific to your deployment.  
In general, the only variables that have to be edited are just the fields that follow the comment:  
`# the following variables are specific to each deployment`.

Compile the `yaml` file using the following command:

```
j2 -g "*.j2" config.ini
```

It will produce a set of file, one for each `.j2` file, present in the local folder, customized using the values present in the `config.ini` file.


## Deploy Tesk

Once you have your status `yaml` files, deploying **Tesk** is just a single command:

```
kubectl create -f .
```

Or in the case of `OpenShift`:

```
oc create -f .
```

## Testing Tesk

### Submit a demo task

Run a `curl` console commen with a POST message:

```
 curl \
 -X POST \
 -s \
 --header 'Content-Type: application/json' \
 --header 'Accept: application/json' \
 -d @stdout.json \
 '[tesk-end-point]/v1/tasks'
```

where:

-   [`stdout.json`](https://github.com/EMBL-EBI-TSI/TESK/blob/master/examples/success/stdout.json) is a file from the `examples` folder.
-   `[tesk-end-point]` has to be replaced with an appropriate value, which can be an `hostname` or a `IP` depending on your installation (i.e. `http://193.62.55.44` or `https://tesk-api.c01.k8s-popup.csc.fi`)

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
When a task is successfully completed, the output will contain the task id from previous step together whit the string: `"state": "COMPLETE"`

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

### Jinja2 Command Line Tool
There are many Jinja2 Command Line Tools, but we suggest this one because it provides file globbing: [shinto-cli](https://github.com/istrategylabs/shinto-cli)

```
pip install shinto-cli
```

### OpenShift client
This is a requirement only if you use OpenShift: [https://github.com/openshift/origin/releases](https://github.com/openshift/origin/releases)

Form Mac users:

```
brew install openshift-cli
```
