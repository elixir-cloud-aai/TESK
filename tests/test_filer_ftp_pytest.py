""" Tests for 'filer.py' FTP functionalities using 'pytest'."""

from unittest import mock
import ftplib
import os

from tesk_core.filer import (
    FTPTransput,
    Type,
    ftp_login,
    ftp_upload_file,
    ftp_download_file,
    ftp_check_directory,
    ftp_make_dirs
)


def test_ftp_login(mocker):
    """ Ensure ftp_login detects ftp credentials and properly calls
        ftplib.FTP.login."""

    conn = mocker.patch('ftplib.FTP')
    mock_login = mocker.patch('ftplib.FTP.login')
    with mock.patch.dict(
            'os.environ',
            {
                'TESK_FTP_USERNAME': 'test',
                'TESK_FTP_PASSWORD': 'test_pass',
            }
    ):
        ftp_login(conn, None, None)
        mock_login.assert_called_with('test', 'test_pass')


def test_ftp_upload_file_error(mocker, caplog):
    """ Ensure that upon upload error, ftp_upload_file behaves correctly."""

    conn = mocker.patch('ftplib.FTP')
    mocker.patch('ftplib.FTP.storbinary', side_effect=ftplib.error_reply)
    assert 1 == ftp_upload_file(conn,
                                'tests/test_filer.py',
                                '/home/tesk/test_copy.py')
    assert 'Unable to upload file' in caplog.text


def test_ftp_download_file_error(mocker, caplog):
    """ Ensure that upon download error, ftp_download_file behaves correctly.
    """

    conn = mocker.patch('ftplib.FTP')
    mocker.patch('ftplib.FTP.retrbinary', side_effect=ftplib.error_perm)
    with mock.patch('builtins.open', mock.mock_open(), create=False) as m:
        assert 1 == ftp_download_file(conn,
                                      'test_filer_ftp_pytest.py',
                                      'test_copy.py')
        assert 'Unable to download file' in caplog.text


def test_ftp_download_file_success(mocker, caplog):
    """ Ensure that upon successful download, the local destination file has
        been created."""

    conn = mocker.patch('ftplib.FTP')
    mock_retrbin = mocker.patch('ftplib.FTP.retrbinary')
    with mock.patch('builtins.open', mock.mock_open(), create=False) as m:
        assert 0 == ftp_download_file(conn,
                                      'test_filer_ftp_pytest.py',
                                      'test_copy.py')

        mock_retrbin.assert_called_with(
            "RETR " + "test_filer_ftp_pytest.py",
            mock.ANY
        )

        m.assert_called_with('test_copy.py', 'w+b')

        # Since we want to avoid file creation in testing and we're using
        # 'create=False', we cannot check whether a file exists or not (but
        # it's not really necessary since we can assert that the necessary
        # functions have been invoked.
        # assert os.path.exists('test_copy.py')


def test_ftp_upload_dir(mocker, fs, ftpserver):
    """ Check whether the upload of a directory through FTP completes
        successfully. """

    # Fake local nested directories with files
    fs.create_dir('dir1')
    fs.create_dir('dir1/dir2')
    fs.create_file('dir1/file1', contents="this is random")
    fs.create_file('dir1/dir2/file2', contents="not really")
    fs.create_file('dir1/dir2/file4.txt', contents="took me a while")

    login_dict = ftpserver.get_login_data()

    conn = ftplib.FTP()

    mocker.patch('ftplib.FTP.connect',
        side_effect=conn.connect(
            host=login_dict['host'],
            port=login_dict['port']
            )
        )
    mocker.patch(
        'ftplib.FTP.login',
        side_effect=conn.login(login_dict['user'], login_dict['passwd'])
        )
    mocker.patch('ftplib.FTP.pwd', side_effect=conn.pwd)
    mocker.patch('ftplib.FTP.cwd', side_effect=conn.cwd)
    mocker.patch('ftplib.FTP.mkd', side_effect=conn.mkd)
    mock_storbinary = mocker.patch('ftplib.FTP.storbinary')

    ftp_obj = FTPTransput(
        "dir1",
        "ftp://" + login_dict['host'] + "/dir1",
        Type.Directory,
        ftp_conn=conn
    )

    ftp_obj.upload_dir()

    # We use mock.ANY since the 2nd argument of the 'ftplib.FTP.storbinary' is
    # a file object and we can't have the same between the original and the
    # mock calls
    assert sorted(mock_storbinary.mock_calls) == sorted([
        mock.call('STOR /' + '/dir1/file1', mock.ANY),
        mock.call('STOR /' + '/dir1/dir2/file2', mock.ANY),
        mock.call('STOR /' + '/dir1/dir2/file4.txt', mock.ANY)
    ])


def test_ftp_download_dir(mocker, tmpdir, tmp_path, ftpserver):
    """ Check whether the download of a directory through FTP completes
        successfully. """

    # Temporary nested directories with files
    file1 = tmpdir.mkdir("dir1").join("file1")
    file1.write("this is random")
    file2 = tmpdir.mkdir("dir1/dir2").join("file2")
    file2.write('not really')
    file3 = tmpdir.join('dir1/dir2/file3')
    file3.write('took me a while')

    # Temporary folder for download
    tmpdir.mkdir('downloads')

    # Populate the server with the above files to later download
    ftpserver.put_files({
        'src': str(tmp_path) + '/dir1/file1',
        'dest': 'remote1/file1'
        })
    ftpserver.put_files({
        'src': str(tmp_path) + '/dir1/dir2/file2',
        'dest': 'remote1/remote2/file2'
        })
    ftpserver.put_files({
        'src': str(tmp_path) +  '/dir1/dir2/file3',
        'dest': 'remote1/remote2/file3'
        })

    login_dict = ftpserver.get_login_data()

    conn = ftplib.FTP()
    conn.connect(host=login_dict['host'], port=login_dict['port'])
    conn.login(login_dict['user'], login_dict['passwd'])

    mock_retrbinary = mocker.patch(
        'ftplib.FTP.retrbinary',
        side_effect=conn.retrbinary
        )

    ftp_obj = FTPTransput(
        str(tmp_path) + "downloads",
        "ftp://" + login_dict['host'],
        Type.Directory,
        ftp_conn=conn
        ) 

    ftp_obj.download_dir()

    # We use mock.ANY since the 2nd argument of the 'ftplib.FTP.storbinary' is
    # a file object and we can't have the same between the original and the
    # mock calls
    assert sorted(mock_retrbinary.mock_calls) == sorted([
        mock.call('RETR ' + '/remote1/file1', mock.ANY),
        mock.call('RETR ' + '/remote1/remote2/file2', mock.ANY),
        mock.call('RETR ' + '/remote1/remote2/file3', mock.ANY)      
    ])

    assert os.path.exists(str(tmp_path) + 'downloads/remote1/file1')
    assert os.path.exists(str(tmp_path) + 'downloads/remote1/remote2/file2')
    assert os.path.exists(str(tmp_path) + 'downloads/remote1/remote2/file3')


def test_ftp_check_directory_error(mocker, caplog):
    """Ensure ftp_check_directory_error creates the proper error log
    message in case of error."""

    conn = mocker.patch('ftplib.FTP')
    mocker.patch('ftplib.FTP.cwd', side_effect=ftplib.error_reply)
    assert 1 == ftp_check_directory(conn, '/folder/file')
    assert 'Could not check if path' in caplog.text


def test_ftp_make_dirs(mocker):
    """ In case of existing directory, exit with 0. """

    conn = mocker.patch('ftplib.FTP')
    assert ftp_make_dirs(conn, os.curdir) == 0


def test_ftp_make_dirs_error(mocker, ftpserver, caplog):
    """ Ensure in case of 'ftplib.error_reply', both the return value
        and the error message are correct. """

    login_dict = ftpserver.get_login_data()

    conn = ftplib.FTP()
    conn.connect(host=login_dict['host'], port=login_dict['port'])
    conn.login(login_dict['user'], login_dict['passwd'])

    mocker.patch('ftplib.FTP.cwd', side_effect=ftplib.error_reply)

    assert ftp_make_dirs(conn, 'dir1') == 1
    assert 'Unable to create directory' in caplog.text
