
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

from sumatra.projects import load_project
from sumatra.parameters import SimpleParameterSet
import lockfile

def SMTSimulation(function, args=(), kwargs={}, tags=(), reason='', main_file=__file__):
    project = load_project()
    record = project.new_record(parameters=SimpleParameterSet(kwargs),
                                main_file=main_file,
                                reason=reason)

##    record.parameters.update(kwargs)

    record.datastore.root = os.path.join(record.datastore.root, record.label)
    datafile = os.path.join(record.datastore.root, 'data.h5')
    record.parameters.update({'dataFile': datafile})

    for tag in tags:
        record.tags.add(tag)

    record.start_time = time.time()
    function(*args, **record.parameters.as_dict())
    record.duration = time.time() - record.start_time
    record.output_data = record.datastore.find_new_data(record.timestamp)
    ##record.stdout_stderr = process.stdout.read() + process.stderr.read()

    lock = lockfile.FileLock('/users/wd15/tmp/smt')
    lock.acquire()
    project.add_record(record)
    project.save()
    lock.release()

