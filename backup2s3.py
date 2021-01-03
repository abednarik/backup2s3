#!/usr/bin/env python3

import argparse
from datetime import datetime
import logging
import os
import time
import configparser
import traceback
import subprocess
from shutil import which
import boto3
from botocore.exceptions import ClientError
import smtplib

logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    filename='/var/log/backup2s3.log',
                    filemode='w')
logging.getLogger("botocore").propagate = False
LOGGER = logging.getLogger(__name__)

# Exit status
NO_CONFIG_FILE=10
CONFIG_OPTION_MISSING=11
LOCAL_DIR_ERROR=12
TAR_FILE_ERROR=13
BINARY_MISSING=14
S3_UPLOAD_FAILED=15
S3_LIST_FAILED=16
S3_POLICY=17
SMTP_ERROR=18

# Constants
TAR_CMD = 'tar'
EXTENSION = '.tar.gz'

class Backup2S3:

    config_file = ''
    local_path = ''
    bucket = ''
    retention = 0
    log_file = ''
    email = ''

    def __init__(self, config_file=config_file):
        self._load_config(config_file)

    def _load_config(self, config_file):
        """ Load configuration options"""

        config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            LOGGER.error("Configuration file {} not found.".format(config_file))
            exit(NO_CONFIG_FILE)
        config.read(config_file)
        try: 
            self.local_path = config['backup2s3']['local_path']
            self.bucket = config['backup2s3']['bucket']
            self.retention = config['backup2s3']['retention']
            self.email = config['backup2s3']['email']
        except KeyError as e:
            LOGGER.error("{} option missing in configuration file. Please see configuration example.".format(e))
            exit(CONFIG_OPTION_MISSING)        

    def _file_format(self, local_path):
        """Set file name based on path and current date"""

        now = datetime.now()
        date_string = now.strftime("%Y%m%d%H%M%S")
        file_name = "{}_{}{}".format(os.path.basename(local_path), date_string, EXTENSION)
        return file_name


    def _tmp_path(self, file_name):
        """Simple helper function to set a tmp path to store a file locally"""

        tmp_dir = '/tmp/'
        return tmp_dir + file_name


    def _check_cmd(self, cmd):
        if not which(cmd):
            LOGGER.error("Binary {} not found in PATH".format(TAR_CMD))
            exit(BINARY_MISSING)
        return True


    def create_file(self, local_file_path):
        """Create local archive"""

        self._check_cmd(TAR_CMD)
        try:
            cmd = [TAR_CMD, 'czf', local_file_path, "-P", self.local_path]
            subprocess.check_output(cmd).decode("utf-8").strip() 
        except Exception as e: 
            msg = "Error while creating tar file {}".format(e)      
            self.send_notification(msg, TAR_FILE_ERROR)
    
        LOGGER.info("Local Archive created succesfully in {}".format(local_file_path))

        return True


    def upload_file(self, local_file_path, file_name):
        """Upload a file to an S3 bucket"""

        # Upload the file
        s3_client = boto3.client('s3')
        try:
            response = s3_client.upload_file(local_file_path, self.bucket, file_name)
        except ClientError as e:
            msg = "Error while uploading file to S3 bucket {}".format(e)      
            self.send_notification(msg, S3_UPLOAD_FAILED)

        LOGGER.info("File {} succesfully upload to S3 bucket {}".format(file_name, self.bucket))
        return True


    def cleanup_old_file(self):
        """Set a policy in bucket to remove old objects"""

        session = boto3.Session()
        s3 = session.resource('s3')
        bucket_lifecycle_configuration = s3.BucketLifecycleConfiguration(self.bucket)
        try:
            bucket_lifecycle_configuration.put(
                LifecycleConfiguration={
                    'Rules': [
                        {
                            'Expiration': {
                                'Days': 7
                            },
                            'ID': 'life cycle config for bucket objects',
                            'Filter': {
                                'Prefix': '/',
                            },
                            'Status': 'Enabled',
                            'NoncurrentVersionExpiration': {
                                'NoncurrentDays': 7
                            },
                            'AbortIncompleteMultipartUpload': {
                                'DaysAfterInitiation': 7
                            }
                        },
                    ]
                }
            )
        except ClientError as e:
            msg = "Unable to apply bucket policy {}".format(e)      
            self.send_notification(msg, S3_POLICY)

        LOGGER.info("Retention policy applied succesfully to S3 bucket {}".format(self.bucket))

        return True


    def send_notification(self, msg, exit_status=0):
        """Send email notification once process complete"""

        sender = 'backuop2s3'
        receivers = [self.email]

        message = """From: From backup2s3
        To: To {}
        Subject: Backup2S3 Report

        {}
        """.format(self.email, msg)

        try:
            smtpObj = smtplib.SMTP('localhost')
            smtpObj.sendmail(sender, receivers, message)         
            LOGGER.info("backup2s3 report email sent")
        except (smtplib.SMTPException, ConnectionRefusedError) as e:
            LOGGER.error("Failed to send email {}".format(e))
            exit(SMTP_ERROR)
        
        if exit_status != 0:
            LOGGER.error("{}".format(msg))
            exit(exit_status)
        
        return True

    def start(self):
        if not os.path.exists(self.local_path):
            LOGGER.error("Local directory {} not found.".format(self.local_path))
            exit(LOCAL_DIR_ERROR)            

        file_name = self._file_format(self.local_path)
        local_file_path = self._tmp_path(file_name)

        self.create_file(local_file_path)
        if self.upload_file(local_file_path, file_name):
            os.remove(local_file_path)
        self.cleanup_old_file()

        self.send_notification(msg="Backup completed succesfully")

        return True


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Backup a local directory to an existing S3 bucket"
    )

    parser.add_argument(
        "-c",
        "--config",
        required=True,
        dest="config_file",
        help="Path to configuration file.",
    )

    args = parser.parse_args()

    Backup2S3(config_file=args.config_file).start()

    exit(0)