import json
import sys
import re

tes = json.load(open(sys.argv[1]));
exe_i = 0

for executor in tes['executors']:
  valid_name = tes['name']
  valid_name = valid_name.lower()
  valid_name = re.sub(r" ", "-", valid_name)
  
  jobspec = {'apiVersion': 'batch/v1', 'kind': 'Job'}
  jobspec['metadata'] = {'name': valid_name}

  jobspec['spec'] = {'template': 0}
  jobspec['spec']['template'] = { 'metadata' : 0, 'spec': 0}
  
  jobspec['spec']['template']['metadata'] = {'name': valid_name}

  jobspec['spec']['template']['spec'] = { 'containers': 0, 'restartPolicy': 'Never'}

  jobspec['spec']['template']['spec']['containers'] = []

  jobspec['spec']['template']['spec']['containers'] = []
  jobspec['spec']['template']['spec']['containers'].append({ 
                                                       'name': valid_name+'-ex'+str(exe_i),
                                                       'image': executor['image_name'], 
                                                       'command': executor['cmd'],
                                                       'resources': {'requests': 0 }
                                                      })
  jobspec['spec']['template']['spec']['containers'][0]['resources']['requests'] = { 
                                                         'cpu': tes['resources']['cpu_cores'], 
                                                         'memory': str(tes['resources']['ram_gb'])+'Gi'
                                                                   }

  print(json.dumps(jobspec, indent=4, separators=(',', ': ')))
  exe_i += 1
