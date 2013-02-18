
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
        self.target = StringIO()
        sys.stdout = self.target
        return self.target
    
    def __exit__(self, type, value, tb):
        sys.stdout = self.tmp_stdout
        print self.target.getvalue()

        
class SMTDecorator(object):
    def __init__(self, function):
        self.function = function
                
    def __call__(self, tags=(), reason='', *args, **kwargs):
        project = load_project()
        record = project.new_record(parameters=SimpleParameterSet(kwargs),
                                    main_file=self.function.func_globals['__file__'],
                                    reason=reason)

        record.datastore.root = os.path.join(record.datastore.root, record.label)
        for tag in tags:
            record.tags.add(tag)

        record.start_time = time.time()

        with Redirect() as out:
            returnvalue = self.function(datadir=record.datastoreroot, *args, **record.parameters.as_dict())

        record.duration = time.time() - record.start_time
        record.stdout_stderr = out.getvalue()
        record.output_data = record.datastore.find_new_data(record.timestamp)

        with SMTLock(project):
            project.add_record(record)
            project.save()

        return returnvalue


class SMTContextManager(object):
    def __init__(self, tags=(), reason=''):
        self.tags = tags
        self.reason = reason
        
    def __enter__(self):
        self.project = load_project()
        self.record = self.project.new_record(parameters=SimpleParameterSet({}),
                                              main_file=__file__,
                                              reason=self.reason)

        self.record.datastore.root = os.path.join(self.record.datastore.root, self.record.label)
        for tag in self.tags:
            self.record.tags.add(tag)

        self.record.start_time = time.time()
        
        self.redirect = Redirect()
        self.redirect.__enter__()
        
    def __exit__(self, type, value, tb):
        self.redirect.__exit__()
            
        self.record.duration = time.time() - self.record.start_time
        self.record.stdout_stderr = self.redirect.target.getvalue()
        self.record.output_data = self.record.datastore.find_new_data(self.record.timestamp)

        with SMTLock(self.project):
            self.project.add_record(self.record)
            self.project.save()

