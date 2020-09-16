import unittest
import pytest
import boto3
import logging
import os
from tesk_core.filer import newTransput, FTPTransput, HTTPTransput, FileTransput,\
    process_file, logConfig, getPath, copyDir, copyFile, ftp_check_directory,\
    subfolders_in
from tesk_core.exception import UnknownProtocol, InvalidHostPath,\
    FileProtocolDisabled
from tesk_core.path import containerPath
from tesk_core.filer_s3 import S3Transput
from tesk_core.extract_endpoint import extract_endpoint
from assertThrows import AssertThrowsMixin
from fs.opener import open_fs
from io import StringIO
from unittest.mock import patch, mock_open
from moto import mock_s3






def getTree(rootDir):
    strio = StringIO()
    with open_fs(rootDir) as dst1_fs:
        dst1_fs.tree(file=strio)
        treeTxt = strio.getvalue()
        strio.close()
        return treeTxt


def stripLines(txt):
    return '\n'.join([line.strip() for line in txt.splitlines()[1:]])


@patch('tesk_core.path.HOST_BASE_PATH', '/home/tfga/workspace/cwl-tes')
@patch('tesk_core.path.CONTAINER_BASE_PATH', '/transfer')
class FilerTest(unittest.TestCase, AssertThrowsMixin):

    @classmethod
    def setUpClass(cls):
        logConfig(logging.DEBUG)  # Doesn't work...

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

        copyMock.assert_called_once_with('/transfer/tmphrtip1o8/md5',
                                         '/var/lib/cwl/stgda974802-fa81-4f0b-'
                                         '8fe4-341d5655af4b/md5')

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

        copyDirMock.assert_called_once_with('/transfer/tmphrtip1o8', '/TclSZU')

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

        copyDirMock.assert_called_once_with('/TclSZU', '/transfer/tmphrtip1o8')

    @patch('tesk_core.filer.copyDir')
    @patch('tesk_core.filer.copyFile')
    def test_upload_file(self, copyFileMock, copyDirMock):

        filedata = {
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/md5",
            "path": "/TclSZU/md5",
            "type": "FILE",
            "name": "stdout"
        }

        process_file('outputs', filedata)

        copyDirMock.assert_not_called()

        copyFileMock.assert_called_once_with( '/TclSZU/md5'
                                        , '/transfer/tmphrtip1o8/md5')


    @patch('tesk_core.filer.copyDir')
    @patch('tesk_core.filer.copyFile')
    def test_upload_file_glob(self, copyFileMock, copyDirMock):

        filedata = {
            "url": "file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/md5*",
            "path": "/TclSZU/md5*",
            "type": "FILE",
            "name": "stdout"
        }

        process_file('outputs', filedata)

        copyDirMock.assert_not_called()

        copyFileMock.assert_called_once_with( '/TclSZU/md5*'
                                        , '/transfer/tmphrtip1o8/md5*')


    def test_copyDir(self):
        def rmDir(d):
            os.system('rm -r {}'.format(d))

        baseDir = 'tests/resources/copyDirTest/'
        src = os.path.join(baseDir, 'src')
        dst1 = os.path.join(baseDir, 'dst1')
        dst2 = os.path.join(baseDir, 'dst2')

        rmDir(dst1)
        rmDir(dst2)

        self.assertTrue(os.path.exists(src))  # src should exist
        self.assertFalse(os.path.exists(dst1))  # dst1 shouldn't
        self.assertFalse(os.path.exists(dst2))  # dst2 shouldn't

        # Copying to existing dst ---------------------------------------------
        # Let's create dst1
        os.mkdir(dst1)
        self.assertTrue(os.path.exists(dst1))  # Now dst1 should exist

        # Let's try to copy
        copyDir(src, dst1)


        self.assertEqual(getTree(dst1),
                          stripLines('''
                            |-- a
                            |   |-- 1.txt
                            |   `-- 2.txt
                            `-- 3.txt
                            '''
                                     )
                          )

        # Copying to non-existing dst -----------------------------------------
        self.assertFalse(os.path.exists(dst2))  # dst2 should not exist

        # Let's try to copy
        copyDir(src, dst2)

        self.assertEqual(getTree(dst2),
                          stripLines('''
                            |-- a
                            |   |-- 1.txt
                            |   `-- 2.txt
                            `-- 3.txt
                            '''
                                     )
                          )

    def test_getPath(self):

        self.assertEqual( getPath('file:///home/tfga/workspace/cwl-tes/tmphrtip1o8/md5')
                         ,                '/home/tfga/workspace/cwl-tes/tmphrtip1o8/md5')

    def test_getPathNoScheme(self):

        self.assertEquals( getPath('/home/tfga/workspace/cwl-tes/tmphrtip1o8/md5')
                         ,         '/home/tfga/workspace/cwl-tes/tmphrtip1o8/md5')

        self.assertEqual( containerPath('/home/tfga/workspace/cwl-tes/tmphrtip1o8/md5')
                         ,               '/transfer/tmphrtip1o8/md5')

    def test_containerPath(self):
        self.assertEqual(
            containerPath('/home/tfga/workspace/cwl-tes/tmphrtip1o8/md5'),
            '/transfer/tmphrtip1o8/md5')

        # What happens if 'path' is not a descendant of HOST_BASE_PATH?
        self.assertThrows(lambda: containerPath('/someOtherFolder'),
                          InvalidHostPath,
                          "'/someOtherFolder' is not a descendant of "
                          "'HOST_BASE_PATH' (/home/tfga/workspace/cwl-tes)"
                          )

    def test_newTransput(self):
        self.assertEqual(newTransput('ftp', 'test.com'), FTPTransput)
        self.assertEqual(newTransput('http', 'test.com'), HTTPTransput)
        self.assertEqual(newTransput('https', 'test.com'), HTTPTransput)
        self.assertEqual(newTransput('file', '/home/tfga/workspace/'), FileTransput)
        self.assertEqual(newTransput('s3', '/home/tfga/workspace/'), S3Transput)
        self.assertEqual(newTransput('http', 's3.aws.com'), S3Transput)

        self.assertThrows(lambda: newTransput('svn', 'example.com')
                          , UnknownProtocol
                          , "Unknown protocol: 'svn'"
                          )

    @patch('ftplib.FTP')
    def test_ftp_check_directory(self, conn):
        """ Ensure that when the path provided is an existing directory, the
            return value is 0."""
        path = os.path.curdir
        self.assertEqual(ftp_check_directory(conn, path), 0)

    def test_subfolders_in(self):
        """ Ensure the all the subfolders of a path are properly returned."""
        path = "/this/is/a/path"
        subfldrs = ['/this', '/this/is', '/this/is/a', '/this/is/a/path']
        self.assertEqual(subfolders_in(path), subfldrs)



class FilerTest_no_env(unittest.TestCase, AssertThrowsMixin):

    def test_newTransput_file_disabled(self):
        self.assertThrows( lambda: newTransput('file','/home/user/test')
                         , FileProtocolDisabled
                         , "'file:' protocol disabled\n"
                           "To enable it, both 'HOST_BASE_PATH' and 'CONTAINER_BASE_PATH' environment variables must be defined."
                         )
@pytest.fixture()
def moto_boto():
    with mock_s3():
        client = boto3.resource('s3',endpoint_url="http://s3.amazonaws.com")
        client.create_bucket(Bucket='tesk')
        client.Bucket('tesk').put_object(Bucket='tesk', Key='folder/file.txt', Body='')
        client.Bucket('tesk').put_object(Bucket='tesk', Key='folder1/folder2/file.txt', Body='')
        yield

@pytest.mark.parametrize("path, url, ftype,expected", [
        ("/home/user/filer_test/file.txt", "http://tesk.s3.amazonaws.com/folder/file.txt","FILE",
         ("tesk","folder/file.txt")),
        ("/home/user/filer_test/file.txt", "http://tesk.s3-aws-region.amazonaws.com/folder/file.txt","FILE",
         ("tesk","folder/file.txt")),
        ("/home/user/filer_test/file.txt", "http://s3.amazonaws.com/tesk/folder/file.txt","FILE",
         ("tesk","folder/file.txt")),
        ("/home/user/filer_test/file.txt", "http://s3-aws-region.amazonaws.com/tesk/folder/file.txt","FILE",
         ("tesk","folder/file.txt")),
        ("/home/user/filer_test/file.txt", "s3://tesk/folder/file.txt","FILE",
         ("tesk","folder/file.txt")),
        ("/home/user/filer_test/file.txt", "http://tesk.s3.amazonaws.com/folder1/folder2","DIRECTORY",
         ("tesk","folder1/folder2")),
        ("/home/user/filer_test/file.txt", "http://tesk.s3-aws-region.amazonaws.com/folder1/folder2","DIRECTORY",
         ("tesk","folder1/folder2")),
        ("/home/user/filer_test/file.txt", "http://s3.amazonaws.com/tesk/folder1/folder2","DIRECTORY",
         ("tesk","folder1/folder2")),
        ("/home/user/filer_test/file.txt", "http://s3-aws-region.amazonaws.com/tesk/folder1/folder2","DIRECTORY",
         ("tesk","folder1/folder2")),
        ("/home/user/filer_test/file.txt", "s3://tesk/folder1/folder2","DIRECTORY",
         ("tesk","folder1/folder2")),
    ])
def test_get_bucket_name_and_file_path( moto_boto, path, url, ftype,expected):
        """
        Check if the bucket name and path is extracted correctly for file and folders
        """
        trans = S3Transput(path, url, ftype)
        assert trans.get_bucket_name_and_file_path() == expected

@pytest.mark.parametrize("path, url, ftype,expected", [
        ("/home/user/filer_test/file.txt", "http://tesk.s3.amazonaws.com/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://tesk.s3-aws-region.amazonaws.com/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://s3.amazonaws.com/tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://s3-aws-region.amazonaws.com/tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "s3://tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://mybucket.s3.amazonaws.com/folder/file.txt","FILE",1),
        ("/home/user/filer_test/file.txt", "http://mybucket.s3-aws-region.amazonaws.com/folder/file.txt","FILE",1),
        ("/home/user/filer_test/file.txt", "http://s3.amazonaws.com/mybucket/folder/file.txt","FILE",1),
        ("/home/user/filer_test/file.txt", "http://s3-aws-region.amazonaws.com/mybucket/folder/file.txt","FILE",1),
        ("/home/user/filer_test/file.txt", "s3://mybucket/folder/file.txt","FILE",1),
        ("/home/user/filer_test/", "http://tesk.s3.amazonaws.com/folder1/folder2","DIRECTORY",0),
        ("/home/user/filer_test/", "http://tesk.s3-aws-region.amazonaws.com/folder1/folder2","DIRECTORY",0),
        ("/home/user/filer_test/", "http://s3.amazonaws.com/tesk/folder1/folder2","DIRECTORY",0),
        ("/home/user/filer_test/", "http://s3-aws-region.amazonaws.com/tesk/folder1/folder2","DIRECTORY",0),
        ("/home/user/filer_test/", "s3://tesk/folder1/folder2","DIRECTORY",0),
        ("/home/user/filer_test/", "http://mybucket.s3.amazonaws.com/folder1/folder2","DIRECTORY",1),
        ("/home/user/filer_test/", "http://mybucket.s3-aws-region.amazonaws.com/folder1/folder2","DIRECTORY",1),
        ("/home/user/filer_test/", "http://s3.amazonaws.com/mybucket/folder1/folder2","DIRECTORY",1),
        ("/home/user/filer_test/", "http://s3-aws-region.amazonaws.com/mybucket/folder1/folder2","DIRECTORY",1),
        ("/home/user/filer_test/", "s3://mybucket/folder1/folder2","DIRECTORY",1)
    ])
def test_check_if_bucket_exists(moto_boto, path, url, ftype, expected):
        """
        Check if the bucket exists
        """
        client = boto3.resource('s3', endpoint_url="http://s3.amazonaws.com")
        trans = S3Transput(path, url, ftype)
        assert trans.check_if_bucket_exists(client) == expected

# @patch('tesk_core.filer.os.makedirs')
# @patch('builtins.open')
# @patch('s3transfer.utils.OSUtils.rename_file')
@pytest.mark.parametrize("path, url, ftype,expected", [
        ("/home/user/filer_test/file.txt", "http://tesk.s3.amazonaws.com/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://tesk.s3-aws-region.amazonaws.com/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://s3.amazonaws.com/tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://s3-aws-region.amazonaws.com/tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "s3://tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://tesk.s3.amazonaws.com/folder/file_new.txt","FILE",1),
        ("/home/user/filer_test/file.txt", "http://tesk.s3-aws-region.amazonaws.com/folder/file_new.txt","FILE",1),
        ("/home/user/filer_test/file.txt", "http://s3.amazonaws.com/tesk/folder/file_new.txt","FILE",1),
        ("/home/user/filer_test/file.txt", "http://s3-aws-region.amazonaws.com/tesk/folder/file_new.txt","FILE",1),
        ("/home/user/filer_test/file.txt", "s3://tesk/folder/file_new.txt","FILE",1),
    ])
def test_s3_download_file( moto_boto, path, url, ftype, expected, fs, caplog):
    """
    Checking for successful/failed file download from Object storage server
    """
    with S3Transput(path, url, ftype) as trans:
        assert trans.download_file() == expected
        if expected:
            assert "Not Found" in caplog.text
        else:
            assert os.path.exists(path) == True



@patch('tesk_core.filer.os.makedirs')
@patch('builtins.open')
@patch('s3transfer.utils.OSUtils.rename_file')
@patch("tesk_core.filer_s3.extract_endpoint", return_value="http://s3.amazonaws.com")
@pytest.mark.parametrize("path, url, ftype,expected", [
        ("filer_test/", "http://tesk.s3.amazonaws.com/folder1/","DIRECTORY",0),
        ("filer_test/", "http://tesk.s3-aws-region.amazonaws.com/folder1/","DIRECTORY",0),
        ("filer_test/", "http://s3.amazonaws.com/tesk/folder1/","DIRECTORY",0),
        ("filer_test/", "http://s3-aws-region.amazonaws.com/tesk/folder1/","DIRECTORY",0),
        ("filer_test/", "s3://tesk/folder1/","DIRECTORY",0),
        ("filer_test/", "http://tesk.s3.amazonaws.com/folder10/folder20","DIRECTORY",1),
        ("filer_test/", "http://tesk.s3-aws-region.amazonaws.com/folder10/folder20","DIRECTORY",1),
        ("filer_test/", "http://s3.amazonaws.com/tesk/folder10/folder20","DIRECTORY",1),
        ("filer_test/", "http://s3-aws-region.amazonaws.com/tesk/folder10/folder20","DIRECTORY",1),
        ("filer_test/", "s3://tesk/folder10/folder20","DIRECTORY",1)
    ])
def test_s3_download_directory( mock_extract_endpoint,mock_makedirs, mock_open, mock_rename, path, url, ftype,
                             expected, moto_boto, caplog):
    """
    test case to check directory download from Object storage server
    """
    with S3Transput(path, url, ftype) as trans:
        assert  trans.download_dir() == expected
        print(mock_rename.mock_calls)
        if expected:
            assert "Invalid file path" in caplog.text
        else:
            '''
            s3 object path http://tesk.s3.amazonaws.com/folder1/ will contain 'folder2', checking if the 'folder2'
             is present in the download folder.
            '''
            mock_rename.assert_called_once_with('filer_test/folder2', exist_ok=True)


@pytest.mark.parametrize("path, url, ftype,expected", [
        ("/home/user/filer_test/file.txt", "http://tesk.s3.amazonaws.com/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://tesk.s3-aws-region.amazonaws.com/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://s3.amazonaws.com/tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "http://s3-aws-region.amazonaws.com/tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file.txt", "s3://tesk/folder/file.txt","FILE",0),
        ("/home/user/filer_test/file_new.txt", "http://tesk.s3.amazonaws.com/folder/file.txt","FILE",1),
        ("/home/user/filer_test/file_new.txt", "http://tesk.s3-aws-region.amazonaws.com/folder/file.txt","FILE",1),
        ("/home/user/filer_test/file_new.txt", "http://s3.amazonaws.com/tesk/folder/file.txt","FILE",1),
        ("/home/user/filer_test/file_new.txt", "http://s3-aws-region.amazonaws.com/tesk/folder/file.txt","FILE",1),
        ("/home/user/filer_test/file_new.txt", "s3://tesk/folder/file.txt","FILE",1),
    ])
def test_s3_upload_file( moto_boto, path, url, ftype, expected,fs, caplog):
    """
        Testing successful/failed file upload to object storage server
    """
    fs.create_file("/home/user/filer_test/file.txt")
    with S3Transput(path, url, ftype) as trans:
        assert trans.upload_file() == expected
        if expected:
            assert "File upload failed for" in caplog.text
        else:
            client = boto3.resource('s3', endpoint_url="http://s3.amazonaws.com")
            '''
            Checking if the file was uploaded, if the object is found load() method will return None 
            otherwise an exception will be raised.
            '''
            assert client.Object('tesk', 'folder/file.txt').load() == None



@pytest.mark.parametrize("path, url, ftype,expected", [
        ("tests", "http://tesk.s3.amazonaws.com/folder1/folder2","DIRECTORY",0),
        ("tests", "http://tesk.s3-aws-region.amazonaws.com/folder1/folder2","DIRECTORY",0),
        ("tests", "http://s3.amazonaws.com/tesk/folder1/folder2","DIRECTORY",0),
        ("tests", "http://s3-aws-region.amazonaws.com/tesk/folder1/folder2","DIRECTORY",0),
        ("tests", "s3://tesk/folder1/folder2","DIRECTORY",0),
        ("/home/user/filer_test_new/", "http://tesk.s3.amazonaws.com/folder1/folder2","DIRECTORY",1),
        ("/home/user/filer_test_new/", "http://tesk.s3-aws-region.amazonaws.com/folder1/folder2","DIRECTORY",1),
        ("/home/user/filer_test_new/", "http://s3.amazonaws.com/tesk/folder1/folder2","DIRECTORY",1),
        ("/home/user/filer_test_new/", "http://s3-aws-region.amazonaws.com/tesk/folder1/folder2","DIRECTORY",1),
        ("/home/user/filer_test_new/", "s3://tesk/folder1/folder2","DIRECTORY",1)
    ])
def test_s3_upload_directory(path, url, ftype, expected, moto_boto, caplog):
    """
        Checking for successful and failed Directory upload to object storage server
    """

    with S3Transput(path, url, ftype) as trans:
        assert trans.upload_dir() == expected
        if expected:
            print(caplog.text)
            assert "File upload failed for" in caplog.text
        else:
            client = boto3.resource('s3', endpoint_url="http://s3.amazonaws.com")
            '''
            Checking if the file was uploaded, if the object is found load() method will return None 
            otherwise an exception will be raised.
            '''
            assert client.Object('tesk', 'folder1/folder2/test_filer.py').load() == None


def test_upload_directory_for_unknown_file_type(moto_boto, fs, monkeypatch, caplog):
    """
        Checking whether an exception is raised when the object type is neither file or directory
        If the exception is raised, an error message will be logged.
    """
    monkeypatch.setattr(os.path, 'isfile', lambda _:False)
    fs.create_file("/home/user/filer_test/text.txt")
    url, ftype = "s3://tesk/folder10/folder20","DIRECTORY"
    path = "/home/user/filer_test/"
    trans = S3Transput(path, url, ftype)
    client = boto3.resource('s3', endpoint_url="http://s3.amazonaws.com")
    trans.bucket_obj = client.Bucket(trans.bucket)
    trans.upload_dir()
    assert "Object is neither file or directory" in caplog.text


@patch("tesk_core.filer.os.path.exists", return_value=1)
def test_extract_url_from_config_file(mock_path_exists):
    """
    Testing extraction of endpoint url from default file location
    """
    read_data = '\n'.join(["[default]", "endpoint_url = http://s3-aws-region.amazonaws.com"])
    with patch("builtins.open", mock_open(read_data=read_data), create=True) as mock_file:
        mock_file.return_value.__iter__.return_value = read_data.splitlines()
        assert extract_endpoint() == "http://s3-aws-region.amazonaws.com"
        mock_file.assert_called_once_with("~/.aws/config", encoding=None)

@patch.dict(os.environ, {"AWS_CONFIG_FILE": "~/.aws/config"})
def test_extract_url_from_environ_variable():
    """
    Testing successful extraction of endpoint url read from file path saved on enviornment variable
    """
    read_data = '\n'.join(["[default]","endpoint_url = http://s3-aws-region.amazonaws.com"])
    with patch("builtins.open", mock_open(read_data=read_data),create=True) as mock_file:
        mock_file.return_value.__iter__.return_value = read_data.splitlines()
        assert (extract_endpoint() == "http://s3-aws-region.amazonaws.com")
        mock_file.assert_called_once_with(os.environ["AWS_CONFIG_FILE"], encoding=None)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()