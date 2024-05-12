import json
import logging
import unittest
from argparse import Namespace
from unittest.mock import patch

from tesk.service.taskmaster import newLogger, newParser, run_task


def pvcCreateMock(self):
	print('[mock] Creating PVC...')


def pvcDeleteMock(self):
	print('[mock] Deleting PVC...')


def jobRunToCompletionMock(job, b, c):
	print(f"[mock] Creating job '{job.name}'...")
	return 'Complete'


class ParserTest(unittest.TestCase):
	def test_defaults(self):
		parser = newParser()

		args = parser.parse_args(['json'])

		print(args)

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
				localKubeConfig=False,
				pull_policy_always=False,
			),
		)

	def test_localKubeConfig(self):
		parser = newParser()

		args = parser.parse_args(['json', '--localKubeConfig'])

		print(args)

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
			),
		)

	def test_pullPolicyAlways(self):
		parser = newParser()

		self.assertEqual(parser.parse_args(['json']).pull_policy_always, False)
		self.assertEqual(
			parser.parse_args(['json', '--pull-policy-always']).pull_policy_always, True
		)

	@patch(
		'service.taskmaster.args',
		Namespace(debug=True, namespace='default', pull_policy_always=True),
	)
	@patch('service.taskmaster.logger', newLogger(logging.DEBUG))
	@patch('service.taskmaster.PVC.create', pvcCreateMock)
	@patch('service.taskmaster.PVC.delete', pvcDeleteMock)
	@patch('service.taskmaster.Job.run_to_completion', jobRunToCompletionMock)
	def test_run_task(self):
		with open('tests/resources/inputFile.json') as fh:
			data = json.load(fh)

		run_task(data, 'filer_version')


if __name__ == '__main__':
	# import sys;sys.argv = ['', 'Test.testName']
	unittest.main()
