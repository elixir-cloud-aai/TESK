import logging
import time
from kubernetes import client, config


class Job:
    def __init__(self, body, name='task-job', namespace='default'):
        self.name = name
        self.namespace = namespace
        self.status = 'Initialized'
        self.bv1 = client.BatchV1Api()
        self.body = body
        self.body['metadata']['name'] = self.name

    def run_to_completion(self, poll_interval, check_cancelled):
        logging.debug(self.body)
        self.bv1.create_namespaced_job(self.namespace, self.body)
        status = self.get_status()
        while status == 'Running':
            if check_cancelled():
                self.delete()
                return 'Cancelled'

            time.sleep(poll_interval)

            status = self.get_status()

        return status

    def get_status(self):
        job = self.bv1.read_namespaced_job(self.name, self.namespace)
        try:
            if job.status.conditions[0].type == 'Complete' and job.status.conditions[0].status:
                self.status = 'Complete'
            elif job.status.conditions[0].type == 'Failed' and job.status.conditions[0].status:
                self.status = 'Failed'
            else:
                self.status = 'Error'
        except TypeError:  # The condition is not initialized, so it is not complete yet, wait for it
            self.status = 'Running'

        return self.status

    def delete(self):
        self.bv1.delete_namespaced_job(
            self.name, self.namespace, client.V1DeleteOptions())
