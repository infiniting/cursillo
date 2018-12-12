FROM nfqsolutions/python3-prod

WORKDIR /code

RUN pip install paramiko watchdog \
    && mkdir /code/logs /code/pem /code/input /code/backup

ENV NFQ_HOME=/code
ENV PEM_NAME=xxx
ENV USER=xxx
ENV HOST=xx.xxx.x.xxx
ENV PORT=xxxx
ENV LOCAL_PATH=/code/input
ENV REMOTE_PATH=/xxxx/xxx/
ENV BACKUP_PATH=/code/backup
ENV HAS_BACKUP=True

ENV PATTERNS=CANARIAS

ENV NO_PATTERNS=NONE

COPY folder_watcher.py /code/

#CMD python folder_watcher.py $PEM_PATH $USER $HOST $PORT $INPUT_PATH $DESTINATION_PATH $BACKUP_PATH $HAS_BACKUP CANARIAS NONE
CMD python folder_watcher.py
