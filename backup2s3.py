#!/usr/bin/env python3

import argparse
from datetime import datetime
import logging
import os
import time
import configparser
import traceback
import subprocess
from datetime import datetime


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)

# EXit status
NO_CONFIG_FILE=10
CONFIG_OPTION_MISSING=11
LOCAL_DIR_ERROR=12
TAR_FILE_ERROR=13


class Backup2S3:

    config_file = ''
    local_path = ''
    remote_path = ''
    retention = ''
    log_file = ''


    def __init__(self, config_file=config_file):
        self._load_config(config_file)

    def _load_config(self, config_file):
        config = configparser.ConfigParser()
        if not os.path.exists(config_file):
            LOGGER.error("Configuration file {} not found.".format(config_file))
            exit(NO_CONFIG_FILE)
        config.read(config_file)
        try: 
            self.local_path = config['backup2s3']['local_path']
            self.remote_path = config['backup2s3']['remote_path']
            self.retention = config['backup2s3']['retention']
            self.log_file = config['backup2s3']['log_file']
        except KeyError as e:
            LOGGER.error("{} option missing in configuration file. Please see configuration example.".format(e))
            exit(CONFIG_OPTION_MISSING)        


    def _file_format(self, local_path):
        extension = '.tar.gz'

        now = datetime.now()
        date_string = now.strftime("%Y%m%d%H%M%S")
        file_name = "{}_{}{}".format(os.path.basename(local_path), date_string, extension)

        return file_name


    def _tmp_path(self, file_name):
        tmp_dir = '/tmp/'
        
        return tmp_dir + file_name


    def upload_file(self, local_file_path):
        pass

    def cleanup_old_file():
        pass

    def sent_notification():
        pass

    
    def start(self):
        if not os.path.exists(self.local_path):
            LOGGER.error("Local directory {} not found.".format(self.local_path))
            exit(LOCAL_DIR_ERROR)            

        file_name = self._file_format(self.local_path)
        local_file_path = self._tmp_path(file_name)

        try:
            cmd = ['tar', 'czf', local_file_path, "-P", self.local_path]
            subprocess.check_output(cmd).decode("utf-8").strip() 
        except Exception as e:       
            LOGGER.error("Error while creating tar file {}".format(e))
            exit(TAR_FILE_ERROR)




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

    Backup2S3(dryrun=args.dryrun,config_file=args.config_file).start()

    exit(0)