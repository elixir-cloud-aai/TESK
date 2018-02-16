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
import logging


created_jobs = []
debug = False
polling_interval = 5
task_volume_basename = 'task-volume'

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

def run_executors(specs, namespace, volume_mounts=None, pvc_name=None):

  # init Kubernetes Job API
  v1 = client.BatchV1Api()

  for executor in specs:
    jobname = executor['metadata']['name']
    spec = executor['spec']['template']['spec']

    if volume_mounts is not None:
      spec['containers'][0]['volumeMounts'] = volume_mounts
    if pvc_name is not None:
      spec['volumes'] = [{ 'name': task_volume_basename, 'persistentVolumeClaim': { 'readonly': False, 'claimName': pvc_name }}]

    logger.debug('Created job: '+jobname)
    job = v1.create_namespaced_job(body=executor, namespace=namespace)
 
    global created_jobs
    created_jobs.append(jobname)

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
                        "volumeMounts": [],
                        "imagePullPolicy": "IfNotPresent"
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

  if args.debug:
    filer['spec']['template']['spec']['containers'][0]['imagePullPolicy'] = 'Always'

  logging.debug(json.dumps(filer))

  return filer

def append_mount(volume_mounts, name, path):
  # Checks all mount paths in volume_mounts if the path given is already in there
  duplicate = next((mount for mount in volume_mounts if mount['mountPath'] == path), None)
  # If not, add mount path
  if duplicate is None:
    logger.debug('appending '+name+' at path '+path)
    volume_mounts.append({ 'name': name, 'mountPath': path })

def populate_pvc(data, namespace, pvc_name, filer_version):
  volume_mounts = []

  # gather volumes that need to be mounted, without duplicates
  volume_name = task_volume_basename
  for idx, volume in enumerate(data['volumes']):
    append_mount(volume_mounts, volume_name, volume)

  # gather other paths that need to be mounted from inputs FILE and DIRECTORY entries
  for idx, aninput in enumerate(data['inputs']):
    if aninput['type'] == 'FILE':
      # strip filename from path
      p = re.compile('(.*)/')
      basepath = p.match(aninput['path']).group(1)
      logger.debug('basepath is: '+basepath)
    elif aninput['type'] == 'DIRECTORY':
      basepath = aninput['path']

    append_mount(volume_mounts, volume_name, basepath)

  # get name from taskmaster and create pretask template
  name = data['executors'][0]['metadata']['labels']['taskmaster-name']
  pretask = get_filer_template(filer_version, name+'-inputs-filer')

  # insert JSON input into job template
  container = pretask['spec']['template']['spec']['containers'][0]
  container['env'].append({ "name": "JSON_INPUT", "value": json.dumps(data) })
  container['args'] += ["inputs", "$(JSON_INPUT)"]

  # insert volume mounts and pvc into job template
  container['volumeMounts'] = volume_mounts
  pretask['spec']['template']['spec']['volumes'] = [ { "name": volume_name, "persistentVolumeClaim": { "claimName": pvc_name} } ]

  #print(json.dumps(pretask, indent=2), file=sys.stderr)

  # Run pretask filer job
  bv1 = client.BatchV1Api()
  job = bv1.create_namespaced_job(body=pretask, namespace=namespace)

  global created_jobs
  created_jobs.append(pretask['metadata']['name'])

  wait_for_job(pretask['metadata']['name'], namespace)

  return volume_mounts

def cleanup_pvc(data, namespace, volume_mounts, pvc_name, filer_version):
  # get name from taskmaster and create posttask template
  name = data['executors'][0]['metadata']['labels']['taskmaster-name']
  posttask = get_filer_template(filer_version, name+'-outputs-filer')

  # insert JSON input into posttask job template
  container = posttask['spec']['template']['spec']['containers'][0]
  container['env'].append({ "name": "JSON_INPUT", "value": json.dumps(data) })
  container['args'] += ["outputs", "$(JSON_INPUT)"]
  
  # insert volume mounts and pvc into posttask job template
  container['volumeMounts'] = volume_mounts
  posttask['spec']['template']['spec']['volumes'] = [ { "name": task_volume_basename, "persistentVolumeClaim": { "claimName": pvc_name} } ]

  # run posttask filer job
  bv1 = client.BatchV1Api()
  job = bv1.create_namespaced_job(body=posttask, namespace=namespace)

  global created_jobs
  created_jobs.append(posttask['metadata']['name'])

  wait_for_job(posttask['metadata']['name'], namespace)

  #print(json.dumps(posttask, indent=2), file=sys.stderr)

  # Delete pvc
  cv1 = client.CoreV1Api()
  cv1.delete_namespaced_persistent_volume_claim(pvc_name, namespace, client.V1DeleteOptions())

def main(argv):
  parser = argparse.ArgumentParser(description='TaskMaster main module')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('json', help='string containing json TES request, required if -f is not given', nargs='?')
  group.add_argument('-f', '--file', help='TES request as a file or \'-\' for stdin, required if json is not given')

  parser.add_argument('-p', '--polling-interval', help='Job polling interval', default=5)
  parser.add_argument('-fv', '--filer-version', help='Filer image version', default='v0.1.9')
  parser.add_argument('-n', '--namespace', help='Kubernetes namespace to run in', default='default')
  parser.add_argument('-s', '--state-file', help='State file for state.py script', default='/tmp/.teskstate')
  parser.add_argument('-d', '--debug', help='Set debug mode', action='store_true')

  global args
  args = parser.parse_args()

  polling_interval = args.polling_interval

  loglevel = logging.WARNING
  if args.debug:
    loglevel = logging.DEBUG
  
  global logger
  logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S', level=loglevel)
  logging.getLogger('kubernetes.client').setLevel(logging.CRITICAL)
  logger = logging.getLogger(__name__)
  logger.debug('Starting taskmaster')

  # Get input JSON
  if args.file is None:
    data = json.loads(args.json)
  elif args.file == '-':
    data = json.load(sys.stdin)
  else:
    data = json.load(open(args.file))

  #specs = generate_job_specs(tes)

  # Load kubernetes config file
  if args.debug:
    config.load_kube_config()
  else:
    config.load_incluster_config()

  # create and populate pvc only if volumes/inputs/outputs are given
  if data['volumes'] or data['inputs'] or data['outputs']:
    pvc_name = create_pvc(data, args.namespace)

    # to global var for cleanup purposes
    global created_pvc
    created_pvc = pvc_name

    volume_mounts = populate_pvc(data, args.namespace, pvc_name, args.filer_version)
    state = run_executors(data['executors'], args.namespace, volume_mounts, pvc_name)
  else:
    state = run_executors(data['executors'], args.namespace)

  # run executors
  print("Finished with state %s" % state)

  # upload files and delete pvc
  if data['volumes'] or data['inputs'] or data['outputs']:
    cleanup_pvc(data, args.namespace, volume_mounts, pvc_name, args.filer_version)

def clean_on_interrupt():
  logger.debug('Caught interrupt signal, deleting jobs and pvc')
  bv1 = client.BatchV1Api()
  
  for job in created_jobs:
    logger.debug('Deleting job: '+job)
    bv1.delete_namespaced_job(job, args.namespace, client.V1DeleteOptions()) 

  if created_pvc:
    cv1 = client.CoreV1Api()
    logger.debug('Deleting pvc: '+created_pvc)
    cv1.delete_namespaced_persistent_volume_claim(created_pvc, args.namespace, client.V1DeleteOptions())

if __name__ == "__main__":
  try:
    main(sys.argv)
  except KeyboardInterrupt:
    clean_on_interrupt()
