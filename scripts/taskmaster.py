#!/usr/bin/python
import argparse
import json
import os
import re
import time
import sys
from kubernetes import client, config

# translates TES JSON into 1 Job spec for each executor
def generate_job_specs( file ):
  tes = json.load(file)
  exe_i = 0
  specs = []

  for executor in tes['executors']:
    valid_name = tes['name']
    valid_name = valid_name.lower()
    valid_name = re.sub(r" ", "-", valid_name)
    
    specs[exe_i] = {'apiVersion': 'batch/v1', 'kind': 'Job'}
    specs[exe_i]['metadata'] = {'name': valid_name}

    specs[exe_i]['spec'] = {'template': 0}
    specs[exe_i]['spec']['template'] = { 'metadata' : 0, 'spec': 0}
    
    specs[exe_i]['spec']['template']['metadata'] = {'name': valid_name}

    specs[exe_i]['spec']['template']['spec'] = { 'containers': 0, 'restartPolicy': 'Never'}

    specs[exe_i]['spec']['template']['spec']['containers'] = []

    specs[exe_i]['spec']['template']['spec']['containers'] = []
    specs[exe_i]['spec']['template']['spec']['containers'].append({ 
                                                         'name': valid_name+'-ex'+str(exe_i),
                                                         'image': executor['image_name'], 
                                                         'command': executor['cmd'],
                                                         'resources': {'requests': 0 }
                                                        })
    specs[exe_i]['spec']['template']['spec']['containers'][0]['resources']['requests'] = { 
                                                           'cpu': tes['resources']['cpu_cores'], 
                                                           'memory': str(tes['resources']['ram_gb'])+'Gi'}
  return specs

def run_executors(specs):

  # init Kubernetes Job API
  v1 = client.BatchV1Api()

  for executor in specs:
    job = v1.create_namespaced_job(body=executor, namespace="default")
    print("Created job with status='%s'" % str(job.status))
    finished = False

    # Job polling loop
    while not finished:
      try:
        if job.status.conditions[0].type == 'Complete' and job.status.conditions[0].status:
          finished = True
        if job.status.conditions[0].type == 'Failed' and job.status.conditions[0].status:
          finished = True
          return 'Failed' # If an executor failed we break out of running the executors
        else:
          return 'Failed' # something we don't know happened, fail
      except TypeError: # The condition is not initialized, so it is not complete yet, wait for it
        time.sleep(polling_interval)

  return 'Complete' # No failures, so return successful finish

def main(argv):
  parser = argparse.ArgumentParser(description='TaskMaster main module')
  parser.add_argument('file', help='file containing TES JSON request')
  config_def = os.path.join(os.environ["HOME"], '.kube/config')
  parser.add_argument('-c', '--config', help='kubernetes connection configuration', default=config_def)
  parser.add_argument('-p', '--polling-interval', help='Job polling interval', default=5)
  args = parser.parse_args()

  specs = generate_job_specs(args.file)
  
  config.load_kube_config(config)

  state = run_executors(specs, polling_interval)
  print("Finished with state %s" % state)

if __name__ == "__main__":
  main(sys.argv)
