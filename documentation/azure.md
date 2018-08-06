# Quick Azure Kubernetes setup

## Install a the azure cli and login

On Mac OS:

```
brew update && brew install azure-cli
```

Login to you your Microsoft Azure account:

```
az login
```

## Create a resource group

An Azure resource group is a logical group in which Azure resources are deployed and managed. We will create a specific one for TESK specifying the Azure location.

```
az group create --name TESKCluster --location uksouth
```


## Create a Azure Kubernetes Service

Creates a Kubernetes cluster named TESKCluster with one node.

```
az aks create --resource-group TESKCluster --name  TESKCluster --node-count 1 --enable-addons monitoring --generate-ssh-keys
```

Take a coffee while you wait that the command returns the JSON-formatted information about the cluster!  
Now I can follow the [common TESK deployment documentation](deployment.md).

### Note
Azure support the `LoadBalancer` functionality, you can choose it as the `service`.`type` in the `config.ini` file.

## Delete cluster
When the cluster is no longer needed, use the `az group delete` command to remove the resource group, container service, and all related resources.

```
az group delete --name TESKCluster --yes --no-wait
```

### Note

When you delete the cluster, the Azure Active Directory service principal used by the AKS cluster is not removed. For steps on how to remove the service principal, see [AKS service principal considerations and deletion.](https://docs.microsoft.com/en-us/azure/aks/kubernetes-service-principal#additional-considerations)


Based on official [Microsoft Azure documentation](https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough)
