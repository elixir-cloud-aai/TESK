# encoding: utf-8

import unittest
from tesk_core.filer_class import Filer
from tesk_core import path
from tesk_core.Util import pprint

try:
    from unittest.mock import patch  # Python 3 @UnresolvedImport
except:
    from mock import patch




@patch('tesk_core.path.HOST_BASE_PATH'          , '/home/tfga/workspace/cwl-tes')
@patch('tesk_core.path.CONTAINER_BASE_PATH'     , '/transfer')
@patch('tesk_core.path.TRANSFER_PVC_NAME'       , 'transfer-pvc')
class FilerClassTest_env(unittest.TestCase):

    def test_env_vars(self):
        
        f = Filer('name', {'a': 1})
        
        pprint(f.spec)
        
        self.assertEquals(f.getEnv(), [
            
            { 'name': 'JSON_INPUT'           , 'value': '{"a": 1}'                      }
           ,{ 'name': 'HOST_BASE_PATH'       , 'value': '/home/tfga/workspace/cwl-tes'  }
           ,{ 'name': 'CONTAINER_BASE_PATH'  , 'value': '/transfer'                     }
        ])

    
    def test_mounts(self):
        '''
        kind: Pod
        apiVersion: v1
        metadata:
          name: tfga-pod
        spec:
          containers:
            - name: tfga-container
              image: eu.gcr.io/tes-wes/filer:testing
              volumeMounts:
                - mountPath: /transfer
                  name: transfer-volume
          volumes:
            - name: transfer-volume
              hostPath:
                path: /transferAtNode
              # persistentVolumeClaim:
              #  claimName: task-pv-claim
        '''
        
        f = Filer('name', {'a': 1})
        
        pprint(f.spec)
        
        pprint(f.getVolumeMounts())
        
        self.assertEquals(f.getVolumeMounts(), [
            
            { "name"        : 'transfer-volume'
            , 'mountPath'   : path.CONTAINER_BASE_PATH 
            }
        ])
        
        self.assertEquals(f.getVolumes(), [
            
            { "name"                  : 'transfer-volume'
            , 'persistentVolumeClaim' : { 'claimName' : 'transfer-pvc' }
            }
        ])

        
class FilerClassTest_no_env(unittest.TestCase):

    def test_mounts_file_disabled(self):
        
        f = Filer('name', {'a': 1})
        
        pprint(f.spec)
        
        pprint(f.getVolumeMounts())
        
        self.assertEquals(f.getVolumeMounts()   , [])
        self.assertEquals(f.getVolumes()        , [])

        
    def test_image_pull_policy(self):
        
        f = Filer('name', {'a': 1})
        self.assertEquals(f.getImagePullPolicy()   , 'IfNotPresent')

        f = Filer('name', {'a': 1}, pullPolicyAlways = True)
        self.assertEquals(f.getImagePullPolicy()   , 'Always')
        

        



    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()