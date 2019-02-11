import unittest
from tesk_core.filer import newTransput, FTPTransput, HTTPTransput, FileTransput,\
    process_file, logConfig, getPath
from tesk_core.exception import UnknownProtocol, InvalidHostPath,\
    FileProtocolDisabled
from assertThrows import AssertThrowsMixin
import logging

try:
    from unittest.mock import patch  # Python 3 @UnresolvedImport
except:
    from mock import patch

from tesk_core.path import containerPath


@patch('tesk_core.path.HOST_BASE_PATH'      , '/home/tfga/workspace/cwl-tes')
@patch('tesk_core.path.CONTAINER_BASE_PATH' , '/transfer')
class FilerTest(unittest.TestCase, AssertThrowsMixin):
    

    @classmethod
    def setUpClass(cls):
        
        logConfig(logging.DEBUG)        # Doesn't work...

    
    @patch('tesk_core.filer.shutil.copytree')
    @patch('tesk_core.filer.shutil.copy')
    def test_download_file(self, copyMock, copytreeMock):
        
        filedata = {
            
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/md5",
            "path": "/var/lib/cwl/stgda974802-fa81-4f0b-8fe4-341d5655af4b/md5",
            
            "type": "FILE",  # File      = 'FILE'
                             # Directory = 'DIRECTORY'

            "name": "md5",
            "description": "cwl_input:md5"
        }
        
        process_file('inputs', filedata)
        
        copytreeMock.assert_not_called()
        
        copyMock.assert_called_once_with( '/transfer/tmphrtip1o8/md5'
                                        , '/var/lib/cwl/stgda974802-fa81-4f0b-8fe4-341d5655af4b/md5')

    @patch('tesk_core.filer.shutil.copytree')
    @patch('tesk_core.filer.shutil.copy')
    def test_upload_dir(self, copyMock, copytreeMock):
        
        filedata = {
            
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/",
            "path": "/TclSZU",
            "type": "DIRECTORY",
            "name": "workdir"
        }
        
        process_file('outputs', filedata)
        
        copyMock.assert_not_called()
        
        copytreeMock.assert_called_once_with( '/TclSZU'
                                            , '/transfer/tmphrtip1o8')

        
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
        
class FilerTest_no_env(unittest.TestCase, AssertThrowsMixin):

    def test_newTransput_file_disabled(self):
        
        self.assertThrows( lambda: newTransput('file')
                         , FileProtocolDisabled
                         , "'file:' protocol disabled\n"
                           "To enable it, both 'HOST_BASE_PATH' and 'CONTAINER_BASE_PATH' environment variables must be defined."
                         )




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()