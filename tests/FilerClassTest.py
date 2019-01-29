import unittest
from tesk_core.filer_class import Filer
import json

try:
    from unittest.mock import patch  # Python 3 @UnresolvedImport
except:
    from mock import patch



def pprint(data):
    
    print json.dumps(data, indent=4)
    

@patch('tesk_core.path.HOST_BASE_PATH'      , '/home/tfga/workspace/cwl-tes')
@patch('tesk_core.path.CONTAINER_BASE_PATH' , '/transfer')
class FilerClassTest(unittest.TestCase):

    def test_env_vars(self):
        
        f = Filer('name', {'a': 1})
        
        pprint(f.spec)
        
        self.assertEquals(f.getEnv(), [
            
            { 'name': 'JSON_INPUT'           , 'value': '{"a": 1}'                      }
           ,{ 'name': 'HOST_BASE_PATH'       , 'value': '/home/tfga/workspace/cwl-tes'  }
           ,{ 'name': 'CONTAINER_BASE_PATH'  , 'value': '/transfer'                     }
        ])
        



    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()