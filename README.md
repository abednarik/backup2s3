# Backup to S3

Script to backup a local directory to an S3 bucket.

__DISCLAIMER__ This script was only tested in Ubuntu 18.04 with Python 3.6 and is not intended to be used in production.
Notifications emails are only sent to localhost.

## Requirements

* [Python](https://www.python.org/downloads/)
* [tar](https://www.gnu.org/software/tar/)

## Install

* Download backup2s3 script, save it in your PATH and give it execution permisssions. 

```shell
$ wget https://raw.githubusercontent.com/abednarik/backup2s3/master/backup2s3.py -O /usr/local/bin/backup2s3.py
$ chmod +x /usr/local/bin/backup2s3.py
```

* Install python modules with pip

```shell
$ pip3 install boto3
```

* Install AWS cli

```shell
sudo apt-get install -y awscli
```

* Configure AWS credentials 

```shell
$ aws configure 
AWS Access Key ID [None]: YOURKEYHERE
AWS Secret Access Key [None]: YOURSECRETKEYHERE
Default region name [None]: your-region
```

## Configuration

- Create a directory to store configurations files for this process. For example:

```shell
$ sudo mkdir /etc/backup2s3
```

- Create a configuration file with a descriptive name and place in the directory created above. For example `apache2.cfg`

```
[backup2s3]
local_path = /etc/apache2
bucket = abednarik-backups
retention = 7
email = abednarik
```

| Option        | Description                                        | 
| ------------- |:--------------------------------------------------:| 
| local_path    | path to directory to backup                        | 
| bucket        | S3 bucket to store backupss                        | 
| retention     | Numbers of days to keep backups                    |
| email         | Email address to send notifications after each run |


## Usage

Schedule a cron job to execute daily backups

#### Example

- Edit crontab using 

```shell
sudo crontab -e
```

- Add an entry for backup2s3 to run every day at midnight

```shell
0 0 * * *    /usr/local/bin/backup2s3.py  > /dev/null 2>&1
```


__NOTE__ Make user user running this cron job is able to wirte to __/var/log/backup2s3.log__


