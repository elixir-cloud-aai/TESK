#!/usr/bin/env python3

from ftplib import FTP
import ftplib
import argparse
import sys
import json
import re
import os
import distutils.dir_util
import logging
import netrc
import requests
import gzip
from tesk_core.exception import UnknownProtocol, FileProtocolDisabled
import shutil
from glob import glob
from tesk_core.path import containerPath, getPath, fileEnabled
from tesk_core.transput import Type, Transput, urlparse
from tesk_core.filer_s3 import S3Transput




class HTTPTransput(Transput):
    def __init__(self, path, url, ftype):
        Transput.__init__(self, path, url, ftype)

    def download_file(self):
        req = requests.get(self.url)

        if req.status_code < 200 or req.status_code >= 300:
            logging.error('Got status code: %d', req.status_code)
            logging.error(req.text)
            return 1
        logging.debug('OK, got status code: %d', req.status_code)

        with open(self.path, 'wb') as file:
            file.write(req.content)
        return 0

    def upload_file(self):
        with open(self.path, 'r') as file:
            file_contents = file.read()
        req = requests.put(self.url, data=file_contents)

        if req.status_code < 200 or req.status_code >= 300:
            logging.error('Got status code: %d', req.status_code)
            logging.error(req.text)
            return 1
        logging.debug('OK, got status code: %d', req.status_code)

        return 0

    def upload_dir(self):
        to_upload = []
        for listing in os.listdir(self.path):
            file_path = self.path + '/' + listing
            if os.path.isdir(file_path):
                ftype = Type.Directory
            elif os.path.isfile(file_path):
                ftype = Type.File
            else:
                return 1
            to_upload.append(
                HTTPTransput(file_path, self.url + '/' + listing, ftype))

        # return 1 if any upload failed
        return min(sum([transput.upload() for transput in to_upload]), 1)

    def download_dir(self):
        logging.error(
            'Won\'t crawl http directory, so unable to download url: %s',
            self.url)
        return 1


def copyContent(src, dst, symlinks=False, ignore=None):
    '''
    https://stackoverflow.com/a/12514470/1553043
    '''

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def copyDir(src, dst):
    '''
    Limitation of shutil.copytree:

    > The destination directory, named by dst, must not already exist; it will be created as well as missing parent directories.
    '''

    if os.path.exists(dst):

        copyContent(src, dst)

    else:

        shutil.copytree(src, dst)

def copyFile(src, dst):
    '''
    Limitations of shutil.copy:

    It does not interpret * as a glob, but as a character.
    '''

    # If there is any * in 'dst', use only the dirname (base path)
    p = re.compile('.*\*.*')
    if p.match(dst):
        dst=os.path.dirname(dst)

    for file in glob(src):
        shutil.copy(file, dst)


class FileTransput(Transput):
    def __init__(self, path, url, ftype):
        Transput.__init__(self, path, url, ftype)

        self.urlContainerPath = containerPath(getPath(self.url))

    def transfer(self, copyFn, src, dst):
        logging.debug("Copying {src} to {dst}".format(**locals()))
        copyFn(src, dst)

    def download_file(self): self.transfer(shutil.copy  , self.urlContainerPath , self.path)
    def download_dir(self):  self.transfer(copyDir      , self.urlContainerPath , self.path)
    def upload_file(self):   self.transfer(copyFile  , self.path             , self.urlContainerPath)
    def upload_dir(self):    self.transfer(copyDir      , self.path             , self.urlContainerPath)


class FTPTransput(Transput):
    def __init__(self, path, url, ftype, ftp_conn=None):
        Transput.__init__(self, path, url, ftype)

        self.connection_owner = ftp_conn is None
        self.ftp_connection = FTP() if ftp_conn is None else ftp_conn

    # entice users to use contexts when using this class
    def __enter__(self):
        if self.connection_owner:
            self.ftp_connection.connect(self.netloc)
            ftp_login(self.ftp_connection, self.netloc, self.netrc_file)
        return self

    def upload_dir(self):
        for file in os.listdir(self.path):
            file_path = self.path + '/' + file
            file_url = self.url + '/' + file

            if os.path.isdir(file_path):
                ftype = Type.Directory
            elif os.path.isfile(file_path):
                ftype = Type.File
            else:
                logging.error(
                    'Directory listing in is neither file nor directory: "%s"',
                    file_url
                )
                return 1

            logging.debug('Uploading %s\t"%s"', ftype.value, file_path)

            # We recurse into new transputs, ending with files which are uploaded
            # Downside is nothing happens with empty dirs.
            with FTPTransput(file_path, file_url, ftype) as transfer:
                if transfer.upload():
                    return 1
        return 0

    def upload_file(self):
        error = ftp_make_dirs(self.ftp_connection,
                              os.path.dirname(self.url_path))
        if error:
            logging.error(
                'Unable to create remote directories needed for %s',
                self.url
            )
            return 1

        if not ftp_check_directory(self.ftp_connection, self.url_path):
            return 1

        return ftp_upload_file(self.ftp_connection, self.path, self.url_path)

    def download_dir(self):
        logging.debug('Processing ftp dir: %s target: %s', self.url, self.path)
        self.ftp_connection.cwd(self.url_path)

        # This is horrible and I'm sorry but it works flawlessly.
        # Credit to Chris Haas for writing this
        # See https://stackoverflow.com/questions/966578/parse-response-from-ftp-list-command-syntax-variations
        # for attribution
        ftp_command = re.compile(
            r'^(?P<dir>[\-ld])(?P<permission>([\-r][\-w][\-xs]){3})\s+(?P<filecode>\d+)\s+(?P<owner>\w+)\s+(?P<group>\w+)\s+(?P<size>\d+)\s+(?P<timestamp>((\w{3})\s+(\d{2})\s+(\d{1,2}):(\d{2}))|((\w{3})\s+(\d{1,2})\s+(\d{4})))\s+(?P<name>.+)$')

        lines = []
        self.ftp_connection.retrlines('LIST', lines.append)

        for line in lines:
            matches = ftp_command.match(line)
            dirbit = matches.group('dir')
            name = matches.group('name')

            file_path = self.path + '/' + name
            file_url = self.url + '/' + name

            if dirbit == 'd':
                ftype = Type.Directory
            else:
                ftype = Type.File

            # We recurse into new transputs, ending with files which are downloaded
            # Downside is nothing happens with empty dirs.
            with FTPTransput(file_path, file_url, ftype,
                             self.ftp_connection) as transfer:
                if transfer.download():
                    return 1
        return 0

    def download_file(self):
        logging.debug('Downloading ftp file: "%s" Target: %s', self.url,
                      self.path)
        basedir = os.path.dirname(self.path)
        distutils.dir_util.mkpath(basedir)

        return ftp_download_file(self.ftp_connection, self.url_path, self.path)

    def delete(self):
        if self.connection_owner:
            self.ftp_connection.close()


def ftp_login(ftp_connection, netloc, netrc_file):
    user = None
    if netrc_file is not None:
        creds = netrc_file.authenticators(netloc)
        if creds:
            user, _, password = creds
    elif 'TESK_FTP_USERNAME' in os.environ and 'TESK_FTP_PASSWORD' in os.environ:
        user = os.environ['TESK_FTP_USERNAME']
        password = os.environ['TESK_FTP_PASSWORD']

    if user:
        try:
            ftp_connection.login(user, password)
        except ftplib.error_perm:
            ftp_connection.login()
    else:
        ftp_connection.login()


def ftp_check_directory(ftp_connection, path):
    """
    Following convention with the rest of the code,
    return 0 if it is a directory, 1 if it is not or failed to do the check
    """
    response = ftp_connection.pwd()
    if response == '':
        return 1
    original_directory = response

    # We are NOT scp, so we won't create a file when filename is not
    # specified (mirrors input behaviour)
    try:
        ftp_connection.cwd(path)
        logging.error(
            'Path "%s" at "%s" already exists and is a folder. \
            Please specify a target filename and retry',
            path, ftp_connection.host)
        is_directory = True
    except ftplib.error_perm:
        is_directory = False
    except (ftplib.error_reply, ftplib.error_temp):
        logging.exception('Could not check if path "%s" in "%s" is directory',
                          path, ftp_connection.host)
        return 1
    try:
        ftp_connection.cwd(original_directory)
    except (ftplib.error_reply, ftplib.error_perm, ftplib.error_temp):
        logging.exception(
            'Error when checking if "%s" in "%s" was a directory',
            path, ftp_connection.host)
        return 1

    return 0 if is_directory else 1


def ftp_upload_file(ftp_connection, local_source_path,
                    remote_destination_path):
    try:
        with open(local_source_path, 'r+b') as file:
            ftp_connection.storbinary("STOR /" + remote_destination_path, file)
    except (ftplib.error_reply, ftplib.error_perm, ftplib.error_temp):
        logging.exception(
            'Unable to upload file "%s" to "%s" as "%s"',
            local_source_path,
            ftp_connection.host,
            remote_destination_path)
        return 1
    return 0


def ftp_download_file(ftp_connection, remote_source_path,
                      local_destination_path):
    try:
        with open(local_destination_path, 'w+b') as file:
            ftp_connection.retrbinary("RETR " + remote_source_path, file.write)
    except (ftplib.error_reply, ftplib.error_perm, ftplib.error_temp):
        logging.exception(
            'Unable to download file "%s" from "%s" as "%s"',
            remote_source_path,
            ftp_connection.host,
            local_destination_path
        )
        return 1
    return 0


def subfolders_in(whole_path):
    """
    Returns all subfolders in a path, in order

    >>> subfolders_in('/')
    ['/']

    >>> subfolders_in('/this/is/a/path')
    ['/this', '/this/is', '/this/is/a', '/this/is/a/path']

    >>> subfolders_in('this/is/a/path')
    ['this', 'this/is', 'this/is/a', 'this/is/a/path']
    """
    path_fragments = whole_path.lstrip('/').split('/')
    if whole_path.startswith('/'):
        path_fragments[0] = '/' + path_fragments[0]
    path = path_fragments[0]
    subfolders = [path]
    for fragment in path_fragments[1:]:
        path += '/' + fragment
        subfolders.append(path)
    return subfolders


def ftp_make_dirs(ftp_connection, path):
    response = ftp_connection.pwd()
    if response == '':
        return 1
    original_directory = response

    # if directory exists do not do anything else
    try:
        ftp_connection.cwd(path)
        return 0
    except (ftplib.error_perm, ftplib.error_temp):
        pass
    except ftplib.error_reply:
        logging.exception('Unable to create directory "%s" at "%s"',
                          path, ftp_connection.host)
        return 1

    for subfolder in subfolders_in(path):
        try:
            ftp_connection.cwd(subfolder)
        except (ftplib.error_perm, ftplib.error_temp):
            try:
                ftp_connection.mkd(subfolder)
            except (ftplib.error_reply, ftplib.error_perm, ftplib.error_temp):
                logging.exception('Unable to create directory "%s" at "%s"',
                                  subfolder, ftp_connection.host)
                return 1
        except ftplib.error_reply:
            logging.exception('Unable to create directory "%s" at "%s"',
                              path, ftp_connection.host)
            return 1

    try:
        ftp_connection.cwd(original_directory)
    except (ftplib.error_reply, ftplib.error_perm, ftplib.error_temp):
        logging.exception('Unable to create directory "%s" at "%s"',
                          path, ftp_connection.host)
        return 1
    return 0


def file_from_content(filedata):
    with open(filedata['path'], 'w') as file:
        file.write(str(filedata['content']))
    return 0



def newTransput(scheme, netloc):
    def fileTransputIfEnabled():

        if fileEnabled():
            return FileTransput
        else:
            raise FileProtocolDisabled("'file:' protocol disabled\n"
                                       "To enable it, both '{}' and '{}' environment variables must be defined."
                                       .format('HOST_BASE_PATH',
                                               'CONTAINER_BASE_PATH')
                                       )

    if scheme == 'ftp':
        return FTPTransput
    elif scheme == 'file':
        return fileTransputIfEnabled()
    elif scheme in ['http', 'https']:
        if 's3' in netloc:
            return S3Transput
        return HTTPTransput
    elif scheme == 's3':
        return S3Transput
    else:
        raise UnknownProtocol("Unknown protocol: '{scheme}'".format(**locals()))


def process_file(ttype, filedata):
    '''
    @param ttype: str
           Can be 'inputs' or 'outputs'
    '''

    if 'content' in filedata:
        return file_from_content(filedata)
    parsed_url = urlparse(filedata['url'])
    scheme = parsed_url.scheme
    netloc = parsed_url.netloc
    if scheme == '':
        logging.info('Could not determine protocol for url: "%s", assuming "file"', filedata['url'])
        scheme='file'

    trans = newTransput(scheme, netloc)

    with trans(filedata['path'], filedata['url'],
               Type(filedata['type'])) as transfer:
        if ttype == 'inputs':
            return transfer.download()
        if ttype == 'outputs':
            return transfer.upload()

    logging.info('There was no action to do with %s', filedata['path'])
    return 0


def logConfig(loglevel):
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S',
                        level=loglevel,
                        stream=sys.stdout)


def main():
    parser = argparse.ArgumentParser(
        description='Filer script for down- and uploading files')
    parser.add_argument(
        'transputtype',
        help='transput to handle, either \'inputs\' or \'outputs\' ')
    parser.add_argument(
        'data',
        help='file description data, see docs for structure')
    parser.add_argument(
        '--debug',
        '-d',
        help='debug logging',
        action='store_true')
    args = parser.parse_args()

    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.ERROR

    logConfig(loglevel)

    logging.info('Starting %s filer...', args.transputtype)

    if args.data.endswith('.gz'):
        with gzip.open(args.data, 'rb') as fh:
            data = json.loads(fh.read())
    else:
        data = json.loads(args.data)

    for afile in data[args.transputtype]:
        logging.debug('Processing file: %s', afile['path'])
        if process_file(args.transputtype, afile):
            logging.error('Unable to process file, aborting')
            return 1
        logging.debug('Processed file: %s', afile['path'])

    return 0


if __name__ == "__main__":
    sys.exit(main())
