
"""
Script to test setting up batch simaulations with Sumatra.

To set up environment.

    $ smt init smt_repository
    $ smt configure --executable=python --main=script.py
    $ smt configure --addlabel=parameters
    $ smt configure -g uuid
    $ smt configure -c store-diff

View data on laptop

    $ ssh concorde
    $ smtweb --allips --no-browser

On laptop use http://129.6.153.60:8000
"""


import time
import os
import sys


from sumatra.projects import load_project
from sumatra.parameters import SimpleParameterSet
from sumatra.projects import _get_project_file
import lockfile


class Writer(object):
    log = []
    def write(self, data):
        self.log.append(data)


def SMTSimulation(function, args=(), kwargs={}, tags=(), reason='', main_file=__file__):
    project = load_project()
    record = project.new_record(parameters=SimpleParameterSet(kwargs),
                                main_file=main_file,
                                reason=reason)

    record.datastore.root = os.path.join(record.datastore.root, record.label)
    record.parameters.update({'datadir': record.datastore.root})

    for tag in tags:
        record.tags.add(tag)

    record.start_time = time.time()

    ## http://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python
    ## see the last post in this thread
    logger = Writer()
    stdout_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = logger, logger

    function(*args, **record.parameters.as_dict())

    sys.stdout, sys.stderr = stdout_stderr
    record.stdout_stderr = logger.log
    print logger.log
    record.duration = time.time() - record.start_time
    record.output_data = record.datastore.find_new_data(record.timestamp)

    lock = lockfile.FileLock(os.path.split(_get_project_file(project.path))[0])
    lock.acquire()
    project.add_record(record)
    project.save()
    lock.release()

