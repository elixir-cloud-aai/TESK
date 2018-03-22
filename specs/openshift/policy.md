Current version of OpenShift deployment uses 2 built in service accounts:
1) `default` - used by filer containers and executor containers.
2) `deployer` - used by taskmaster and API.

Role binding (`oc get rolebinding`):
*   `default` account runs with default role binding.
*   `deployer` account has additional role binding: built-in `edit` role - gives access to many Kube API endpoints.

SCC (`oc get scc anyuid -o json`):
*   Both `deployer` and `default` have been assigned built-in scc `anyuid` - to be able to run containers with root.

Improvements:
1) Replace built in `deployer` service account with a new one, with a more descriptive name (taskmaster?).
2) Create local role that has less extensive list of privileges, than edit (use `oc get clusterrole edit -o json` as an example)
3) Bind 1. with 2.
