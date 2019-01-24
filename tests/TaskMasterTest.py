import unittest
from taskmaster import newParser
from argparse import Namespace


class ParserTest(unittest.TestCase):


    def test_defaults(self):
        
        parser = newParser()
        
        args = parser.parse_args(["json"])
        
        print(args)
        
        self.assertEquals( args 
                         , Namespace( debug=False, file=None, filer_version='v0.1.9', json='json', namespace='default', poll_interval=5, state_file='/tmp/.teskstate'
                                    , localKubeConfig=False
                                    )
                         )


    def test_localKubeConfig(self):
        
        parser = newParser()
        
        args = parser.parse_args(['json', '--localKubeConfig'])
        
        print(args)
        
        self.assertEquals( args 
                         , Namespace( debug=False, file=None, filer_version='v0.1.9', json='json', namespace='default', poll_interval=5, state_file='/tmp/.teskstate'
                                    , localKubeConfig=True 
                                    )
                         )



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()