import unittest
from tesk_core.filer import newTransput, FTPTransput, HTTPTransput, FileTransput,\
    process_file, logConfig, getPath, copyDir
from tesk_core.exception import UnknownProtocol, InvalidHostPath,\
    FileProtocolDisabled
from assertThrows import AssertThrowsMixin
import logging
import os
from fs.opener import open_fs
from StringIO import StringIO
from string import strip

try:
    from unittest.mock import patch  # Python 3 @UnresolvedImport
except:
    from mock import patch

from tesk_core.path import containerPath


def getTree(rootDir):
        
        strio = StringIO()
        with open_fs(rootDir) as dst1_fs:
            
            dst1_fs.tree(file = strio)
            
            treeTxt = strio.getvalue()
            
            strio.close()
            
            return treeTxt

        
def stripLines(txt):
    
    return '\n'.join([ strip(line) for line in txt.splitlines()[1:] ])



@patch('tesk_core.path.HOST_BASE_PATH'      , '/home/tfga/workspace/cwl-tes')
@patch('tesk_core.path.CONTAINER_BASE_PATH' , '/transfer')
class FilerTest(unittest.TestCase, AssertThrowsMixin):
    

    @classmethod
    def setUpClass(cls):
        
        logConfig(logging.DEBUG)        # Doesn't work...

    
    @patch('tesk_core.filer.copyDir')
    @patch('tesk_core.filer.shutil.copy')
    def test_download_file(self, copyMock, copyDirMock):
        
        filedata = {
            
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/md5",
            "path": "/var/lib/cwl/stgda974802-fa81-4f0b-8fe4-341d5655af4b/md5",
            
            "type": "FILE",  # File      = 'FILE'
                             # Directory = 'DIRECTORY'

            "name": "md5",
            "description": "cwl_input:md5"
        }
        
        process_file('inputs', filedata)
        
        copyDirMock.assert_not_called()
        
        copyMock.assert_called_once_with( '/transfer/tmphrtip1o8/md5'
                                        , '/var/lib/cwl/stgda974802-fa81-4f0b-8fe4-341d5655af4b/md5')

    @patch('tesk_core.filer.copyDir')
    @patch('tesk_core.filer.shutil.copy')
    def test_download_dir(self, copyMock, copyDirMock):
        
        filedata = {
            
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/",
            "path": "/TclSZU",
            "type": "DIRECTORY",
            "name": "workdir"
        }
        
        process_file('inputs', filedata)
        
        copyMock.assert_not_called()
        
        copyDirMock.assert_called_once_with( '/transfer/tmphrtip1o8'
                                            , '/TclSZU')
        

    @patch('tesk_core.filer.copyDir')
    @patch('tesk_core.filer.shutil.copy')
    def test_upload_dir(self, copyMock, copyDirMock):
        
        filedata = {
            
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/",
            "path": "/TclSZU",
            "type": "DIRECTORY",
            "name": "workdir"
        }
        
        process_file('outputs', filedata)
        
        copyMock.assert_not_called()
        
        copyDirMock.assert_called_once_with( '/TclSZU'
                                            , '/transfer/tmphrtip1o8')

    @patch('tesk_core.filer.copyDir')
    @patch('tesk_core.filer.shutil.copy')
    def test_upload_file(self, copyMock, copyDirMock):
        
        filedata = {
            
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/md5",
            "path": "/TclSZU/md5",
            "type": "FILE",
            "name": "stdout"
        }
        
        process_file('outputs', filedata)
        
        copyDirMock.assert_not_called()
        
        copyMock.assert_called_once_with( '/TclSZU/md5'
                                        , '/transfer/tmphrtip1o8/md5')

        
    def test_copyDir(self):
        
        def rmDir(d):
            
            os.system('rm -r {}'.format(d))


        baseDir = 'tests/resources/copyDirTest/'
        src     = os.path.join(baseDir, 'src')
        dst1    = os.path.join(baseDir, 'dst1')
        dst2    = os.path.join(baseDir, 'dst2')
        
        rmDir(dst1)
        rmDir(dst2)
        
        self.assertTrue(os.path.exists(src))    # src should exist
        self.assertFalse(os.path.exists(dst1))  # dst1 shouldn't
        self.assertFalse(os.path.exists(dst2))  # dst2 shouldn't
        
        
        # Copying to existing dst ------------------------------------------------
        # Let's create dst1
        os.mkdir(dst1)
        self.assertTrue(os.path.exists(dst1))  # Now dst1 should exist
        
        # Let's try to copy
        copyDir(src, dst1)
        
        self.assertEquals( getTree(dst1)
                         , stripLines('''
                            |-- a
                            |   |-- 1.txt
                            |   `-- 2.txt
                            `-- 3.txt
                            '''          
                            )
                         )
        
        # Copying to non-existing dst ------------------------------------------------
        self.assertFalse(os.path.exists(dst2))  # dst2 should not exist
        
        # Let's try to copy
        copyDir(src, dst2)
        
        self.assertEquals( getTree(dst2)
                         , stripLines('''
                            |-- a
                            |   |-- 1.txt
                            |   `-- 2.txt
                            `-- 3.txt
                            '''          
                            )
                         )
        
        
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