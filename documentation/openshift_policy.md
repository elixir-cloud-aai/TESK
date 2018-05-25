Service accounts, role binding and roles for TESK are now defined in `taskmaster-rbac.yaml.j2` and are common for OpenShift and other types of deployments. 
The only piece of additional setup that _might_ be still required for OpenShift is assigning `anyuid` SCC (Security Context Constraint) to `default` service account, which is used to run `filer` and `executor` jobs. Executor images - in particular - may require running with root and `anyuid` enables that.         
```
oc adm policy add-scc-to-user anyuid -z default
```
 
