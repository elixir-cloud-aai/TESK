import logging
import os

from kubernetes import client
from kubernetes.client.exceptions import ApiException

from tesk.services.exceptions import ServiceStatusCodes
from tesk.services.utils import pprint


class PVC:
	def __init__(self, name='task-pvc', size_gb=1, namespace='default'):
		self.name = name
		self.spec = {
			'apiVersion': 'v1',
			'kind': 'PersistentVolumeClaim',
			'metadata': {'name': name},
			'spec': {
				'accessModes': ['ReadWriteOnce'],
				'resources': {'requests': {'storage': f'{str(size_gb)}Gi'}},
			},
		}

		self.subpath_idx = 0
		self.namespace = namespace
		self.cv1 = client.CoreV1Api()

		# The environment variable 'TESK_API_TASKMASTER_ENVIRONMENT_STORAGE_CLASS_NAME'
		# can be set to the preferred, non-default, user-defined storageClass
		if os.environ.get('STORAGE_CLASS_NAME') is not None:
			self.spec['spec'].update(
				{'storageClassName': os.environ.get('STORAGE_CLASS_NAME')}
			)

	def set_volume_mounts(self, mounts):
		self.volume_mounts = mounts

	def get_subpath(self):
		subpath = f'dir{str(self.subpath_idx)}'
		self.subpath_idx += 1
		return subpath

	def create(self):
		logging.debug('Creating PVC...')
		logging.debug(pprint(self.spec))
		try:
			return self.cv1.create_namespaced_persistent_volume_claim(
				self.namespace, self.spec
			)
		except ApiException as ex:
			if ex.status == ServiceStatusCodes.CONFLICT:
				logging.debug(f'Reading existing PVC: {self.name}')
				return self.cv1.read_namespaced_persistent_volume_claim(
					self.name, self.namespace
				)
			else:
				logging.debug(ex.body)
				raise ApiException(ex.status, ex.reason) from None

	def delete(self):
		cv1 = client.CoreV1Api()
		cv1.delete_namespaced_persistent_volume_claim(
			self.name, self.namespace, body=client.V1DeleteOptions()
		)
