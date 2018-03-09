kubectl delete pvc $1-pvc
kubectl delete job $1-inputs-filer
kubectl delete job $1-outputs-filer
kubectl delete job $1-ex-00
kubectl delete job $1-ex-01
kubectl delete job $1-ex-02
kubectl delete job $1-ex-03
kubectl delete job $1
