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

debug = True


def download_ftp_file(source, target, ftp):
    logging.debug('downloading ftp file: ' + source + ' target: ' + target)
    basedir = os.path.dirname(target)
    distutils.dir_util.mkpath(basedir)

    try:
        ftp.retrbinary("RETR " + source, open(target, 'w').write)
    except:
        logging.error('Unable to retrieve file')
        return 1
    return 0


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

    ftp.mkd(basename)


def process_upload_dir(source, target, ftp):
    logging.debug(
        'processing upload dir src: ' +
        source +
        ' target: ' +
        target)
    #logging.debug('dir basename: '+basename)
    wd = ftp.pwd()
    # does the parent dir exist?
    try:
        ftp.cwd('/' + target)
    except:
        ftp.cwd(wd)
        logging.error('Cannot stat parent dir: /' + target + ', creating...')
        create_ftp_dir(target, ftp)
        ftp.cwd('/' + target)

    basename = os.path.basename(source)
    for f in os.listdir(source):
        path = source + '/' + f
        if os.path.isdir(path):
            process_upload_dir(path, target + '/' + basename + '/', ftp)
        elif os.path.isfile(path):
            logging.debug(
                'Trying to upload file: ' +
                path +
                ' to dest: ' +
                target +
                '/' +
                f)
            try:
                ftp.storbinary("STOR " + target + '/' + f, open(path, 'r'))
            except:
                logging.error('Error trying to upload file')
    return 0


def process_ftp_dir(source, target, ftp):
    logging.debug('processing ftp dir: ' + source + ' target: ' + target)
    pwd = ftp.pwd()
    ftp.cwd('/' + source)

    ls = []
    ftp.retrlines('LIST', ls.append)

    # This is horrible and I'm sorry but it works flawlessly. Credit to Chris Haas for writing this.
    # See https://stackoverflow.com/questions/966578/parse-response-from-ftp-list-command-syntax-variations
    # for attribution
    p = re.compile(
        '^(?P<dir>[\-ld])(?P<permission>([\-r][\-w][\-xs]){3})\s+(?P<filecode>\d+)\s+(?P<owner>\w+)\s+(?P<group>\w+)\s+(?P<size>\d+)\s+(?P<timestamp>((\w{3})\s+(\d{2})\s+(\d{1,2}):(\d{2}))|((\w{3})\s+(\d{1,2})\s+(\d{4})))\s+(?P<name>.+)$')
    for l in ls:
        dirbit = p.match(l).group('dir')
        name = p.match(l).group('name')

        if dirbit == 'd':
            process_ftp_dir(source + '/' + name, target + '/' + name, ftp)
        else:
            download_ftp_file(name, target + '/' + name, ftp)

    ftp.cwd(pwd)


def process_ftp_file(ftype, afile):
    p = re.compile('[a-z]+://([-a-z.]+)/(.*)')
    ftp_baseurl = p.match(afile['url']).group(1)
    ftp_path = p.match(afile['url']).group(2)

    logging.debug('Connecting to FTP: ' + ftp_baseurl)
    ftp = FTP(ftp_baseurl)
    if os.environ.get('TESK_FTP_USERNAME') is not None:
        try:
            user = os.environ['TESK_FTP_USERNAME']
            pw = os.environ['TESK_FTP_PASSWORD']
            ftp.login(user, pw)
        except ftplib.error_perm:
            ftp.login()
    else:
        ftp.login()

    if ftype == 'inputs':
        if afile['type'] == 'FILE':
            return download_ftp_file(ftp_path, afile['path'], ftp)
        elif afile['type'] == 'DIRECTORY':
            return process_ftp_dir(ftp_path, afile['path'], ftp)
        else:
            print('Unknown file type')
            return 1
    elif ftype == 'outputs':
        if afile['type'] == 'FILE':
            try:
                # this will do nothing if directory exists so safe to do always
                create_ftp_dir(os.path.dirname(ftp_path), ftp)

                ftp.storbinary("STOR /" + ftp_path, open(afile['path'], 'r'))
            except:
                logging.error(
                    'Unable to store file ' +
                    afile['path'] +
                    ' at FTP location ' +
                    ftp_path)
                raise
                return 1
            return 0
        elif afile['type'] == 'DIRECTORY':
            return process_upload_dir(afile['path'], ftp_path, ftp)
        else:
            logging.error('Unknown file type: ' + afile['type'])
            return 1
    else:
        logging.error('Unknown file action: ' + ftype)
        return 1


def process_http_file(ftype, afile):
    if ftype == 'inputs':
        r = requests.get(afile['url'])

        if r.status_code != 200:
            logging.error('Got status code: ' + str(r.status_code))
            return 1

        fp = open(afile['path'], 'wb')
        fp.write(r.content)
        fp.close
        return 0
    elif ftype == 'outputs':
        fp = open(afile['path'], 'r')
        r = requests.put(afile['url'], data=fp.read())

        if r.status_code != 200 or r.status_code != 201:
            logging.error('Got status code: ' + str(r.status_code))
            return 1

        fp.close
        return 0
    else:
        print('Unknown action')
        return 1


def filefromcontent(afile):
    content = afile.get('content')
    if content is None:
        logging.error(
            'Incorrect file spec format, no content or url specified')
        return 1

    fh = open(afile['path'], 'w')
    fh.write(str(afile['content']))
    fh.close()
    return 0


def process_file(ftype, afile):
    url = afile.get('url')

    if url is None:
        return filefromcontent(afile)

    p = re.compile('([a-z]+)://')
    protocol = p.match(url).group(1)
    logging.debug('protocol is: ' + protocol)

    if protocol == 'ftp':
        return process_ftp_file(ftype, afile)
    elif protocol == 'http' or protocol == 'https':
        return process_http_file(ftype, afile)
    else:
        print('Unknown file protocol')
        return 1


def debug(msg):
    if debug:
        print(msg, file=sys.stderr)


def main(argv):
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S',
        level=logging.DEBUG)
    logging.debug('Starting filer...')
    parser = argparse.ArgumentParser(
        description='Filer script for down- and uploading files')
    parser.add_argument(
        'filetype',
        help='filetype to handle, either \'inputs\' or \'outputs\' ')
    parser.add_argument(
        'data',
        help='file description data, see docs for structure')
    args = parser.parse_args()

    data = json.loads(args.data)

    for afile in data[args.filetype]:
        logging.debug('processing file: ' + afile['path'])
        if process_file(args.filetype, afile):
            logging.error('something went wrong')
            return 1
        # TODO a bit more detailed reporting
        else:
            logging.debug('Processed file: ' + afile['path'])

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
