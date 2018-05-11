Current version of OpenShift deployment uses 2 built in service accounts:

1.  `default` - used by filer containers and executor containers.
2.  `deployer` - used by taskmaster and API.

Role binding (`oc get rolebinding`):

*   `default` account runs with default role binding.
*   `deployer` account has additional role binding: built-in `edit` role - gives access to many Kube API endpoints.
```
oc adm policy add-role-to-user edit -z deployer
```

SCC (`oc get scc anyuid -o json`):

*   Both `deployer` and `default` have been assigned built-in scc `anyuid` - to be able to run containers with root. Apparently a user have to have `cluster-admin` role to perform the commands below:
```
oc adm policy add-scc-to-user anyuid -z deployer
oc adm policy add-scc-to-user anyuid -z default
```

Improvements:

1.  Replace built in `deployer` service account with a new one, with a more descriptive name (taskmaster?).
2.  Create local role that has less extensive list of privileges, than edit (use `oc get clusterrole edit -o json` as an example)
3.  Bind `1.` with `2.`
4.  Explore replacing OS roles with K8s  `rbac.authorization.k8s.io/v1beta1` 
