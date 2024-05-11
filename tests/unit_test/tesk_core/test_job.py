import unittest
import json
import os
import datetime
from unittest.mock import patch
from dateutil.tz import tzutc
from tesk_core import taskmaster
from tesk_core.job import Job
from argparse import Namespace
from datetime import timezone
from kubernetes.client.rest import ApiException

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
                     'start_time': START_TIME - datetime.timedelta(minutes=10),
                     'succeeded': None}
    return MockObject({"status":return_value})

def read_namespaced_job_pending(diff_time=5):
    return_value = {'active': 1,
                     'completion_time': None,
                     'conditions': None,
                     'failed': None,
                     'start_time': START_TIME - datetime.timedelta(minutes=diff_time),
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

def read_namespaced_job_running(name, namespace):
    """
    if the `conditions` value is `None`, its assumed that the pod is running. Hence the value of `conditions` is
    kept as `None`
    """
    return_value = {'active': None,
                 'completion_time': None,
                 'conditions': None,
                 'failed': None,
                 'start_time': datetime.datetime(2020, 7, 20, 5, 12, 35, tzinfo=tzutc()),
                 'succeeded': None}
    return  MockObject({"status":return_value})

def list_namespaced_pod_error_ImagePullBackOff(diff_time=10):
    return_value =  {"status": {"conditions": [],
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
            "start_time": START_TIME- datetime.timedelta(minutes=diff_time)}}
    return MockObject({"items":[MockObject(return_value)]})

def list_namespaced_pod_pending_unknown_error(diff_time=5):
    return_value =  {"status": {"conditions": [],
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
                                              "waiting": {"message": "Unknown error",
                                                          "reason": "Unknown"}}})],
            "host_ip": "192.168.99.100",
            "init_container_statuses": None,
            "message": None,
            "nominated_node_name": None,
            "phase": "Pending",
            "pod_ip": "172.17.0.5",
            "qos_class": "BestEffort",
            "reason": None,
            "start_time": START_TIME- datetime.timedelta(minutes=diff_time)}}
    return MockObject({"items":[MockObject(return_value)]})

class JobTestCase(unittest.TestCase):
    def setUp(self):
        """
        Initialising
        """
        self.data = json.loads(open(os.path.join(os.path.dirname(__file__), "resources/inputFile.json")).read())
        taskmaster.args = Namespace(debug=False, file=None, filer_version='v0.1.9', json='json'
                                    , namespace='default', poll_interval=5, state_file='/tmp/.teskstate'
                                    , localKubeConfig=False, pull_policy_always=False
                                    , filer_name="eu.gcr.io/tes-wes/filer", pod_timeout=240
                                    )
    def test_job(self):
        """
        Testing if Job object is getting created successfully
        """
        job = Job({'metadata': {'name': 'test'}})
        self.assertEqual(job.name, 'task-job')
        self.assertEqual(job.namespace, 'default')

    @patch("kubernetes.client.BatchV1Api.create_namespaced_job")
    @patch("tesk_core.job.Job.get_status", side_effect=[("Running", True),("Running", True),("Running", True),
                                                        ("Running", True),("Running", True),("Complete", True)])
    def test_run_to_completion_success(self, mock_get_status, mock_create_namespaced_job):
        """
        Checking if the Job runs is completed successfully
        """
        for executor in self.data['executors']:
            jobname = executor['metadata']['name']
            job = Job(executor, jobname, taskmaster.args.namespace)
            status = job.run_to_completion(1, taskmaster.check_cancelled,
                                           taskmaster.args.pod_timeout)
            self.assertEqual(status, "Complete")

    @patch("tesk_core.job.Job.delete")
    @patch("tesk_core.taskmaster.check_cancelled", return_value=True)
    @patch("kubernetes.client.BatchV1Api.create_namespaced_job")
    @patch("tesk_core.job.Job.get_status", side_effect=[("Running", True)])
    def test_run_to_completion_cancelled(self, mock_get_status, mock_create_namespaced_job, mock_check_cancelled,
                               mock_job_delete):
        """
        Checking if the Job is cancelled
        """
        for executor in self.data['executors']:
            jobname = executor['metadata']['name']
            job = Job(executor, jobname, taskmaster.args.namespace)
            status = job.run_to_completion(taskmaster.args.poll_interval, taskmaster.check_cancelled,
                                           taskmaster.args.pod_timeout)
            self.assertEqual(status, "Cancelled")

    @patch("tesk_core.taskmaster.check_cancelled", return_value=False)
    @patch("kubernetes.client.BatchV1Api.create_namespaced_job", side_effect=ApiException(status=409,reason="conflict"))
    @patch("tesk_core.job.Job.get_status", side_effect=[("Complete", True)])
    @patch("kubernetes.client.BatchV1Api.read_namespaced_job", side_effect=read_namespaced_job_running)
    def test_run_to_completion_check_conflict_exception(self, mock_get_status, mock_read_namespaced_job,
                                                        mock_check_cancelled,mock_create_namespaced_job):
        """
        Checking if the Job status is complete when an ApiException of 409 is raised
        """
        for executor in self.data['executors']:
            jobname = executor['metadata']['name']
            job = Job(executor, jobname, taskmaster.args.namespace)
            status = job.run_to_completion(taskmaster.args.poll_interval, taskmaster.check_cancelled,
                                           taskmaster.args.pod_timeout)
            self.assertEqual(status, "Complete")

    @patch("kubernetes.client.BatchV1Api.create_namespaced_job",
           side_effect=ApiException(status=500, reason="Random Exception"))
    def test_run_to_completion_check_other_K8_exception(self,mock_create_namespaced_job):
        """
        Checking if the an exception is raised when ApiException status is other than 409
        """
        for executor in self.data['executors']:
            jobname = executor['metadata']['name']
            job = Job(executor, jobname, taskmaster.args.namespace)
            with self.assertRaises(ApiException):
                job.run_to_completion(taskmaster.args.poll_interval, taskmaster.check_cancelled,
                                               taskmaster.args.pod_timeout)

    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod")
    @patch("kubernetes.client.BatchV1Api.read_namespaced_job", side_effect=read_namespaced_job_error)
    @patch("tesk_core.job.Job.delete")
    @patch("tesk_core.taskmaster.check_cancelled", return_value=False)
    @patch("kubernetes.client.BatchV1Api.create_namespaced_job")
    def test_run_to_completion_error(self, mock_create_namespaced_job, mock_check_cancelled,
                                         mock_job_delete,mock_read_namespaced_job,mock_list_namespaced_pod  ):
        """
        Testing if the job state is 'error' when the status of the pod is in pending
        state and reason is ImagePullBackOff
        """
        mock_list_namespaced_pod.return_value = list_namespaced_pod_error_ImagePullBackOff(10)
        for executor in self.data['executors']:
            jobname = executor['metadata']['name']
            job = Job(executor, jobname, taskmaster.args.namespace)
            status = job.run_to_completion(1, taskmaster.check_cancelled,120)
            self.assertEqual(status, "Error")

    @patch("kubernetes.client.BatchV1Api.read_namespaced_job", side_effect=read_namespaced_job_error)
    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod")
    def test_get_job_status_ImagaPullBackoff_error(self,mock_list_namespaced_pod,  mock_read_namespaced_job):
        """
        Checking whether the job state is 'error', when the pod failed to start and if reason for pod failure
        is ImagePullBackOff
        """
        mock_list_namespaced_pod.return_value = list_namespaced_pod_error_ImagePullBackOff()
        executor = self.data['executors'][0]
        jobname = executor['metadata']['name']
        job = Job(executor, jobname, taskmaster.args.namespace)
        job.timeout = 50
        status, all_pods_running = job.get_status(False)
        self.assertEqual(status,"Error")

    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod")
    @patch("kubernetes.client.BatchV1Api.read_namespaced_job", side_effect=read_namespaced_job_success)
    def test_get_status_success(self, mock_read_namespaced_job, mock_list_namespaced_pod):
        """
        Checking if job status is complete
        """
        executor = self.data['executors'][0]
        jobname = executor['metadata']['name']
        job = Job(executor, jobname, taskmaster.args.namespace)
        status, all_pods_running = job.get_status(False)
        self.assertEqual(status, "Complete")

    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod")
    @patch("kubernetes.client.BatchV1Api.read_namespaced_job", side_effect=read_namespaced_job_running)
    def test_get_status_running(self, mock_read_namespaced_job, mock_list_namespaced_pod):
        """
        Checking if the job is in running state in an ideal situation
        """
        executor = self.data['executors'][0]
        jobname = executor['metadata']['name']
        job = Job(executor, jobname, taskmaster.args.namespace)
        status, all_pods_running = job.get_status(False)
        self.assertEqual(status, "Running")

    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod")
    @patch("kubernetes.client.BatchV1Api.read_namespaced_job")
    def test_get_job_status_for_failed_pod(self, mock_read_namespaced_job, mock_list_namespaced_pod):
        """
        Checking if the job status is 'running' when the pod failed to start with a reason other than ImagePullBackOff.
        """
        mock_list_namespaced_pod.return_value = list_namespaced_pod_pending_unknown_error()
        mock_read_namespaced_job.return_value = read_namespaced_job_pending()
        executor = self.data['executors'][0]
        jobname = executor['metadata']['name']
        job = Job(executor, jobname, taskmaster.args.namespace)
        status, all_pods_running = job.get_status(False)
        self.assertEqual(status, "Running")

    @patch("kubernetes.client.CoreV1Api.list_namespaced_pod")
    @patch("kubernetes.client.BatchV1Api.read_namespaced_job")
    def test_get_job_status_for_wrong_image(self, mock_read_namespaced_job, mock_list_namespaced_pod):
        """
        Assuming image name is wrong, the testcase will check if job status returned from the method is "running"
        during the default pod timeout.
        """
        mock_list_namespaced_pod.return_value = list_namespaced_pod_error_ImagePullBackOff(2)
        mock_read_namespaced_job.return_value = read_namespaced_job_pending(2)
        executor = self.data['executors'][0]
        jobname = executor['metadata']['name']
        job = Job(executor, jobname, taskmaster.args.namespace)
        status, all_pods_running = job.get_status(False)
        self.assertEqual(status, "Running")


if __name__ == '__main__':
    unittest.main()
