import json
import os
import unittest
from argparse import Namespace
from unittest.mock import patch

from kubernetes.client.rest import ApiException

from tesk.services import taskmaster
from tesk.services.filer_class import Filer
from tesk.services.taskmaster import (
	PVC,
	append_mount,
	dirname,
	generate_mounts,
	init_pvc,
	newParser,
	run_executor,
	run_task,
)


class TaskmasterTest(unittest.TestCase):
	def setUp(self):
		input_file_path = os.path.join(
			os.path.dirname(__file__), 'resources/inputFile.json'
		)
		with open(input_file_path) as file:
			self.data = json.load(file)
		self.task_name = self.data['executors'][0]['metadata']['labels'][
			'taskmaster-name'
		]
		taskmaster.args = Namespace(
			debug=False,
			file=None,
			filer_version='v0.1.9',
			json='json',
			namespace='default',
			poll_interval=5,
			state_file='/tmp/.teskstate',
			localKubeConfig=False,
			pull_policy_always=False,
			filer_name='eu.gcr.io/tes-wes/filer',
			pod_timeout=240,
		)
		self.filer = Filer(
			f'{self.task_name}-filer',
			self.data,
			taskmaster.args.filer_name,
			taskmaster.args.filer_version,
			taskmaster.args.pull_policy_always,
		)
		self.pvc = PVC(
			f'{self.task_name}-pvc',
			self.data['resources']['disk_gb'],
			taskmaster.args.namespace,
		)

		taskmaster.created_jobs = []

	@patch('tesk.services.taskmaster.PVC.create')
	@patch('tesk.services.taskmaster.Job.run_to_completion', return_value='Complete')
	@patch('tesk.services.taskmaster.logger')
	def test_pvc_creation(self, mock_logger, mock_run_to_compl, mock_pvc_create):
		"""
		Testing to check if the PVC volume was created successfully
		"""
		self.assertIsInstance(init_pvc(self.data, self.filer), PVC)

	@patch('kubernetes.client.CoreV1Api.read_namespaced_persistent_volume_claim')
	@patch(
		'kubernetes.client.CoreV1Api.create_namespaced_persistent_volume_claim',
		side_effect=ApiException(status=409, reason='conflict'),
	)
	def test_create_pvc_check_for_conflict_exception(
		self, mock_create_namespaced_pvc, mock_read_namespaced_pvc
	):
		self.pvc.create()
		mock_read_namespaced_pvc.assert_called_once()

	@patch(
		'kubernetes.client.CoreV1Api.create_namespaced_persistent_volume_claim',
		side_effect=ApiException(status=500, reason='Random error'),
	)
	def test_create_pvc_check_for_other_exceptions(self, mock_create_namespaced_pvc):
		with self.assertRaises(ApiException):
			self.pvc.create()

	@patch('tesk.services.taskmaster.PVC.delete')
	@patch('tesk.services.taskmaster.PVC.create')
	@patch('tesk.services.taskmaster.Job.run_to_completion', return_value='error')
	@patch('tesk.services.taskmaster.logger')
	def test_pvc_failure(
		self, mock_logger, run_to_compl, mock_pvc_create, mock_pvc_delete
	):
		"""
		Testcase for finding if the PVC creation failed with exit 0
		"""

		self.assertRaises(SystemExit, init_pvc, self.data, self.filer)

	@patch('tesk.services.taskmaster.PVC.delete')
	@patch('tesk.services.taskmaster.Job.delete')
	@patch('tesk.services.taskmaster.Job.run_to_completion', return_value='Error')
	@patch('tesk.services.taskmaster.logger')
	def test_run_executor_failure(
		self, mock_logger, mock_run_to_compl, mock_job_delete, mock_pvc_delete
	):
		""" """
		self.assertRaises(
			SystemExit,
			run_executor,
			self.data['executors'][0],
			taskmaster.args.namespace,
		)

	@patch('tesk.services.taskmaster.PVC')
	@patch('tesk.services.taskmaster.Job.run_to_completion', return_value='Complete')
	@patch('tesk.services.taskmaster.logger')
	def test_run_executor_complete(self, mock_logger, mock_run_to_compl, mock_pvc):
		""" """
		self.assertEqual(
			run_executor(
				self.data['executors'][0], taskmaster.args.namespace, mock_pvc
			),
			None,
		)

	@patch('tesk.services.taskmaster.logger')
	def test_generate_mount(self, mock_logger):
		""" """
		self.assertIsInstance(generate_mounts(self.data, self.pvc), list)

	@patch('tesk.services.taskmaster.logger')
	def test_append_mount(self, mock_logger):
		""" """
		volume_mounts = []
		task_volume_name = 'task-volume'
		for aninput in self.data['inputs']:
			dirnm = dirname(aninput)
			append_mount(volume_mounts, task_volume_name, dirnm, self.pvc)
		self.assertEqual(
			volume_mounts,
			[
				{
					'name': task_volume_name,
					'mountPath': '/some/volume',
					'subPath': 'dir0',
				}
			],
		)

	@patch('tesk.services.taskmaster.logger')
	@patch('tesk.services.taskmaster.PVC.create')
	@patch('tesk.services.taskmaster.PVC.delete')
	@patch('tesk.services.taskmaster.Job.run_to_completion', return_value='Complete')
	def test_run_task(self, mock_job, mock_pvc_create, mock_pvc_delete, mock_logger):
		""" """
		run_task(self.data, taskmaster.args.filer_name, taskmaster.args.filer_version)

	def test_localKubeConfig(self):
		""" """
		parser = newParser()
		args = parser.parse_args(['json', '--localKubeConfig'])
		self.assertEqual(
			args,
			Namespace(
				debug=False,
				file=None,
				filer_version='v0.1.9',
				json='json',
				namespace='default',
				poll_interval=5,
				state_file='/tmp/.teskstate',
				localKubeConfig=True,
				pull_policy_always=False,
				filer_name='eu.gcr.io/tes-wes/filer',
				pod_timeout=240,
			),
		)


if __name__ == '__main__':
	# import sys;sys.argv = ['', 'Test.testName']
	unittest.main()