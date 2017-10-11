#!/usr/bin/python

import argparse
import json
import os
import binascii
import json
from kubernetes import client, config

jobspec = '../specs/pi_job.json'
failspec = '../specs/pi_fail.json'

pilen = 2000
cmd = 'print bpi('+str(pilen)+')'

parser = argparse.ArgumentParser(description='TaskMaster main module')
parser.add_argument('-f', '--fail', action='store_true')
args = parser.parse_args()

jobfile = failspec if args.fail else jobspec
jobname = 'pi-fail-' if args.fail else 'pi-example-'

config.load_kube_config(
    os.path.join(os.environ["HOME"], '.kube/config'))

v1 = client.BatchV1Api()
with open(jobfile) as f:
  jobdesc = json.load(f)
  jobdesc['metadata']['name'] = jobname+binascii.hexlify(os.urandom(4))
  jobdesc['spec']['template']['spec']['containers'][0]['command'][3] = cmd
  resp = v1.create_namespaced_job(body=jobdesc, namespace="default")
  print("Job created. status='%s'" % str(resp.status))
