"""Tests for 'filer.py' general purpose functionalities using 'pytest'."""

# Note: In tests such as 'test_process_file_with_scheme' or
# 'test_copyContent_dir', only the outer function of each unit under testing is
# checked, since mocking a function apparently affects its output. Maybe
# there's a way to bypass that issue and test deeper down the call tree.

import pytest

from tesk_core.filer import (
    process_file,
    copyContent,
    FileProtocolDisabled
)


def test_process_file_no_scheme(caplog):
    """ Ensure that when process_file is called without a scheme and no 
        'HOST_BASE_PATH', 'CONTAINER_BASE_PATH' environment variables
        set, the appropriate error is raised."""

    filedata = {'url': 'www.foo.bar'}

    with pytest.raises(FileProtocolDisabled):
        process_file('upload', filedata)


def test_process_file_with_scheme(mocker):
    """ Ensure expected behaviour when 'process_file' is called with scheme.
        In this test example, scheme is 'http', filedata:type is 'FILE' and
        ttype is 'inputs'."""

    filedata = {
        'url': 'http://www.foo.bar',
        'path': '.',
        'type': 'FILE',
    }
    mock_new_Trans = mocker.patch('tesk_core.filer.newTransput')
    process_file('inputs', filedata)

    mock_new_Trans.assert_called_once_with('http','www.foo.bar')


def test_process_file_from_content(tmpdir, tmp_path):
    """ Ensure 'process_file' behaves correctly when the file contents
        should be drawn from the filedata content field."""

    test_file = tmpdir.join("testfile")
    filedata = {
        'path': str(tmp_path)  + '/testfile',
        'content': 'This is some test content'
    }
    process_file('inputs', filedata)

    assert open(str(tmp_path) + '/testfile', 'r').read() == filedata['content']


def test_copyContent_dir(mocker):
    """Ensure that 'os.listdir' is called when 'copyContent' is called."""

    mock_os_listdir = mocker.patch('os.listdir')
    copyContent('.', '/test_dst')

    mock_os_listdir.assert_called_once_with('.')
