import unittest
from tesk_core.taskmaster import newParser, run_task, newLogger
from argparse import Namespace
import json
import logging
try:
    from unittest.mock import patch  # Python 3 @UnresolvedImport
except:
    from mock import patch



def pvcCreateMock(self):    print '[mock] Creating PVC...'
def pvcDeleteMock(self):    print '[mock] Deleting PVC...'

def jobRunToCompletionMock(job, b, c):
    
    print "[mock] Creating job '{}'...".format(job.name)
    
    return 'Complete'


class ParserTest(unittest.TestCase):


    def test_defaults(self):
        
        parser = newParser()
        
        args = parser.parse_args(["json"])
        
        print(args)
        
        self.assertEquals( args 
                         , Namespace( debug=False, file=None, filer_version='v0.1.9', json='json', namespace='default', poll_interval=5, state_file='/tmp/.teskstate'
                                    , localKubeConfig=False
                                    , pull_policy_always=False
                                    )
                         )


    def test_localKubeConfig(self):
        
        parser = newParser()
        
        args = parser.parse_args(['json', '--localKubeConfig'])
        
        print(args)
        
        self.assertEquals( args 
                         , Namespace( debug=False, file=None, filer_version='v0.1.9', json='json', namespace='default', poll_interval=5, state_file='/tmp/.teskstate'
                                    , localKubeConfig=True 
                                    , pull_policy_always=False
                                    )
                         )

        
    def test_pullPolicyAlways(self):
        
        parser = newParser()
        
        self.assertEquals( parser.parse_args(['json'                        ]).pull_policy_always,       False )
        self.assertEquals( parser.parse_args(['json', '--pull-policy-always']).pull_policy_always,       True  )


        
    @patch('tesk_core.taskmaster.args'                  , Namespace(debug=True, namespace='default', pull_policy_always=True))
    @patch('tesk_core.taskmaster.logger'                , newLogger(logging.DEBUG))
    @patch('tesk_core.taskmaster.PVC.create'            , pvcCreateMock)
    @patch('tesk_core.taskmaster.PVC.delete'            , pvcDeleteMock)
    @patch('tesk_core.taskmaster.Job.run_to_completion' , jobRunToCompletionMock)
    def test_run_task(self):
        
        with open('tests/resources/inputFile.json') as fh:
            data = json.load(fh)

        run_task(data, 'filer_version')



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()