import json
from tesk_core import path
from tesk_core.path import fileEnabled


class Filer:
    
    def getVolumes(self):           return self.spec['spec']['template']['spec']['volumes']
                                    
    def getContainer(self, i):      return self.spec['spec']['template']['spec']['containers'][i]
    
    def getVolumeMounts(self):      return self.getContainer(0)['volumeMounts']
    def getEnv(self):               return self.getContainer(0)['env']
    def getImagePullPolicy(self):   return self.getContainer(0)['imagePullPolicy']

    
    def __init__(self, name, data, filer_version='v0.5', pullPolicyAlways = False):
        self.name = name
        self.spec = {
            "kind": "Job",
            "apiVersion": "batch/v1",
            "metadata": {"name": name},
            "spec": {
                "template": {
                    "metadata": {"name": "tesk-filer"},
                    "spec": {
                        "containers": [{
                            "name": "filer",
                            "image": "eu.gcr.io/tes-wes/filer:" + filer_version,
                            "args": [],
                            "env": [],
                            "volumeMounts": [],
                            "imagePullPolicy": 'Always' if pullPolicyAlways else 'IfNotPresent'
                        }
                        ],
                        "volumes": [],
                        "restartPolicy": "Never"
                    }
                }
            }
        }

        env = self.getEnv()
        env.append({ "name": "JSON_INPUT"           , "value": json.dumps(data)          })
        env.append({ "name": "HOST_BASE_PATH"       , "value": path.HOST_BASE_PATH       })
        env.append({ "name": "CONTAINER_BASE_PATH"  , "value": path.CONTAINER_BASE_PATH  })

        if fileEnabled():
            
            self.getVolumeMounts().append({ 
                
                  "name"      : 'transfer-volume'
                , 'mountPath' : path.CONTAINER_BASE_PATH 
            })
            
            self.getVolumes().append({
                
                  "name"                  : 'transfer-volume'
                , 'persistentVolumeClaim' : { 'claimName' : path.TRANSFER_PVC_NAME }
            })


    def set_ftp(self, user, pw):
        env = self.getEnv()
        env.append({"name": "TESK_FTP_USERNAME", "value": user})
        env.append({"name": "TESK_FTP_PASSWORD", "value": pw})

    def add_volume_mount(self, pvc):
        self.getVolumeMounts().extend(pvc.volume_mounts)
        self.getVolumes().append({ "name"                  : "task-volume",
                                   "persistentVolumeClaim" : {"claimName": pvc.name}})

    def get_spec(self, mode, debug=False):
        self.spec['spec']['template']['spec']['containers'][0]['args'] = [
            mode, "$(JSON_INPUT)"]

        if debug:
            self.spec['spec']['template']['spec']['containers'][0]['args'].append(
                '-d')

        self.spec['spec']['template']['metadata']['name'] = self.name
        return self.spec
