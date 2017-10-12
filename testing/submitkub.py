import os
import json
from kubernetes import client, config

config.load_kube_config(
    os.path.join(os.environ["HOME"], '.kube/config'))

v1 = client.BatchV1Api()

with open("/tmp/jobs.json") as f:
  dep = json.load(f)
  resp = v1.create_namespaced_job(body=dep, namespace="default")
  print("Job created. status='%s'" % str(resp.status))
