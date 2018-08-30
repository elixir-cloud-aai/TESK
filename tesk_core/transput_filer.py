#!/usr/bin/env python3

from __future__ import print_function
from ftplib import FTP
import ftplib
import argparse
import sys
import json
import re
import os
import enum
import distutils.dir_util
import logging
import requests

try:
    from urllib.parse import urlparse
except ModuleNotFoundError:
    from urlparse import urlparse


@enum.unique
class Type(enum.Enum):
    File = 'FILE'
    Directory = 'DIRECTORY'

class Transput:
    def __init__(self, path, url, ftype):
        self.path = path
        self.url = url
        self.ftype = ftype

    def upload(self):
        if self.ftype == Type.File:
            return self.upload_file()
        if self.ftype == Type.Directory:
            return self.upload_dir()
        return 1

    def download(self):
        if self.ftype == Type.File:
            return self.download_file()
        if self.ftype == Type.Directory:
            return self.download_dir()
        return 1

    def delete(self):
        pass

    def download_file(self):
        raise NotImplementedError()

    def download_dir(self):
        raise NotImplementedError()

    def upload_file(self):
        raise NotImplementedError()

    def upload_dir(self):
        raise NotImplementedError()

    # make it compatible with contexts (with keyword)
    def __enter__(self):
        return self

    def __exit__(self, error_type, error_value, traceback):
        self.delete()
        # Swallow all exceptions since the filer mostly works with error codes
        return False

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
            to_upload.append(HTTPTransput(file_path, self.url + '/' + listing, ftype))

        # return 1 if any upload failed
        return min(sum([transput.upload() for transput in to_upload]), 1)

    def download_dir(self):
        logging.error(
            'Won\'t crawl http directory, so unable to download url: %s',
            self.url)
        return 1


class FTPTransput(Transput):
    def __init__(self, path, url, ftype):
        Transput.__init__(self, path, url, ftype)

        parsed_url = urlparse(url)
        self.ftp_baseurl = parsed_url.netloc
        self.ftp_path = parsed_url.path
        self.ftp = FTP(self.ftp_baseurl)

        if 'TESK_FTP_USERNAME' in os.environ and 'TESK_FTP_PASSWORD' in os.environ:
            user = os.environ['TESK_FTP_USERNAME']
            password = os.environ['TESK_FTP_PASSWORD']
            try:
                self.ftp.login(user, password)
            except ftplib.error_perm:
                self.ftp.login()
        else:
            self.ftp.login()

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
                    'Directory listing is neither file nor directory: %s',
                    file_path
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
        try:
            # this will do nothing if directory exists so safe to do always
            logging.debug("in upload_file, self.ftp_path: %s", self.ftp_path)
            create_ftp_dir(os.path.dirname('/' + self.ftp_path), self.ftp)

            # We are NOT scp, so we won't create a file when filename is not
            # specified (mirrors input behaviour)
            try:
                self.ftp.cwd('/' + self.ftp_path)
                logging.error(
                    'Target ftp path /%s already exists and is a folder. \
                    Please specify a target filename and retry',
                    self.ftp_path)
                return 1
            except ftplib.error_perm:
                pass

            with open(self.path, 'r+b') as file:
                self.ftp.storbinary("STOR /" + self.ftp_path, file)
        except:
            logging.error(
                'Unable to store file %s at FTP location /%s',
                self.path,
                self.ftp_path)
            return 1

        return 0

    def download_dir(self):
        logging.debug('Processing ftp dir: %s target: %s', self.url, self.path)
        self.ftp.cwd(self.ftp_path)

        # This is horrible and I'm sorry but it works flawlessly.
        # Credit to Chris Haas for writing this
        # See https://stackoverflow.com/questions/966578/parse-response-from-ftp-list-command-syntax-variations
        # for attribution
        ftp_command = re.compile(
            r'^(?P<dir>[\-ld])(?P<permission>([\-r][\-w][\-xs]){3})\s+(?P<filecode>\d+)\s+(?P<owner>\w+)\s+(?P<group>\w+)\s+(?P<size>\d+)\s+(?P<timestamp>((\w{3})\s+(\d{2})\s+(\d{1,2}):(\d{2}))|((\w{3})\s+(\d{1,2})\s+(\d{4})))\s+(?P<name>.+)$')

        lines = []
        self.ftp.retrlines('LIST', lines.append)

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
            with FTPTransput(file_path, file_url, ftype, self.ftp_connection) as transfer:
                if transfer.download():
                    return 1
        return 0

    def download_file(self):
        logging.debug('Downloading ftp file: "%s" Target: %s', self.url, self.path)
        basedir = os.path.dirname(self.path)
        distutils.dir_util.mkpath(basedir)

        try:
            with open(self.path, 'w+b') as file:
                self.ftp.retrbinary("RETR " + self.ftp_path, file.write)
        except:
            logging.error('Unable to retrieve file')
            return 1
        return 0

    def delete(self):
        self.ftp.close()


def create_ftp_dir(target, ftp):
    # if directory exists do not do anything else
    try:
        ftp.cwd(target)
        return
    except ftplib.error_perm:
        pass

    parent = os.path.dirname(target)
    basename = os.path.basename(target)
    logging.debug('parent: %s, basename: %s', parent, basename)

    if parent == target:  # we have recursed to root, nothing left to do
        raise RuntimeError('Unable to create parent dir')

    try:
        ftp.cwd(parent)
    except:
        logging.error('cannot stat: %s, trying to create parent', parent)
        create_ftp_dir(parent, ftp)

        ftp.cwd(parent)

    logging.debug('Current wd is: %s', ftp.pwd())
    logging.debug('Creating: %s/%s', ftp.pwd(), basename)

    try:
        ftp.mkd(basename)
    except:
        logging.error('Unable to create directory %s/%s', ftp.pwd(), basename)
        raise


def file_from_content(filedata):
    with open(filedata['path'], 'w') as file:
        file.write(str(filedata['content']))

    return 0


def process_file(ttype, filedata):
    if filedata.get('content') is not None:
        return file_from_content(filedata)

    scheme = urlparse(filedata['url']).scheme
    if scheme == '':
        logging.error('Could not determine protocol for url: %s', filedata['url'])
        return 1

    if scheme == 'ftp':
        trans = FTPTransput
    elif scheme in ['http', 'https']:
        trans = HTTPTransput
    else:
        logging.error('Unknown protocol %s', scheme)
        return 1

    with trans(filedata['path'], filedata['url'], filedata['type']) as transfer:
        if ttype == 'inputs':
            return transfer.download()
        if ttype == 'outputs':
            return transfer.upload()

    logging.info('There was no action to do with %s', filedata['path'])
    return 0


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

    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S',
        level=loglevel)

    logging.info('Starting filer...')

    data = json.loads(args.data)

    for afile in data[args.transputtype]:
        logging.debug('processing file: %s', afile['path'])
        if process_file(args.transputtype, afile):
            logging.error('Unable to process all files, aborting')
            return 1
        logging.debug('Processed file: %s', afile['path'])

    return 0


if __name__ == "__main__":
    sys.exit(main())
