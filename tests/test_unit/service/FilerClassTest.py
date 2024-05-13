import os
import unittest

from tesk.service import path
from tesk.service.filer_class import Filer
from tesk.service.Util import pprint

try:
	from unittest.mock import patch  # Python 3 @UnresolvedImport
except ImportError:
	from unittest.mock import patch


@patch('tesk.service.path.HOST_BASE_PATH', '/home/tfga/workspace/cwl-tes')
@patch('tesk.service.path.CONTAINER_BASE_PATH', '/transfer')
@patch('tesk.service.path.TRANSFER_PVC_NAME', 'transfer-pvc')
@patch.dict(
	os.environ,
	{
		'AWS_SHARED_CREDENTIALS_FILE': '/aws/credentials',
		'AWS_CONFIG_FILE': '/aws/config',
	},
)
class FilerClassTest_env(unittest.TestCase):
	def test_env_vars(self):
		f = Filer('name', {'a': 1})
		f.set_backoffLimit(10)

		pprint(f.spec)

		self.assertEqual(
			f.getEnv(),
			[
				{'name': 'JSON_INPUT', 'value': '{"a": 1}'},
				{'name': 'HOST_BASE_PATH', 'value': '/home/tfga/workspace/cwl-tes'},
				{'name': 'CONTAINER_BASE_PATH', 'value': '/transfer'},
				{'name': 'AWS_CONFIG_FILE', 'value': '/aws/config'},
				{'name': 'AWS_SHARED_CREDENTIALS_FILE', 'value': '/aws/credentials'},
			],
		)
		self.assertEqual(f.spec['spec']['backoffLimit'], 10)

	def test_mounts(self):
		"""
		kind: Pod
		apiVersion: v1
		metadata:
			name: tfga-pod
		spec:
			containers:
				- name: tfga-container
					image: eu.gcr.io/tes-wes/filer:testing
					volumeMounts:
						- mountPath: /transfer
							name: transfer-volume
			volumes:
				- name: transfer-volume
					hostPath:
						path: /transferAtNode
					# persistentVolumeClaim:
					#  claimName: task-pv-claim
		"""

		f = Filer('name', {'a': 1})

		pprint(f.spec)

		pprint(f.getVolumeMounts())

		self.assertEqual(
			f.getVolumeMounts(),
			[
				{
					'name': 'transfer-volume',
					'mountPath': path.CONTAINER_BASE_PATH,
				},
				{'mountPath': '/aws', 'name': 's3-conf', 'readOnly': True},
			],
		)

		self.assertEqual(
			f.getVolumes(),
			[
				{
					'name': 'transfer-volume',
					'persistentVolumeClaim': {'claimName': 'transfer-pvc'},
				},
				{
					'name': 's3-conf',
					'secret': {
						'secretName': 'aws-secret',
						'items': [
							{'key': 'credentials', 'path': 'credentials'},
							{'key': 'config', 'path': 'config'},
						],
						'optional': True,
					},
				},
			],
		)


class FilerClassTest_no_env(unittest.TestCase):
	def test_mounts_file_disabled(self):
		f = Filer('name', {'a': 1})

		pprint(f.spec)

		pprint(f.getVolumeMounts())

		self.assertEqual(
			f.getVolumeMounts(),
			[{'mountPath': '/aws', 'name': 's3-conf', 'readOnly': True}],
		)
		self.assertEqual(
			f.getVolumes(),
			[
				{
					'name': 's3-conf',
					'secret': {
						'secretName': 'aws-secret',
						'items': [
							{'key': 'credentials', 'path': 'credentials'},
							{'key': 'config', 'path': 'config'},
						],
						'optional': True,
					},
				}
			],
		)

	def test_image_pull_policy(self):
		f = Filer('name', {'a': 1})
		self.assertEqual(f.getImagePullPolicy(), 'IfNotPresent')

		f = Filer('name', {'a': 1}, pullPolicyAlways=True)
		self.assertEqual(f.getImagePullPolicy(), 'Always')


if __name__ == '__main__':
	# import sys;sys.argv = ['', 'Test.testName']
	unittest.main()
