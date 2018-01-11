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
polling_interval = 5
task_volume_name = 'task-volume'

# translates TES JSON into 1 Job spec per executor
def generate_job_specs(tes):
  specs = []
  name = re.sub(r" ", "-", tes['name'].lower())

  for executor in tes['executors']:
    descriptor = {
        'apiVersion': 'batch/v1',
        'kind': 'Job',
        'metadata': {'name': name},
        'spec': {
            'template': {
                'metadata': {'name': name},
                'spec': {
                    'restartPolicy': 'Never',
                    'containers': [{
                        'name': name + '-ex' + len(specs),
                        'image': executor['image_name'],
                        'command': executor['cmd'],
                        'resources': {
                            'requests': {
                                'cpu': tes['resources']['cpu_cores'],
                                'memory': str(tes['resources']['ram_gb']) + 'Gi'
                            }
                        }
                    }]
                }
            }
        }
    }
    specs.append(descriptor)

  return specs

def run_executors(specs, namespace, volume_mounts, pvc_name):

  # init Kubernetes Job API
  v1 = client.BatchV1Api()

  for executor in specs:
    jobname = executor['metadata']['name']
    spec = executor['spec']['template']['spec']

    spec['containers'][0]['volumeMounts'] = volume_mounts
    spec['volumes'] = [{ 'name': task_volume_name, 'persistentVolumeClaim': { 'readonly': False, 'claimName': pvc_name }}]

    job = v1.create_namespaced_job(body=executor, namespace=namespace)
    print("Created job with metadata='%s'" % str(job.metadata))
    if wait_for_job(jobname, namespace) == 'Failed':
      return 'Failed'

  return 'Complete'

def wait_for_job(jobname, namespace):
  bv1 = client.BatchV1Api()

  finished = False
  # Job polling loop
  while not finished:
    job = bv1.read_namespaced_job(jobname, namespace)
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

def get_filer_template(filer_version, name):
  filer = {
              "kind": "Job",
              "apiVersion": "batch/v1",
              "metadata": { "name": name },
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

  if os.environ.get('TESK_FTP_USERNAME') is not None:
    env = filer['spec']['template']['spec']['containers'][0]['env']
    env.append({ "name": "TESK_FTP_USERNAME", "value": os.environ['TESK_FTP_USERNAME'] })
    env.append({ "name": "TESK_FTP_PASSWORD", "value": os.environ['TESK_FTP_PASSWORD'] })

  return filer

def append_mount(volume_mounts, name, path):
  # Checks all mount paths in volume_mounts if the path given is already in there
  duplicate = next((mount for mount in volume_mounts if mount['mountPath'] == path), None)
  # If not, add mount path
  if duplicate is None:
    volume_mounts.append({ 'name': name, 'mountPath': path })

def populate_pvc(data, namespace, pvc_name, filer_version):
  volume_mounts = []
  volume_name = task_volume_name
  for idx, volume in enumerate(data['volumes']):
    append_mount(volume_mounts, volume_name, volume)

  for idx, aninput in enumerate(data['inputs']):
    if aninput['type'] == 'FILE':
      p = re.compile('(.*)/')
      basepath = p.match(aninput['path']).group(1)
    elif aninput['type'] == 'DIRECTORY':
      basepath = aninput['path']

    append_mount(volume_mounts, volume_name, basepath)

  name = data['executors'][0]['metadata']['labels']['taskmaster-name']
  pretask = get_filer_template(filer_version, name+'-inputs-filer')
  container = pretask['spec']['template']['spec']['containers'][0]
  container['env'].append({ "name": "JSON_INPUT", "value": json.dumps(data) })
  container['args'] += ["inputs", "$(JSON_INPUT)"]
  container['volumeMounts'] = volume_mounts
  pretask['spec']['template']['spec']['volumes'] = [ { "name": volume_name, "persistentVolumeClaim": { "claimName": pvc_name} } ]

  print(json.dumps(pretask, indent=2), file=sys.stderr)

  bv1 = client.BatchV1Api()
  job = bv1.create_namespaced_job(body=pretask, namespace=namespace)
  wait_for_job(pretask['metadata']['name'], namespace)

  return volume_mounts

def cleanup_pvc(data, namespace, volume_mounts, pvc_name, filer_version):
  name = data['executors'][0]['metadata']['labels']['taskmaster-name']
  posttask = get_filer_template(filer_version, name+'-outputs-filer')
  container = posttask['spec']['template']['spec']['containers'][0]
  container['env'].append({ "name": "JSON_INPUT", "value": json.dumps(data) })
  container['args'] += ["outputs", "$(JSON_INPUT)"]
  posttask['spec']['template']['spec']['containers'][0]['volumeMounts'] = volume_mounts
  posttask['spec']['template']['spec']['volumes'] = [ { "name": task_volume_name, "persistentVolumeClaim": { "claimName": pvc_name} } ]

  bv1 = client.BatchV1Api()
  job = bv1.create_namespaced_job(body=posttask, namespace=namespace)
  wait_for_job(posttask['metadata']['name'], namespace)

  print(json.dumps(posttask, indent=2), file=sys.stderr)

  cv1 = client.CoreV1Api()
  cv1.delete_namespaced_persistent_volume_claim(pvc_name, namespace, client.V1DeleteOptions())

def main(argv):
  parser = argparse.ArgumentParser(description='TaskMaster main module')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('json', help='string containing json TES request, required if -f is not given', nargs='?')
  group.add_argument('-f', '--file', help='TES request as a file or \'-\' for stdin, required if json is not given')

  parser.add_argument('-p', '--polling-interval', help='Job polling interval', default=5)
  parser.add_argument('-fv', '--filer-version', help='Filer image version', default='v0.1.5')
  parser.add_argument('-n', '--namespace', help='Kubernetes namespace to run in', default='default')
  parser.add_argument('-s', '--state-file', help='State file for state.py script', default='/tmp/.teskstate')
  parser.add_argument('-d', '--debug', help='Set debug mode', action='store_true')
  args = parser.parse_args()

  polling_interval = args.polling_interval

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

  state = run_executors(data['executors'], args.namespace, volume_mounts, pvc_name)
  print("Finished with state %s" % state)

  cleanup_pvc(data, args.namespace, volume_mounts, pvc_name, args.filer_version)

if __name__ == "__main__":
  main(sys.argv)
