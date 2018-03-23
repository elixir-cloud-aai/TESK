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

Edit the `config.ini` file, setting up the few variable specific to your deployment.
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
