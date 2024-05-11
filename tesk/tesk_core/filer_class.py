import json
from tesk_core import path
from tesk_core.path import fileEnabled


class Filer:

    def getVolumes(self):           return self.spec['spec']['template']['spec']['volumes']

    def getContainer(self, i):      return self.spec['spec']['template']['spec']['containers'][i]

    def getVolumeMounts(self):      return self.getContainer(0)['volumeMounts']
    def getEnv(self):               return self.getContainer(0)['env']
    def getImagePullPolicy(self):   return self.getContainer(0)['imagePullPolicy']


    def __init__(self, name, data, filer_name='eu.gcr.io/tes-wes/filer', filer_version='v0.5', pullPolicyAlways = False, json_pvc=None):
        self.name = name
        self.json_pvc = json_pvc
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
                            "image": "%s:%s" % (filer_name, filer_version),
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
        if json_pvc is None:
            env.append({"name": "JSON_INPUT", "value": json.dumps(data)})
        env.append({"name": "HOST_BASE_PATH", "value": path.HOST_BASE_PATH})
        env.append(
            {"name": "CONTAINER_BASE_PATH", "value": path.CONTAINER_BASE_PATH})

        if json_pvc:
            self.getVolumeMounts().append({
                "name"        : 'jsoninput'
              , 'mountPath'   : '/jsoninput'
            })
            self.getVolumes().append({
                "name"        : 'jsoninput'
              , "configMap"   : { 'name' : json_pvc }
            })

        if fileEnabled():
            self.getVolumeMounts().append({

                  "name"      : 'transfer-volume'
                , 'mountPath' : path.CONTAINER_BASE_PATH
            })

            self.getVolumes().append({

                  "name"                  : 'transfer-volume'
                , 'persistentVolumeClaim' : { 'claimName' : path.TRANSFER_PVC_NAME }

            })

        self.add_s3_mount()

    def add_s3_mount(self):
        """ Mounts the s3 configuration file. The secret name is hardcoded and
            set to 'aws-secret'.
        """

        env = self.getEnv()
        env.append({"name": "AWS_CONFIG_FILE", "value": "/aws/config"})
        env.append(
            {
                "name": "AWS_SHARED_CREDENTIALS_FILE",
                "value": "/aws/credentials"
            }
        )

        self.getVolumeMounts().append(
            {
                "name": "s3-conf",
                "mountPath": "/aws",
                "readOnly": True,
            }
        )
        self.getVolumes().append(
            {
                "name": "s3-conf",
                "secret": {
                    "secretName": "aws-secret",
                    "items": [
                        {
                            "key": "credentials",
                            "path": "credentials"
                        },
                        {
                            "key": "config",
                            "path": "config"
                        }
                    ],
                    "optional": True,
                }
            }
        )

    def set_ftp(self, user, pw):
        env = self.getEnv()
        env.append({"name": "TESK_FTP_USERNAME", "value": user})
        env.append({"name": "TESK_FTP_PASSWORD", "value": pw})

    def set_backoffLimit(self, limit):
        """Set a number of retries of a job execution (default value is 6). Use the environment variable
        TESK_API_TASKMASTER_ENVIRONMENT_FILER_BACKOFF_LIMIT to explicitly set this value.

        Args:
            limit: The number of retries before considering a Job as failed.
        """
        self.spec['spec'].update({"backoffLimit": limit})

    def add_volume_mount(self, pvc):
        self.getVolumeMounts().extend(pvc.volume_mounts)
        self.getVolumes().append({"name": "task-volume",
                                  "persistentVolumeClaim": {
                                      "claimName": pvc.name}})


    def add_netrc_mount(self, netrc_name='netrc'):
        '''
            Sets $HOME to an arbitrary location (to prevent its change as a result of runAsUser), currently hardcoded to `/opt/home`
            Mounts the secret netrc into that location: $HOME/.netrc.
        '''

        self.getVolumeMounts().append({"name"      : 'netrc',
                                       "mountPath" : '/opt/home/.netrc',
                                       "subPath" : ".netrc"
                                      })
        self.getVolumes().append({"name"   : "netrc",
                                  "secret" : {
                                      "secretName" : netrc_name,
                                      "defaultMode" :  420,
                                      "items" : [
                                          {
                                              "key": ".netrc",
                                              "path": ".netrc"
                                          }
                                      ]
                                  }
                                 })
        self.getEnv().append({"name": "HOME",
                              "value": "/opt/home"
                            })


    def get_spec(self, mode, debug=False):
        if self.json_pvc is None:
            self.spec['spec']['template']['spec']['containers'][0]['args'] = [
                mode, "$(JSON_INPUT)"]
        else:
            self.spec['spec']['template']['spec']['containers'][0]['args'] = [
                mode, "/jsoninput/JSON_INPUT.gz"]

        if debug:
            self.spec['spec']['template']['spec']['containers'][0][
                'args'].append(
                '-d')

        self.spec['spec']['template']['metadata']['name'] = self.name
        return self.spec
