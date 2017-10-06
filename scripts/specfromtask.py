import json
import sys

tes = json.load(open(sys.argv[1]));
exe_i = 0

for executor in tes['executors']:
  
  jobspec = {'apiVersion': 'batch/v1', 'kind': 'Job'}
  jobspec['metadata'] = {'name': tes['name']}

  jobspec['spec'] = {'template': 0}
  jobspec['spec']['template'] = { 'metadata' : 0, 'spec': 0}
  jobspec['spec']['template']['metadata'] = {'name': tes['name']}

  jobspec['spec']['template']['spec'] = { 'containers': 0, 'restartPolicy': 'Never', 'backoffLimit': 5 }

  jobspec['spec']['template']['spec']['containers'] = []

  jobspec['spec']['template']['spec']['containers'] = { 
                                                       'name': tes['name']+' Executor '+str(exe_i),
                                                       'image': executor['image_name'], 
                                                       'command': executor['cmd'],
                                                       'resources': {'requests':0}
                                                      }
  jobspec['spec']['template']['spec']['containers']['resources']['requests'] = { 
                                                         'cpu': tes['resources']['cpu_cores'], 
                                                         'memory': str(tes['resources']['ram_gb'])+'Gi'
                                                                   }

  print(json.dumps(jobspec, indent=4, separators=(',', ': ')))
  exe_i += 1
