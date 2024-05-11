"""Tests for 'filer.py' HTTP functionalities using 'pytest'."""

from requests import Response, put
import os
from unittest import mock

from tesk_core.filer import (
    HTTPTransput,
    Type
)

PATH_DOWN = 'test_download_file.txt'
PATH_UP = 'tests/test_filer_http_pytest.py'
SUCCESS = 200
FAIL = 300
URL = 'http://www.foo.bar'
FTYPE = 'FILE'

resp = Response()
resp._content = b'{ "foo" : "bar" }'


def test_download_file(mocker):
    """ Ensure a file gets properly downloaded."""

    resp.status_code = SUCCESS
    http_obj = HTTPTransput(PATH_DOWN, URL, FTYPE)
    mocker.patch('requests.get', return_value=resp)

    with mock.patch(
            'builtins.open',
            mock.mock_open(read_data=resp._content),
            create=False
    ) as m:
        assert 0 == http_obj.download_file()
        assert open(PATH_DOWN, 'rb').read() == resp._content


def test_download_file_error(mocker, caplog):
    """ Ensure download error returns the correct value and log message."""

    resp.status_code = FAIL
    http_obj = HTTPTransput(PATH_DOWN, URL, FTYPE)
    mocker.patch('requests.get', return_value=resp)

    assert 1 == http_obj.download_file()
    assert 'Got status code: {}'.format(FAIL) in caplog.text


def test_upload_file(mocker):
    """ Ensure a file gets properly uploaded."""

    resp.status_code = SUCCESS
    http_obj = HTTPTransput(PATH_UP, URL, FTYPE)
    mocker.patch('requests.put', return_value=resp)

    assert 0 == http_obj.upload_file()


def test_upload_file_error(mocker, caplog):
    """ Ensure upload error returns the correct value and log message."""

    resp.status_code = FAIL
    http_obj = HTTPTransput(PATH_UP, URL, FTYPE)
    mocker.patch('requests.put', return_value=resp)

    assert 1 == http_obj.upload_file()
    assert 'Got status code: {}'.format(FAIL) in caplog.text


def test_upload_dir(mocker, fs):
    """ Ensure that each file inside nexted directories gets successfully
    uploaded."""
    
    # Tele2 Speedtest Service, free upload /download test server
    endpoint = "http://speedtest.tele2.net/upload.php"
    resp.status_code = 200

    fs.create_dir('dir1')
    fs.create_dir('dir1/dir2')
    fs.create_file('dir1/file1', contents="this is random")
    fs.create_file('dir1/dir2/file2', contents="not really")
    fs.create_file('dir1/dir2/file4.txt', contents="took me a while")


    mock_put = mocker.patch('requests.put', return_value=resp)

    http_obj = HTTPTransput(
        "dir1",
        endpoint + "/dir1",
        Type.Directory
    )

    assert http_obj.upload_dir() == 0

    # We emply the 'list.sorted' trick to ignore calls order because the
    # 'assert_has_calls' method would not work in this setting
    assert sorted(mock_put.mock_calls) == sorted([
        mock.call(endpoint + '/dir1/dir2/file2', data="not really"),
        mock.call(endpoint + '/dir1/dir2/file4.txt', data="took me a while"),
        mock.call(endpoint + '/dir1/file1', data="this is random"),
    ])


    def test_upload_dir_error(mocker, fs):
        """ Ensure 'upload_dir' error returns the correct value. """

        fs.create_dir('dir2')

        # Tele2 Speedtest Service, free upload /download test server
        endpoint1 = "http://speedtest.tele2.net/upload.php"

        # Non-existent endpoint
        endpoint2 = "http://somerandomendpoint.fail"

        http_obj1 = HTTPTransput(
            "dir1",
            endpoint1 + "/dir1",
            Type.Directory
        )

        http_obj2 = HTTPTransput(
            "dir2",
            endpoint2 + "/dir1",
            Type.Directory
        )    

        assert http_obj1.upload_dir() == 1
        assert http_obj2.upload_dir() == 1
