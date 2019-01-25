import unittest
from filer import newTransput, FTPTransput, HTTPTransput, FileTransput,\
    process_file, logConfig, getPath
from exception import UnknownProtocol, InvalidHostPath
from assertThrows import AssertThrowsMixin
import logging

try:
    from unittest.mock import patch  # Python 3 @UnresolvedImport
except:
    from mock import patch

from path import containerPath


@patch('path.HOST_BASE_PATH'      , '/home/tfga/workspace/cwl-tes')
@patch('path.CONTAINER_BASE_PATH' , '/transfer')
class FilerTest(unittest.TestCase, AssertThrowsMixin):
    

    @classmethod
    def setUpClass(cls):
        
        logConfig(logging.DEBUG)        # Doesn't work...

    
    @patch('filer.shutil.copy')
    def test_process_file(self, copyMock):
        
        filedata = {
            
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/md5",
            "path": "/var/lib/cwl/stgda974802-fa81-4f0b-8fe4-341d5655af4b/md5",
            
            "type": "FILE",  # File      = 'FILE'
                             # Directory = 'DIRECTORY'

            "name": "md5",
            "description": "cwl_input:md5"
        }
        
        process_file('inputs', filedata)
        
        copyMock.assert_called_once_with( '/transfer/tmphrtip1o8/md5'
                                        , '/var/lib/cwl/stgda974802-fa81-4f0b-8fe4-341d5655af4b/md5')

        
    def test_getPath(self):
        
        self.assertEquals( getPath('file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/md5')
                         ,                '/home/tfga/workspace/cwl-tes/tmphrtip1o8/md5')
        
        
    def test_containerPath(self):
        
        self.assertEquals( containerPath('/home/tfga/workspace/cwl-tes/tmphrtip1o8/md5')
                         ,               '/transfer/tmphrtip1o8/md5')
        
        # What happens if 'path' is not a descendant of HOST_BASE_PATH?
        self.assertThrows( lambda: containerPath('/someOtherFolder')
                         , InvalidHostPath
                         , "'/someOtherFolder' is not a descendant of 'HOST_BASE_PATH' (/home/tfga/workspace/cwl-tes)"
                         )
        
        
        
        
    def test_newTransput(self):
        
        self.assertEquals(newTransput('ftp')   , FTPTransput)
        self.assertEquals(newTransput('http')  , HTTPTransput)
        self.assertEquals(newTransput('https') , HTTPTransput)
        self.assertEquals(newTransput('file')  , FileTransput)
        
        self.assertThrows( lambda: newTransput('svn')
                         , UnknownProtocol
                         , "Unknown protocol: 'svn'"
                         )




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()