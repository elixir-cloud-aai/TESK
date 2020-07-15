import unittest
import json
import os
import sys
import datetime
from unittest.mock import patch
from dateutil.tz import tzutc
from tesk_core import taskmaster
from tesk_core.job import Job
from argparse import Namespace
from datetime import timezone

START_TIME = datetime.datetime.now(timezone.utc)
class MockObject(object):
    def __init__(self, dictionary):
        for k, v in dictionary.items():
            if isinstance(v, dict):
                self.__dict__[k] = MockObject(v)
            else:
                self.__dict__[k] = v

def read_namespaced_job_error(name, namespace):
    return_value = {'active': 1,
                     'completion_time': None,
                     'conditions': None,
                     'failed': None,
                     'start_time': START_TIME - datetime.timedelta(minutes=1),
                     'succeeded': None}
    return MockObject({"status":return_value})


def read_namespaced_job_success(name, namespace):
    return_value = {'active': None,
                 'completion_time': datetime.datetime(2020, 7, 20, 5, 12, 42, tzinfo=tzutc()),
                 'conditions': [MockObject({'last_probe_time': datetime.datetime(2020, 7, 20, 5, 12, 42, tzinfo=tzutc()),
                                 'last_transition_time': datetime.datetime(2020, 7, 20, 5, 12, 42, tzinfo=tzutc()),
                                 'message': None,
                                 'reason': None,
                                 'status': 'True',
                                 'type': 'Complete'})],
                 'failed': None,
                 'start_time': datetime.datetime(2020, 7, 20, 5, 12, 35, tzinfo=tzutc()),
                 'succeeded': 1}
    return  MockObject({"status":return_value})

def list_namespaced_pod_error(namespace, label_selector):
    return_value =  {"status": {"conditions": [{"last_probe_time": None,
                            "last_transition_time": START_TIME- datetime.timedelta(minutes=1),
                            "message": None,
                            "reason": None,
                            "status": "True",
                            "type": "Initialized"},
                           {"last_probe_time": None,
                            "last_transition_time": START_TIME- datetime.timedelta(minutes=1),
                            "message": "containers with unready status: "
                                       "[task-1000-ex-00]",
                            "reason": "ContainersNotReady",
                            "status": "False",
                            "type": "Ready"},
                           {"last_probe_time": None,
                            "last_transition_time": START_TIME- datetime.timedelta(minutes=1),
                            "message": "containers with unready status: "
                                       "[task-1000-ex-00]",
                            "reason": "ContainersNotReady",
                            "status": "False",
                            "type": "ContainersReady"},
                           {"last_probe_time": None,
                            "last_transition_time": START_TIME- datetime.timedelta(minutes=1),
                            "message": None,
                            "reason": None,
                            "status": "True",
                            "type": "PodScheduled"}],
            "container_statuses": [MockObject({"container_id": None,
                                    "image": "ubuntu_mock_test_image",
                                    "image_id": "",
                                    "last_state": {"running": None,
                                                   "terminated": None,
                                                   "waiting": None},
                                    "name": "task-1000-ex-00",
                                    "ready": False,
                                    "restart_count": 0,
                                    "state": {"running": None,
                                              "terminated": None,
                                              "waiting": {"message": "Back-off "
                                                                     "pulling "
                                                                     "image "
                                                                     "ubuntu_mock_test_image",
                                                          "reason": "ImagePullBackOff"}}})],
            "host_ip": "192.168.99.100",
            "init_container_statuses": None,
            "message": None,
            "nominated_node_name": None,
            "phase": "Pending",
            "pod_ip": "172.17.0.5",
            "qos_class": "BestEffort",
            "reason": None,
            "start_time": START_TIME- datetime.timedelta(minutes=1)}}
    return MockObject({"items":[MockObject(return_value)]})

class JobTestCase(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(open(os.path.join(os.path.dirname(__file__), "resources/inputFile.json")).read())
        taskmaster.args = Namespace(debug=False, file=None, filer_version='v0.1.9', json='json'
                                    , namespace='default', poll_interval=5, state_file='/tmp/.teskstate'
                                    , localKubeConfig=False, pull_policy_always=False
                                    , filer_name="eu.gcr.io/tes-wes/filer", pod_timeout=240
                                    )
    def test_job(self):
        job = Job({'metadata': {'name': 'test'}})
        self.assertEqual(job.name, 'task-job')
        self.assertEqual(job.namespace, 'default')

    @patch("kubernetes.client.BatchV1Api.create_namespaced_job")
    @patch("tesk_core.job.Job.get_status", side_effect=[("Running", True),("Running", True),("Running", True),
                                                        ("Running", True),("Running", True),("Complete", True)])
    def test_run_to_completion_success(self, mock_get_status, mock_create_namespaced_job):
        for executor in self.data['executors']:
            jobname = executor['metadata']['name']
            job = Job(executor, jobname, taskmaster.args.namespace)
            status = job.run_to_completion(taskmaster.args.poll_interval, taskmaster.check_cancelled,
                                           taskmaster.args.pod_timeout)
            self.assertEqual(status, "Complete")

    @patch("tesk_core.job.Job.delete")
    @patch("tesk_core.taskmaster.check_cancelled", return_value=True)
    @patch("kubernetes.client.BatchV1Api.create_namespaced_job")
    @patch("tesk_core.job.Job.get_status", side_effect=[("Running", True)])
    def test_run_to_completion_cancelled(self, mock_get_status, mock_create_namespaced_job, mock_check_cancelled,
                               mock_job_delete):
        for executor in self.data['executors']:
            jobname = executor['metadata']['name']
            job = Job(executor, jobname, taskmaster.args.namespace)
            status = job.run_to_completion(taskmaster.args.poll_interval, taskmaster.check_cancelled,
                                           taskmaster.args.pod_timeout)
            self.assertEqual(status, "Cancelled")

    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod", side_effect=list_namespaced_pod_error)
    @patch("kubernetes.client.BatchV1Api.read_namespaced_job", side_effect=read_namespaced_job_error)
    @patch("tesk_core.job.Job.delete")
    @patch("tesk_core.taskmaster.check_cancelled", return_value=False)
    @patch("kubernetes.client.BatchV1Api.create_namespaced_job")
    def test_run_to_completion_error(self, mock_create_namespaced_job, mock_check_cancelled,
                                         mock_job_delete,mock_list_namespaced_pod,  mock_read_namespaced_job):
        for executor in self.data['executors']:
            jobname = executor['metadata']['name']
            job = Job(executor, jobname, taskmaster.args.namespace)
            status = job.run_to_completion(1, taskmaster.check_cancelled,
                                           120)
            self.assertEqual(status, "Error")

    @patch("kubernetes.client.BatchV1Api.read_namespaced_job", side_effect=read_namespaced_job_error)
    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod", side_effect=list_namespaced_pod_error)
    def test_get_status_error(self,mock_list_namespaced_pod,  mock_read_namespaced_job):
        executor = self.data['executors'][0]
        jobname = executor['metadata']['name']
        job = Job(executor, jobname, taskmaster.args.namespace)
        job.timeout = 5
        status, all_pods_running = job.get_status(False)
        self.assertEqual(status,"Error")

    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod")
    @patch("kubernetes.client.BatchV1Api.read_namespaced_job", side_effect=read_namespaced_job_success)
    def test_get_status_success(self, mock_read_namespaced_job, mock_list_namespaced_pod):
        executor = self.data['executors'][0]
        jobname = executor['metadata']['name']
        job = Job(executor, jobname, taskmaster.args.namespace)
        status, all_pods_running = job.get_status(False)
        self.assertEqual(status, "Complete")

if __name__ == '__main__':
    unittest.main()
