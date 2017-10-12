import os
from kubernetes import client, config

config.load_kube_config(
    os.path.join(os.environ["HOME"], '.kube/config'))

v1 = client.BatchV1Api()

print ("name\tactive\tfailed\tsucceeded\tmsg")
job_list = v1.list_namespaced_job("default")
for job in job_list.items:
    try:
      print("%s\t%s\t%s\t%s\t%s\t%s" % (job.metadata.name, 
                                  job.status.active,
                                  job.status.failed,
                                  #job.status.succeeded))
                                  job.status.succeeded,
                                  job.status.conditions[0].type,
                                  job.status.conditions[0].status))
    except TypeError:
      print("%s\t%s\t%s\t%s\t%s" % (job.metadata.name, 
                                  job.status.active,
                                  job.status.failed,
                                  #job.status.succeeded))
                                  job.status.succeeded,
                                  "Not completed"))
