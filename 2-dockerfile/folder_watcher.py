#!/usr/bin/python
#
# Para adeslas-canarias:
#  To launch the process:[python][python script name][Pem path][user][host][port][folder input path]
#                        [folder output path where file is copy][Copy files with this pattern in name. Can be NONE]
#                        [Not copy files with this pattern in name. Can be NONE]
# Example: python folder_watcher.py C:/Users/nfqSolutions/Desktop/juan juan xx.xxx.x.xxx 2222 F:/Trabajo/mesana_pruebas/ /home/juan/ CANARIAS NONE
#
#
# Para corpbanca:
# python folder_watcher.py /nfqsolutions/automatization/corpbanca corpbanca xx.xxx.x.xxx /nfqsolutions/Innovar/sftp-homes/sftpuser/corpbanca/Corpbanca/inputs/diario/ /nfqsolutions/Innovar/sftp-homes/sftpuser/corpbanca/Corpbanca/inputs/diario/ NONE SENS,READY,COMPLEMENTARY,TOTAL,NEG,REPORT,REPORT.CSV,AGR
#

import os
import shutil
import sys
import logging
import threading
import time
import paramiko
import socket
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime


# Configuration for logger
NFQ_HOME = os.getenv('NFQ_HOME')
DATE_FORMAT = '%Y%m%d'
FILENAME = '{}/logs/folder_watcher_{}.log'.format(NFQ_HOME, datetime.now().strftime(DATE_FORMAT))
LEVEL = logging.INFO
formatter = logging.Formatter(fmt='%(asctime)15s - %(levelname)8s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
file = logging.FileHandler(filename=FILENAME)
file.setFormatter(formatter)

# Configure console handler
log_console = logging.StreamHandler()
log_console.setFormatter(formatter)

# Add console and file handlers to logger
logger = logging.getLogger()
logger.setLevel(LEVEL)
logger.addHandler(file)
logger.addHandler(log_console)

# Input parameter define
PEM_NAME = os.getenv('PEM_NAME')
USER = os.getenv('USER')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
LOCAL_PATH = os.getenv('LOCAL_PATH')
REMOTE_PATH = os.getenv('REMOTE_PATH')
BACKUP_PATH = os.getenv('BACKUP_PATH')
HAS_BACKUP = os.getenv('HAS_BACKUP')
PATTERNS = os.getenv('PATTERNS')
NO_PATTERNS = os.getenv('NO_PATTERNS')


class MyHandler(FileSystemEventHandler):

    def on_created(self, event):

        file_path = event.src_path
        logger.info('New file detected: {}'.format(file_path))
        threading.Thread(target=thread_launcher(file_path)).start()


def thread_launcher(file_path):
    try:
        file_name = os.path.basename(file_path)
        file_name_params = file_name.upper().split('_')

        is_not_same_size_bool = True
        while is_not_same_size_bool:
            before_size = int(os.stat(file_path).st_size)
            time.sleep(5)
            after_size = int(os.stat(file_path).st_size)
            if before_size == after_size:
                is_not_same_size_bool = False

        # No copy files with this parameters in name
        if PATTERNS != 'NONE':
            for pattern in PATTERNS.split(','):
                if pattern not in file_name:
                    logger.warning('NO copy files with pattern not similar to ({}): local={}'.format(pattern,
                                                                                                     file_path))
                    return

        if NO_PATTERNS != 'NONE':
            for no_pattern in NO_PATTERNS.split(','):
                if no_pattern in file_name_params:
                    logger.warning('NO copy files with pattern is similar to ({}): local={}'.format(no_pattern,
                                                                                                    file_path))
                    return

        # Copy file to remote path
        remote_path = os.path.join(REMOTE_PATH, file_name)

        logger.debug('Copy file: local={} --> remote={}'.format(file_path, remote_path))
        ssh_client = paramiko.client.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(HOST, port=PORT, username=USER, key_filename=os.path.join('/code/pem', PEM_NAME))
        for i in range(0, 10):
            ftp_client = ssh_client.open_sftp()
            try:
                logger.debug('Intent {}'.format(i))
                ftp_client.get_channel().settimeout(60.0)
                ftp_client.put(file_path, remote_path)
                ftp_client.close()
                break
            except socket.timeout:
                ftp_client.close()
                logger.debug('SSH channel timeout exceeded of {}'.format(60.0))

        logger.info('Copied file: local={} --> remote={} is OK'.format(file_path, remote_path))

        # Move local file to backup docker
        if HAS_BACKUP == 'True':
            try:
                # Backup path
                backup_path = os.path.join(BACKUP_PATH, file_name)
                logger.debug('Move file: local={} --> backup={} is OK'.format(file_path, backup_path))
                # Move file
                shutil.move(file_path, backup_path)
                logger.info('Moved file: local={} --> backup={} is OK'.format(file_path, backup_path))
            except Exception as e1:
                e1_type, e1_value, e1_traceback = sys.exc_info()
                logger.error('Error moving file {} of local to backup --> Line: {} Type: {} Error: {}'.format(
                    file_path, e1_traceback.tb_lineno, e1_type.__name__, e1))
    except Exception as e2:
        e2_type, e2_value, e2_traceback = sys.exc_info()
        logger.error('Error coping file {} of local --> Line: {} Type: {} Error: {}'.format(file_path,
                                                                                            e2_traceback.tb_lineno,
                                                                                            e2_type.__name__, e2))


if __name__ == "__main__":
    # Check local path
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=LOCAL_PATH, recursive=False)
    observer.start()

    try:
        logger.info('STARTED folder watcher python daemon')
        print('STARTED folder watcher python daemon')

        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt as interruption:
                logger.info('STOPPED folder watcher python daemon')
                print('\nSTOPPED folder watcher python daemon')
                sys.exit()

    except Exception as e0:
        e0_type, e0_value, e0_traceback = sys.exc_info()
        logger.error('Error in checking files --> Line: {} Type: {} Error: {}'.format(e0_traceback.tb_lineno,
                                                                                      e0_type.__name__, e0))
        observer.stop()
    observer.join()
