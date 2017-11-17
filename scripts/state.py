#!/usr/bin/python

import sys
from kubernetes import client, config

def exec_state(exe_f, namespace, state):

  bv1 = client.BatchV1Api()
  cv1 = client.CoreV1Api()

  with open(exe_f) as exe_fp:
    exe_i = 0
    for exe in exe_file:
      job = bv1.read_namespaced_job(exe, namespace=namespace)
      state['logs'][exe_i]['start_time'] = job.metadata.creation_timestamp
      state['logs'][exe_i]['end_time'] = job.status.completion_time
      
      job_label_s = 'controller-uid='+job.spec.selector.match_labels['controller-uid']
      pods = cv1.list_namespaced_pod(label_selector=label_s, namespace=namespace)

      try: 
        state['logs'][exe_i]['stdout'] = read_namespaced_pod_log(pods[0].metadata.name, namespace=namespace)
      except IndexError:
        print("No pod matching job "+job.metadata.name+" could be found", file=sys.stderr)

      try:
        state['logs'][exe_i]['exit_code'] = pods[0].status.container_statuses[0].state.terminated.exit_code)
      except AttributeError:
        state['logs'][exe_i]['exit_code'] = ''

      exe_i += 1

def control_state(control_f, namespace, state):
  bv1 = client.BatchV1Api()
  cv1 = client.CoreV1Api()

  with open(control_f, 'r') as control_fp:
    masterjob = control_fp.read()
    job = bv1.read_namespaced_job(masterjob, namespace=namespace)
    state['start_time'] = job.metadata.creation_timestamp
    state['end_time'] = job.status.completion_time

    job_label_s = 'controller-uid='+job.spec.selector.match_labels['controller-uid']
    pods = cv1.list_namespaced_pod(label_selector=label_s, namespace=namespace)

    try: 
      state['system_logs'] = read_namespaced_pod_log(pods[0].metadata.name, namespace=namespace)
    except IndexError:
      print("No pod matching job "+job.metadata.name+" could be found", file=sys.stderr)

def main(argv):

  config.load_incluster_config()
  status = {}

  # get state file

  exec_state(exe_f, state)
  control_state(control_f, state)

  json.dumps(state)
if __name__ = "__main__":
  main(sys.argv)
