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
from StringIO import StringIO
import argparse


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
    """
    Transforms a function so that its execution is recorded by
    Sumatra, e.g

    >>> from smtdecorator import SMTDecorator

    >>> @SMTdecorator
    ... def myfunc(arg1=1, arg2=2):
    ...     return arg1 + arg2

    >>> print myfunc(arg1=3, tag=['test'], reason='testing')
    8

    You can also use the above script at the command line with

    $ python script.py --tag=test --reason='testing command line args'
    \ --tag=commandline --arg1=4

    The functions keyword arguments can be overridden using command
    line arguments.
    
    """

    def __init__(self, function):
        self.function = function

    def __call__(self, tag=[], reason='', *args, **kwargs):

        parameters, tag, reason = self.parseargs(kwargs, list(tag), reason)

        project = load_project()
        record = project.new_record(parameters=SimpleParameterSet(parameters),
                                    main_file=self.function.func_globals['__file__'],
                                    reason=reason)

        record.datastore.root = os.path.join(record.datastore.root, record.label)

        for t in tag:
            record.tags.add(t)

        record.start_time = time.time()
        with Redirect() as out:
            returnvalue = self.function(datadir=record.datastore.root, *args, **record.parameters.as_dict())

        record.duration = time.time() - record.start_time
        record.stdout_stderr = out.getvalue()
        record.output_data = record.datastore.find_new_data(record.timestamp)

        with SMTLock(project):
            project.add_record(record)
            project.save()

        return returnvalue

    def parseargs(self, func_kwargs, tag, reason):
        class Bare:
            pass
        ext_kwargs = Bare()
        parser = argparse.ArgumentParser(description="SMT arguments")

        for k, v in func_kwargs.iteritems():
            parser.add_argument('--' + k, default=v, type=type(v), dest=k)
                                          
        parser.add_argument('--tag', action='append', default=tag, dest='tag')
        parser.add_argument('--reason', default=reason, dest='reason')
        parser.parse_args(namespace=ext_kwargs)

        tag = ext_kwargs.tag
        reason = ext_kwargs.reason

        for k, v in func_kwargs.iteritems():
            func_kwargs[k] = getattr(ext_kwargs, k)
        
        return func_kwargs, tag, reason
            
            
