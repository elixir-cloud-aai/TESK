#!/usr/bin/env python2

from __future__ import print_function
import argparse
import json
import os
import re
import sys
import logging
from kubernetes import client, config
from job import Job
from pvc import PVC
from filer_class import Filer

created_jobs = []
poll_interval = 5
task_volume_basename = 'task-volume'


def run_executor(executor, namespace, pvc=None):
    jobname = executor['metadata']['name']
    spec = executor['spec']['template']['spec']

    if pvc is not None:
        spec['containers'][0]['volumeMounts'] = pvc.volume_mounts
        spec['volumes'] = [{'name': task_volume_basename, 'persistentVolumeClaim': {
            'readonly': False, 'claimName': pvc.name}}]

    logger.debug('Created job: ' + jobname)
    job = Job(executor, jobname, namespace)
    logger.debug('Job spec: ' + str(job.body))

    global created_jobs
    created_jobs.append(job)

    status = job.run_to_completion(poll_interval, check_cancelled)
    if status != 'Complete':
        exit_cancelled('Got status ' + status)

# TODO move this code to PVC class


def append_mount(volume_mounts, name, path, pvc):

    # Checks all mount paths in volume_mounts if the path given is already in
    # there
    duplicate = next(
        (mount for mount in volume_mounts if mount['mountPath'] == path),
        None)
    # If not, add mount path
    if duplicate is None:
        subpath = pvc.get_subpath()
        logger.debug(' '.join(
            ['appending' + name +
             'at path' + path +
             'with subPath:' + subpath]))
        volume_mounts.append(
            {'name': name, 'mountPath': path, 'subPath': subpath})


def dirname(iodata):
    if iodata['type'] == 'FILE':
        # strip filename from path
        r = '(.*)/'
        dirname = re.match(r, iodata['path']).group(1)
        logger.debug('dirname of ' + iodata['path'] + 'is: ' + dirname)
    elif iodata['type'] == 'DIRECTORY':
        dirname = iodata['path']

    return dirname


def generate_mounts(data, pvc):
    volume_mounts = []

    # gather volumes that need to be mounted, without duplicates
    volume_name = task_volume_basename
    for volume in data['volumes']:
        append_mount(volume_mounts, volume_name, volume, pvc)

    # gather other paths that need to be mounted from inputs/outputs FILE and
    # DIRECTORY entries
    for aninput in data['inputs']:
        dirnm = dirname(aninput)
        append_mount(volume_mounts, volume_name, dirnm, pvc)

    for anoutput in data['outputs']:
        dirnm = dirname(anoutput)
        append_mount(volume_mounts, volume_name, dirnm, pvc)

    return volume_mounts


def init_pvc(data, filer):
    task_name = data['executors'][0]['metadata']['labels']['taskmaster-name']
    pvc_name = task_name + '-pvc'
    pvc_size = data['resources']['disk_gb']
    pvc = PVC(pvc_name, pvc_size, args.namespace)

    # to global var for cleanup purposes
    global created_pvc
    created_pvc = pvc

    mounts = generate_mounts(data, pvc)
    logging.debug(mounts)
    logging.debug(type(mounts))
    pvc.set_volume_mounts(mounts)

    filer.set_volume_mounts(pvc)
    filerjob = Job(
        filer.get_spec('inputs', args.debug),
        task_name + '-inputs-filer',
        args.namespace)

    global created_jobs
    created_jobs.append(filerjob)
    # filerjob.run_to_completion(poll_interval)
    status = filerjob.run_to_completion(poll_interval, check_cancelled)
    if status != 'Complete':
        exit_cancelled('Got status ' + status)

    return pvc


def run_task(data, filer_version):
    task_name = data['executors'][0]['metadata']['labels']['taskmaster-name']
    pvc = None

    if data['volumes'] or data['inputs'] or data['outputs']:

        filer = Filer(task_name + '-filer', data, filer_version, args.debug)
        if os.environ.get('TESK_FTP_USERNAME') is not None:
            filer.set_ftp(
                os.environ['TESK_FTP_USERNAME'],
                os.environ['TESK_FTP_PASSWORD'])

        pvc = init_pvc(data, filer)

    for executor in data['executors']:
        run_executor(executor, args.namespace, pvc)

    # run executors
    logging.debug("Finished running executors")

    # upload files and delete pvc
    if data['volumes'] or data['inputs'] or data['outputs']:
        filerjob = Job(
            filer.get_spec('outputs', args.debug),
            task_name + '-outputs-filer',
            args.namespace)

        global created_jobs
        created_jobs.append(filerjob)

        # filerjob.run_to_completion(poll_interval)
        status = filerjob.run_to_completion(poll_interval, check_cancelled)
        if status != 'Complete':
            exit_cancelled('Got status ' + status)
        else:
            pvc.delete()


def main(argv):
    parser = argparse.ArgumentParser(description='TaskMaster main module')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        'json',
        help='string containing json TES request, required if -f is not given',
        nargs='?')
    group.add_argument(
        '-f',
        '--file',
        help='TES request as a file or \'-\' for stdin, required if json is not given')

    parser.add_argument(
        '-p',
        '--poll-interval',
        help='Job polling interval',
        default=5)
    parser.add_argument(
        '-fv',
        '--filer-version',
        help='Filer image version',
        default='v0.1.9')
    parser.add_argument(
        '-n',
        '--namespace',
        help='Kubernetes namespace to run in',
        default='default')
    parser.add_argument(
        '-s',
        '--state-file',
        help='State file for state.py script',
        default='/tmp/.teskstate')
    parser.add_argument(
        '-d',
        '--debug',
        help='Set debug mode',
        action='store_true')

    global args
    args = parser.parse_args()

    poll_interval = args.poll_interval

    loglevel = logging.ERROR
    if args.debug:
        loglevel = logging.DEBUG

    global logger
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S',
        level=loglevel)
    logging.getLogger('kubernetes.client').setLevel(logging.CRITICAL)
    logger = logging.getLogger(__name__)
    logger.debug('Starting taskmaster')

    # Get input JSON
    if args.file is None:
        data = json.loads(args.json)
    elif args.file == '-':
        data = json.load(sys.stdin)
    else:
        with open(args.file) as fh:
            data = json.load(fh)

    # Load kubernetes config file
    config.load_incluster_config()

    global created_pvc
    created_pvc = None

    # Check if we're cancelled during init
    if check_cancelled():
        exit_cancelled('Cancelled during init')

    run_task(data, args.filer_version)


def clean_on_interrupt():
    logger.debug('Caught interrupt signal, deleting jobs and pvc')

    for job in created_jobs:
        job.delete()

    if created_pvc:
        created_pvc.delete()


def exit_cancelled(reason='Unknown reason'):
    if created_pvc:
        created_pvc.delete()
    logger.error('Cancelling taskmaster: ' + reason)
    sys.exit(0)


def check_cancelled():
    with open('/podinfo/labels') as fh:
        for line in fh.readlines():
            name, label = line.split('=')
            logging.debug('Got label: ' + label)
            if label == '"Cancelled"':
                return True

    return False


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        clean_on_interrupt()
