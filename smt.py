
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
from contextlib import contextmanager
from StringIO import StringIO


from sumatra.projects import load_project
from sumatra.parameters import SimpleParameterSet
from sumatra.projects import _get_project_file
import lockfile


class SMTLock:
    def __init__(self, project):
        self.lock = lockfile.FileLock(os.path.split(_get_project_file(project.path))[0])

    def __enter__(self):
        self.lock.acquire()

    def __exit__(self, type, value, tb):
        self.lock.release()


class Redirect:
    def __enter__(self):
        self.tmp_stdout = sys.stdout
        sys.stdout = StringIO()
        return sys.stdout
    
    def __exit__(self, type, value, tb):
        sys.stdout = self.tmp_stdout

        
class SMTSimulation(object):
    def __init__(self, function, args=(), kwargs={}, tags=(), reason='', main_file=__file__):
        project = load_project()
        record = project.new_record(parameters=SimpleParameterSet(kwargs),
                                    main_file=main_file,
                                    reason=reason)

        record.datastore.root = os.path.join(record.datastore.root, record.label)
        record.parameters.update({'datadir': record.datastore.root})

        for tag in tags:
            record.tags.add(tag)

        self.record = record
        self.project = project
        self.function = function
        self.args = args
        
    def launch(self):
        record = self.record
        record.start_time = time.time()

        with Redirect() as out:
            self.function(*self.args, **record.parameters.as_dict())

        print out.getvalue()
        record.stdout_stderr = out.getvalue()
        record.duration = time.time() - record.start_time

        record.output_data = record.datastore.find_new_data(record.timestamp)

        with SMTLock(self.project):
            self.project.add_record(record)
            self.project.save()
