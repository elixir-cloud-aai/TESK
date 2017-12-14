#!/usr/bin/python

from __future__ import print_function
from ftplib import FTP
import argparse
import requests
import sys
import json
import re
import os

def process_ftp_file(ftype, afile):
  p = re.compile('[a-z]+://([-a-z.]+)/(.*)')
  ftp_baseurl = p.match(afile['url']).group(1)
  ftp_path = p.match(afile['url']).group(2)

  ftp = FTP(ftp_baseurl)
  if os.environ.get('TESK_FTP_USERNAME') is not None:
    user = os.environ['TESK_FTP_USERNAME']
    pw   = os.environ['TESK_FTP_PASSWORD']
    ftp.login(user, pw)
  else:
    ftp.login()

  if ftype == 'inputs':
    ftp.retrbinary("RETR "+ftp_path, open(afile['path'], 'w').write)
    return 0
  elif ftype == 'outputs':
    ftp.storbinary("STOR "+ftp_path, open(afile['path'], 'r'))
    return 0
  else:
    print('Unknown file action')
    return 1

def process_http_file(ftype, afile):
  if ftype == 'inputs':
    r = requests.get(afile['url'])
    fp = open(afile['path'], 'wb')
    fp.write(r.content)
    fp.close
    return 0
  elif ftype == 'outputs':
    fp = open(afile['path'], 'r')
    r = requests.put(afile['url'], data=fp.read())
    fp.close
    return 0
  else:
    print('Unknown action')
    return 1

def process_file(ftype, afile):
  url = afile['url']
  p = re.compile('([a-z]+)://')
  protocol = p.match(url).group(1)
  #print(protocol, file=sys.stderr)

  if protocol == 'ftp':
    return process_ftp_file(ftype, afile)
  elif protocol == 'http' or protocol == 'https':
    return process_http_file(ftype, afile)
  else:
    print('Unknown file protocol')
    return 1

def main(argv):
  parser = argparse.ArgumentParser(description='Filer script for down- and uploading files')
  parser.add_argument('data', help='file description data, see docs for structure')
  args = parser.parse_args()

  data = json.loads(args.data)

  if data.get('outputs') is not None:
    ftype = 'outputs'
  else:
    ftype = 'inputs'
  
  for afile in data[ftype]:
    if process_file(ftype, afile):
      print('something went wrong', file=sys.stderr)
      return 1
    else:
      print('Processed file: ' + afile['url'], file=sys.stderr)

  return 0
if __name__ == "__main__":
  main(sys.argv)
