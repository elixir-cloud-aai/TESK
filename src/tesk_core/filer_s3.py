import sys
import os
import logging
import re
import botocore
import boto3
from tesk_core.transput import Transput, Type

class S3Transput(Transput):
    def __init__(self, path, url, ftype):
        Transput.__init__(self, path, url, ftype)
        self.bucket, self.file_path = self.get_bucket_name_and_file_path()
        self.bucket_obj = None

    def __enter__(self):
        client = boto3.resource('s3', endpoint_url=self.extract_endpoint())
        if self.check_if_bucket_exists(client):
            sys.exit(1)
        self.bucket_obj = client.Bucket(self.bucket)
        return self

    def extract_endpoint(self):
        return boto3.client('s3').meta.endpoint_url

    def check_if_bucket_exists(self, client):
        try:
            client.meta.client.head_bucket(Bucket=self.bucket)
        except botocore.exceptions.ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            logging.error('Got status code: %s', e.response['Error']['Code'])
            if e.response['Error']['Code'] == "404":
                logging.error("Failed to fetch Bucket, reason: %s", e.response['Error']['Message'])
            return 1
        return 0

    def get_bucket_name_and_file_path(self):
        """
        if the S3 url is similar to s3://idr-bucket-1/README.txt format
        """
        if self.url.startswith("s3"):
            self.url_path = re.sub(r's3:\/', "", self.url)

        """
        If the s3 url are of following formats
        1. File type = FILE
            * http://mybucket.s3.amazonaws.com/file.txt
            * http://mybucket.s3-aws-region.amazonaws.com/file.txt
            * http://s3.amazonaws.com/mybucket/file.txt
            * http://s3-aws-region.amazonaws.com/mybucket/file.txt
            * s3://mybucket/file.txt

            return values will be
            bucket name = mybucket , file path = file.txt

        2. File type = DIRECTORY
            * http://mybucket.s3.amazonaws.com/dir1/dir2/
            * http://mybucket.s3-aws-region.amazonaws.com/dir1/dir2/
            * http://s3.amazonaws.com/mybucket/dir1/dir2/
            * http://s3-aws-region.amazonaws.com/mybucket/dir1/dir2/
            * s3://mybucket/dir1/dir2/

            return values will be
            bucket name = mybucket , file path = dir1/dir2/
        """

        match = re.search('^([^.]+).s3', self.netloc)
        if match:
            bucket = match.group(1)
        else:
            bucket = self.url_path.split("/")[1]
        file_path = re.sub(r'^\/' + bucket + '\/', "", self.url_path).lstrip("/")
        return bucket, file_path

    def download_file(self):
        logging.debug('Downloading s3 object: "%s" Target: %s', self.bucket + "/" + self.file_path, self.path)
        basedir = os.path.dirname(self.path)
        os.makedirs(basedir, exist_ok=True)
        return self.get_s3_file(self.path, self.file_path)

    def upload_file(self):
        logging.debug('Uploading s3 object: "%s" Target: %s', self.path,  self.bucket + "/" + self.file_path)
        try:
            self.bucket_obj.upload_file(Filename=self.path, Key=self.file_path)
        except (botocore.exceptions.ClientError,  OSError) as err:
            logging.error("File upload failed for '%s'", self.bucket + "/" + self.file_path)
            logging.error(err)
            return 1
        return 0

    def upload_dir(self):
        logging.debug('Uploading s3 object: "%s" Target: %s', self.path, self.bucket + "/" + self.file_path)
        try:
            for item in os.listdir(self.path):
                path = os.path.join(self.path,item)
                if os.path.isdir(path):
                    file_type = Type.Directory
                elif os.path.isfile(path):
                    file_type = Type.File
                else:
                    # An exception is raised, if the object type is neither file or directory
                    logging.error("Object is neither file or directory : '%s' ",path)
                    raise IOError
                file_path = os.path.join(self.url, item)
                with S3Transput(path, file_path, file_type) as transfer:
                    if transfer.upload():
                        return 1
        except OSError as err:
            logging.error("File upload failed for '%s'", self.bucket + "/" + self.file_path)
            logging.error(err)
            return 1
        return 0

    def download_dir(self):
        logging.debug('Downloading s3 object: "%s" Target: %s', self.bucket + "/" + self.file_path, self.path)
        client = boto3.client('s3', endpoint_url=self.extract_endpoint())
        if not self.file_path.endswith('/'):
            self.file_path += '/'
        objects = client.list_objects_v2(Bucket=self.bucket, Prefix=self.file_path)

        # If the file path does not exists in s3 bucket, 'Contents' key will not be present in objects
        if "Contents" not in objects:
            logging.error('Got status code: %s', 404)
            logging.error("Invalid file path!.")
            return 1

        # Looping through the list of objects and downloading them
        for obj in objects["Contents"]:
            file_name = os.path.basename(obj["Key"])
            dir_name = os.path.dirname(obj["Key"])
            path_to_create = re.sub(r'^' + self.file_path.strip('/').replace('/', '\/') + '', "", dir_name).strip('/')
            path_to_create = os.path.join(self.path, path_to_create)
            os.makedirs(path_to_create, exist_ok=True)
            if self.get_s3_file(os.path.join(path_to_create, file_name), obj["Key"]):
                return 1
        return 0

    def get_s3_file(self, file_name, key):
        try:
            self.bucket_obj.download_file(Filename=file_name, Key=key)
        except botocore.exceptions.ClientError as err:
            logging.error('Got status code: %s', err.response['Error']['Code'])
            logging.error(err.response['Error']['Message'])
            return 1
        return 0
    