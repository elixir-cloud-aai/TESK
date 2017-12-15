#!/usr/bin/python

from __future__ import print_function
import argparse
import json
import os
import binascii
import re
import time
import sys
from kubernetes import client, config
from datetime import datetime

debug = False

# translates TES JSON into 1 Job spec per executor
def generate_job_specs(tes):
  exe_i = 0
  specs = []

  for executor in tes['executors']:
    valid_name = tes['name']
    valid_name = valid_name.lower()
    valid_name = re.sub(r" ", "-", valid_name)
    
    specs.append({'apiVersion': 'batch/v1', 'kind': 'Job'})
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
    
    exe_i += 1
  return specs

def run_executors(specs, polling_interval, namespace):

  # init Kubernetes Job API
  v1 = client.BatchV1Api()

  for executor in specs:
    jobname = executor['metadata']['name']
    #executor['metadata']['name'] = jobname
    job = v1.create_namespaced_job(body=executor, namespace=namespace)
    print("Created job with metadata='%s'" % str(job.metadata))
    finished = False

    # Job polling loop
    while not finished:
      job = v1.read_namespaced_job(jobname, namespace)
      try:
        #print("job.status.conditions[0].type: %s" % job.status.conditions[0].type)
        if job.status.conditions[0].type == 'Complete' and job.status.conditions[0].status:
          finished = True
        elif job.status.conditions[0].type == 'Failed' and job.status.conditions[0].status:
          finished = True
          return 'Failed' # If an executor failed we break out of running the executors
        else:
          #print("hit else, failing")
          return 'Failed' # something we don't know happened, fail
      except TypeError: # The condition is not initialized, so it is not complete yet, wait for it
        time.sleep(polling_interval)

  return 'Complete' # No failures, so return successful finish

def create_pvc(data, namespace):
  task_name = data['executors'][0]['metadata']['labels']['taskmaster-name']
  pvc_name = task_name + '-pvc'
  size = data['resources']['disk_gb']

  pvc = { 'apiVersion': 'v1',
          'kind': 'PersistentVolumeClaim',
          'metadata': { 'name': pvc_name },
          'spec': {
            'accessModes': [ 'ReadWriteOnce'],
            'resources': { 'requests' : { 'storage': str(size)+'Gi' } },
            'storageClassName': 'gold'
          }
        }

  cv1 = client.CoreV1Api()
  cv1.create_namespaced_persistent_volume_claim(namespace, pvc)
  return pvc_name

def get_filer_template(filer_version):
  filer = {
              "kind": "Job",
              "apiVersion": "batch/v1",
              "metadata": { "name": "tesk-filer" },
              "spec": {
                "template": {
                  "metadata": { "name": "tesk-filer" },
                  "spec": {
                    "containers": [ {
                        "name": "filer",
                        "image": "eu.gcr.io/tes-wes/filer:"+filer_version,
                        "args": [],
                        "env": [],
                        "volumeMounts": []
                      }
                    ],
                    "volumes": [],
                    "restartPolicy": "Never"
                  }
                }
              }
            }
  return filer
  
def populate_pvc(data, namespace, pvc_name, filer_version):
  volume_mounts = []
  volume_name = 'task-volume'
  for idx, volume in enumerate(data['volumes']):
    volume_mounts.append({"name": volume_name, "mountPath": volume })

  for idx, aninput in enumerate(data['inputs']):
    if aninput['type'] == 'FILE':
      p = re.compile('(.*)/')
      basepath = p.match(aninput['path']).group(1)
    elif aninput['type'] == 'DIRECTORY':
      basepath = aninput['path']

    volume_mounts.append({"name": volume_name, "mountPath": basepath})

  pretask = get_filer_template(filer_version)
  pretask['spec']['template']['spec']['containers'][0]['env'].append({ "name": "JSON_INPUT", "value": json.dumps(data) })
  pretask['spec']['template']['spec']['containers'][0]['args'].append("inputs")
  pretask['spec']['template']['spec']['containers'][0]['args'].append("$(JSON_INPUT)")
  pretask['spec']['template']['spec']['containers'][0]['volumeMounts'] = volume_mounts
  pretask['spec']['template']['volumes'] = [ { "name": volume_name, "persistentVolumeClaim": { "claimName": pvc_name} } ]

  print(json.dumps(pretask, indent=2), file=sys.stderr)
  
  #bv1 = client.BatchV1Api()
  #job = v1.create_namespaced_job(body=pretask, namespace=namespace)

  return volume_mounts

def cleanup_pvc(data, namespace, volume_mounts, pvc_name, filer_version):
  posttask = get_filer_template(filer_version)
  posttask['spec']['template']['spec']['containers'][0]['env'].append({ "name": "JSON_INPUT", "value": json.dumps(data) })
  posttask['spec']['template']['spec']['containers'][0]['args'].append("outputs")
  posttask['spec']['template']['spec']['containers'][0]['args'].append("$(JSON_INPUT)")
  posttask['spec']['template']['spec']['containers'][0]['volumeMounts'] = volume_mounts
  posttask['spec']['template']['volumes'] = [ { "name": "task-volume", "persistentVolumeClaim": { "claimName": pvc_name} } ]

  #bv1 = client.BatchV1Api()
  #job = v1.create_namespaced_job(body=posttask, namespace=namespace)

  print(json.dumps(posttask, indent=2), file=sys.stderr)

  cv1 = client.CoreV1Api()
  cv1.delete_namespaced_persistent_volume_claim(pvc_name, namespace, client.V1DeleteOptions())

def main(argv):
  parser = argparse.ArgumentParser(description='TaskMaster main module')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('json', help='string containing json TES request, required if -f is not given', nargs='?')
  group.add_argument('-f', '--file', help='TES request as a file or \'-\' for stdin, required if json is not given')

  parser.add_argument('-p', '--polling-interval', help='Job polling interval', default=5)
  parser.add_argument('-fv', '--filer-version', help='Filer image version', default='v0.1.2')
  parser.add_argument('-n', '--namespace', help='Kubernetes namespace to run in', default='default')
  parser.add_argument('-s', '--state-file', help='State file for state.py script', default='/tmp/.teskstate')
  parser.add_argument('-d', '--debug', help='Set debug mode', action='store_true')
  args = parser.parse_args()

  debug = args.debug

  if args.file is None:
    data = json.loads(args.json)
  elif args.file == '-':
    data = json.load(sys.stdin)
  else:
    data = json.load(open(args.file))

  #specs = generate_job_specs(tes)

  if not debug:
    config.load_incluster_config()
  else:
    config.load_kube_config()

  pvc_name = create_pvc(data, args.namespace)

  volume_mounts = populate_pvc(data, args.namespace, pvc_name, args.filer_version)

  #state = run_executors(data['executors'], args.polling_interval, args.namespace)
  #print("Finished with state %s" % state)
 
  cleanup_pvc(data, args.namespace, volume_mounts, pvc_name, args.filer_version)

if __name__ == "__main__":
  main(sys.argv)
