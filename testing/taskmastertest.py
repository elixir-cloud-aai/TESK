#!/usr/bin/python

import os
import json
import binascii
import argparse
from kubernetes import client, config

parser.add_argument('file', help='file containing TES JSON request', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
parser.add_argument('-s', '--spec', help='file containing taskmaster spec', required=True)

config.load_kube_config(
    os.path.join(os.environ["HOME"], '.kube/config'))

v1 = client.BatchV1Api()

dep = json.load(open(args.spec))
dep['metadata']['name'] = 'taskmaster-'+binascii.hexlify(os.urandom(4))
dep['spec']['template']['spec']['containers'][0]['command'] = args.file.read()

resp = v1.create_namespaced_job(body=dep, namespace="default")
print("Taskmaster created. status='%s'" % str(resp.status))
