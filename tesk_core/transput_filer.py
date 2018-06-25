#!/usr/bin/env python3

from __future__ import print_function
from ftplib import FTP
import ftplib
import argparse
import sys
import json
import re
import os
import distutils.dir_util
import logging
import requests
from io import BytesIO


class Transput:
    def __init__(self, path, url, ftype):
        self.path = path
        self.url = url
        self.ftype = ftype

    def upload(self):
        if self.ftype == 'FILE':
            return self.upload_file()
        if self.ftype == 'DIRECTORY':
            return self.upload_dir()

    def download(self):
        if self.ftype == 'FILE':
            return self.download_file()
        if self.ftype == 'DIRECTORY':
            return self.download_dir()

    def delete(self):
        pass


class HTTPTransput(Transput):
    def __init__(self, path, url, ftype):
        Transput.__init__(self, path, url, ftype)

    def download_file(self):
        r = requests.get(self.url)

        if r.status_code < 200 or r.status_code >= 300:
            logging.error('Got status code: ' + str(r.status_code))
            logging.error(r.text)
            return 1
        else:
            logging.debug('OK, got status code: ' + str(r.status_code))

        fp = open(self.path, 'wb')
        fp.write(r.content)
        fp.close
        return 0

    def upload_file(self):
        fp = open(self.path, 'r')
        r = requests.put(self.url, data=fp.read())

        if r.status_code < 200 or r.status_code >= 300:
            logging.error('Got status code: ' + str(r.status_code))
            logging.error(r.text)
            return 1
        else:
            logging.debug('OK, got status code: ' + str(r.status_code))

        fp.close
        return 0

    def upload_dir(self):
        for f in os.listdir(self.path):
            fpath = self.path + '/' + f
            if os.path.isdir(fpath):
                ftype = 'DIRECTORY'
            if os.path.isfile(fpath):
                ftype = 'FILE'

        return HTTPTransput(fpath, self.url + '/' + f, ftype).upload()

    def download_dir(self):
        logging.error(
            'Won\'t crawl http directory, so unable to download url: ' +
            self.url)
        return 1


class FTPTransput(Transput):
    def __init__(self, path, url, ftype):
        Transput.__init__(self, path, url, ftype)

        p = re.compile('[a-z]+://([-a-z.]+)/(.*)')
        self.ftp_baseurl = p.match(url).group(1)
        self.ftp_path = p.match(url).group(2)
        self.ftp = FTP(self.ftp_baseurl)

        if os.environ.get('TESK_FTP_USERNAME') is not None:
            try:
                user = os.environ['TESK_FTP_USERNAME']
                pw = os.environ['TESK_FTP_PASSWORD']
                self.ftp.login(user, pw)
            except ftplib.error_perm:
                self.ftp.login()
        else:
            self.ftp.login()

    def upload_dir(self):
        for f in os.listdir(self.path):
            fpath = self.path + '/' + f
            newurl = self.url + '/' + f
            if os.path.isdir(fpath):
                ftype = 'DIRECTORY'
            if os.path.isfile(fpath):
                ftype = 'FILE'

            logging.debug(''.join([
                "in upload_dir, fpath:" + fpath +
                "ftype is:" + ftype
            ]))

            # We recurse into new transputs, ending with files which are uploaded
            # Downside is nothing happens with empty dirs.
            t = FTPTransput(fpath, newurl, ftype)
            if t.upload():
                return 1
            t.delete()

    def upload_file(self):
        try:
            # this will do nothing if directory exists so safe to do always
            logging.debug("in upload_file, self.ftp_path: " + self.ftp_path)
            create_ftp_dir(os.path.dirname('/' + self.ftp_path), self.ftp)

            # We are NOT scp, so we won't create a file when filename is not
            # specified (mirrors input behaviour)
            try:
                self.ftp.cwd('/' + self.ftp_path)
                logging.error(
                    'Target ftp path /' + self.ftp_path +
                    ' already exists and is a folder. Please specify a target filename and retry')
                return 1
            except:
                pass

            fp = open(self.path, 'r+b')
            self.ftp.storbinary("STOR /" + self.ftp_path, fp)
            fp.close()
        except:
            logging.error(
                'Unable to store file ' + self.path +
                ' at FTP location /' + self.ftp_path)
            raise
            return 1

        return 0

    def download_dir(self):
        logging.debug(' '.join([
            'processing ftp dir: ' + self.url +
            ' target: ' + self.path]))
        self.ftp.cwd(self.ftp_path)

        # This is horrible and I'm sorry but it works flawlessly. Credit to Chris Haas for writing this
        # See https://stackoverflow.com/questions/966578/parse-response-from-ftp-list-command-syntax-variations
        # for attribution
        p = re.compile(
            '^(?P<dir>[\-ld])(?P<permission>([\-r][\-w][\-xs]){3})\s+(?P<filecode>\d+)\s+(?P<owner>\w+)\s+(?P<group>\w+)\s+(?P<size>\d+)\s+(?P<timestamp>((\w{3})\s+(\d{2})\s+(\d{1,2}):(\d{2}))|((\w{3})\s+(\d{1,2})\s+(\d{4})))\s+(?P<name>.+)$')

        ls = []
        self.ftp.retrlines('LIST', ls.append)

        for l in ls:
            dirbit = p.match(l).group('dir')
            name = p.match(l).group('name')

            fpath = self.path + '/' + name
            newurl = self.url + '/' + name

            if dirbit == 'd':
                ftype = 'DIRECTORY'
            else:
                ftype = 'FILE'

            # We recurse into new transputs, ending with files which are downloaded
            # Downside is nothing happens with empty dirs.
            t = FTPTransput(fpath, newurl, ftype)
            if t.download():
                return 1
            t.delete()

    def download_file(self):
        logging.debug(' '.join([
            'downloading ftp file:' + self.url +
            'target:' + self.path]))
        basedir = os.path.dirname(self.path)
        distutils.dir_util.mkpath(basedir)

        try:
            fp = open(self.path, 'w+b')
            self.ftp.retrbinary("RETR " + self.ftp_path, fp.write)
            fp.close()
        except:
            logging.error('Unable to retrieve file')
            raise
            return 1
        return 0

    def delete(self):
        self.ftp.close()


def create_ftp_dir(target, ftp):
    # check if directory exists, if yes just return
    try:
        ftp.cwd(target)
        return
    except ftplib.error_perm:
        pass

    parent = os.path.dirname(target)
    basename = os.path.basename(target)
    logging.debug('parent: ' + parent + ', basename: ' + basename)

    if parent == target:  # we have recursed to root, nothing left to do
        raise RuntimeError('Unable to create parent dir')
    try:
        ftp.cwd(parent)
    except:
        logging.error('cannot stat: ' + parent + ', trying to create parent')
        create_ftp_dir(parent, ftp)
        ftp.cwd(parent)

    logging.debug('Current wd is: ' + ftp.pwd())
    logging.debug('Creating: ' + ftp.pwd() + '/' + basename)

    try:
        ftp.mkd(basename)
    except:
        logging.error(
            'Unable to create directory ' + ftp.pwd() +
            '/' + basename)
        raise


def file_from_content(filedata):
    fh = open(filedata['path'], 'w')
    fh.write(str(filedata['content']))
    fh.close()

    return 0


def process_file(ttype, filedata):
    if filedata.get('content') is not None:
        return file_from_content(filedata)

    try:
        protocol = re.match('([a-z]+)://', filedata['url']).group(1)
    except AttributeError:
        logging.error(
            'Could not determine protocol for url: ' +
            filedata['url'])
        return 1

    if protocol == 'ftp':
        t = FTPTransput(filedata['path'], filedata['url'], filedata['type'])
    elif protocol == 'http' or protocol == 'https':
        t = HTTPTransput(filedata['path'], filedata['url'], filedata['type'])
    else:
        logging.error('Unknown protocol ' + protocol)
        return 1

    if ttype == 'inputs':
        return t.download()
    if ttype == 'outputs':
        return t.upload()

    t.delete()


def main(argv):
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
    logging.debug('Starting filer...')

    data = json.loads(args.data)

    for afile in data[args.transputtype]:
        logging.debug('processing file: ' + afile['path'])
        if process_file(args.transputtype, afile):
            logging.error('Unable to process all files, aborting')
            return 1
        else:
            logging.debug('Processed file: ' + afile['path'])

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
