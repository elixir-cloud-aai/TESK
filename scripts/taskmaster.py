#!/usr/bin/python

import argparse
import json
import os
import binascii
import re
import time
import sys
from kubernetes import client, config

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
    jobname = executor['metadata']['name']+'-'+binascii.hexlify(os.urandom(4))
    executor['metadata']['name'] = jobname
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

def generate_config(user, cert_auth, client_cert, client_key):
  config = {'apiVersion': 'v1', 'kind': 'Config', 'clusters': [], 'users': [], 'contexts': [], 'current-context': user+'@kubernetes', 'preferences': {}}
  config['clusters'].append( {'name': 'kubernetes', 'cluster': 0} )
  config['clusters'][0]['cluster'] = {'server': 'kubernetes:6443', 'certificate-authority-data': cert_auth}
  config['users'].append( { 'name': user, 'user':0} )
  config['users'][0]['user'] = { 'client-certificate-data': client_cert, 'client-key-data': client_key }
  config['contexts'].append( { 'name': user+'@kubernetes', 'context': 0 } )
  config['contexts'][0]['context'] = { 'cluster': 'kubernetes', 'user': user }
  return config

def main(argv):
  parser = argparse.ArgumentParser(description='TaskMaster main module')
  parser.add_argument('file', help='file containing TES JSON request', nargs='?', type=argparse.FileType('r'), default=sys.stdin)

  config_def = os.path.join(os.environ["HOME"], '.kube/config')
  parser.add_argument('-c', '--config', help='kubernetes connection configuration', default=config_def)

  parser.add_argument('-ca', '--certificate-authority', help='Certificate authority data for the kubernetes cluster')
  parser.add_argument('-cc', '--client-cert', help='Client Certificate for the kubernetes user')
  parser.add_argument('-ck', '--client-key', help='Client Key data for the kubernetes user')
  parser.add_argument('-u', '--user', help='Kubernetes user who will create exec jobs')

  parser.add_argument('-p', '--polling-interval', help='Job polling interval', default=5)
  parser.add_argument('-n', '--namespace', help='Kubernetes namespace to run in', default='default')
  args = parser.parse_args()

  tes = json.load(args.file)
  specs = generate_job_specs(tes)

  generate_config(user, certificate_authority, client_cert, client_key)
  config.load_kube_config(args.config)

  state = run_executors(specs, args.polling_interval, args.namespace)
  print("Finished with state %s" % state)

if __name__ == "__main__":
  main(sys.argv)
