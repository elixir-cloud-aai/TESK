import os
import pytest
import boto3
from tesk_core.filer_s3 import S3Transput
from tesk_core.extract_endpoint import extract_endpoint
from moto import mock_s3
from unittest.mock import patch, mock_open

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
    client = boto3.resource('s3', endpoint_url="http://s3.amazonaws.com")
    trans = S3Transput(path, url, ftype)
    trans.bucket_obj = client.Bucket(trans.bucket)
    assert trans.upload_file() == expected
    if expected:
        assert "File upload failed for" in caplog.text
    else:
        '''
        Checking if the file was uploaded, if the object is found, load() method will return None 
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
    client = boto3.resource('s3', endpoint_url="http://s3.amazonaws.com")
    trans = S3Transput(path, url, ftype)
    trans.bucket_obj = client.Bucket(trans.bucket)
    assert trans.upload_dir() == expected
    if expected:
        assert "File upload failed for" in caplog.text
    else:
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
