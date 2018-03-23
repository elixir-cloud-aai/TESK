# Set up for OpenShift

The following instructions will be declined for the OpenShift __PopUp__ cluster, provided by [CSC](https://www.csc.fi).  
Nevertheless, they can be applied to any other OpenShift provider, simply replacing the provider-specific links.

## Requirements:

### OpenShift client

[https://github.com/openshift/origin/releases](https://github.com/openshift/origin/releases)

Form Mac users:

```
brew install openshift-cli
```
————————————————————————————————————————————————————————

#### Tip: manage multiple Kubernetes - Openshift Contexts

Switching `kubectl`/`oc` between contexts.

-   List all the local contexts:

```
kubectl config get-contexts
```

-   Switch the context:

```
kubectl config use-context CONTEXT_NAME
```

### CSC links:

In order to connect to the __CSC OpenShift cluster__ (`c01 popup cluster container cloud`) it is required to be part the `c01-k8s-popup` GitHub organization:  
[https://github.com/c01-k8s-popup](https://github.com/c01-k8s-popup)

CSI is the owner of the organization and can add new members to it.  
Once your GitHub user is part of the organization, you can access the Openshift console:  
[https://c01.k8s-popup.csc.fi:8443/console/](https://c01.k8s-popup.csc.fi:8443/console/)

Official documentation for `c01 popup cluster container cloud`:  
[https://c01.k8s-popup.csc.fi](https://c01.k8s-popup.csc.fi)


## Get an OpenShift token

-   From the top left `?` icon, open the: `Command Line Tools` page and just press on the first clipboard icon, to copy to your clipboard the command, that you have to run in your terminal.

-   Login to OpenShift (with an example token):

```
oc login https://c01.k8s-popup.csc.fi:8443 --token=abcefghijk
```

## Create an OpenShift Project

-   Create a new OpenShift Project

```
oc new-project "tesk-demo"  --description="TESK an implementation of GA4GH TES protocol using Kubernetes, by EMBL-EBI"   --display-name="TESK"
```

## Deploy Tesk

Follow the [deployment instructions for TESK](deployment.md).

Your service will be available at:

[https://tesk-api.c01.k8s-popup.csc.fi/](https://tesk-api.c01.k8s-popup.csc.fi/)

_https://`[openshift.namespace]`/`[openshift.host]`/_

## OpenShift Policy requirements

Please have a read to the [openshift policy](openshift_policy.md) and check that your OpenStack fulfill the requirements about the service account policy.

