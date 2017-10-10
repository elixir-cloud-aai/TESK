#!/usr/bin/python
import argparse
import json
import re
import time
from kubernetes import client, config

# job polling interval in seconds
job_poll_interv = 5

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
                                                           'memory': str(tes['resources']['ram_gb'])+'Gi'
  return specs

def run_executors(specs)
  v1 = client.BatchV1Api()
  for executor in specs:
    job = v1.create_namespaced_job(body=executor, namespace="default")
    print("Created job with status='%s'" % str(job.status))
    while (job.status.conditions[0].status.type)
      
      time.sleep(job_poll_interv)


def main():
  parser = argparse.ArgumentParser(description='TaskMaster main module')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('-f', '--file', help='file containing TES JSON request')
  group.add_argument('-c', '--config', help='kubernetes connection configuration')
  args = parser.parse_args()

  specs = generate_job_specs(args.file)
  
  config.load_kube_config(config)

  run_executors(specs)

if __name__ = "__main__":
  main()
