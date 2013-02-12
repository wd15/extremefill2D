"""
Script to test setting up batch simaulations with Sumatra.

To set up environment.

    $ smt init smt_repository
    $ smt configure --executable=python --main=script.py
    $ smt configure --addlabel=parameters
    $ smt configure -g uuid

View data on laptop

    $ ssh concorde
    $ smtweb --allips --no-browser

On laptop use http://129.6.153.60:8000
"""

import time
import shutil
from subprocess import Popen, PIPE, call
import tempfile
import os

from sumatra.projects import load_project
from sumatra.parameters import build_parameters

def popen(cmd):
    return Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

def get_virtualenv():
    return os.path.split(os.environ.get('VIRTUAL_ENV'))[1]


class TempFile(object):
    def __init__(self, lines=[], suffix='', dir=None):
        (f, self.name) = tempfile.mkstemp(suffix=suffix, dir=dir)
        ff = os.fdopen(f, 'w')
        ff.writelines(lines)
        ff.close()

    def __del__(self):
        os.remove(self.name)


class Launcher(object):
    def __init__(self, cmd, datapath='.'):
        self.process = popen(cmd)
    
    @property
    def finished(self):
        return not (self.process.poll() is None)

    @property
    def output(self):
        return self.process.stdout.read() + self.process.stderr.read()


class QsubLauncher(object):
    def __init__(self, cmd, datapath='.'):
        self.qsubfile = TempFile(['#!/bin/bash\n',
                                  '\n',
                                  'source ~/.bashrc\n',
                                  'workon {virtualenv}\n'.format(virtualenv=get_virtualenv()),
                                  ' '.join(cmd)], suffix='.qsub', dir='.')
        self.datapath = datapath
        (stdout, stderr) = popen(['qsub', '-cwd', '-o', self.datapath, '-e', self.datapath, self.qsubfile.name]).communicate()
        self.qsubID = stdout.split(' ')[2]

    @property
    def finished(self):
        stdout, stderr = popen(['qstat', '-j', self.qsubID]).communicate()
        lines = stderr.splitlines()
        return len(lines) > 0 and "Following jobs do not exist" in lines[0]

    @property
    def output(self):
        stdout_stderr = ''
        for l in  ('o', 'e'):
            filename = self.qsubfile.name + '.' + l + self.qsubID
            filepath = os.path.join(self.datapath, filename)
            if os.path.exists(filepath):
                f = open(os.path.join(self.datapath, filename), 'r')
                stdout_stderr += f.read()
            else:
                stdout_stderr += "%s does not exist\n" % filepath
        return stdout_stderr


class Simulation(object):
    def __init__(self, record, parameters, tags):
        self.record = record
        self.record.parameters.update({"sumatra_label": self.record.label})
        self.record.parameters.update(parameters)
        lines = ["%s = %s\n" % (k, repr(v)) for k, v in self.record.parameters.values.iteritems()]
        self.paramfile = TempFile(lines=lines, suffix='.param', dir='.')
        self.record.datastore.root = os.path.join(self.record.datastore.root, self.record.label)
        for tag in tags:
            self.record.tags.add(tag)

    def launch(self):
        cmd = ['python', self.record.main_file, self.paramfile.name] 
        self.record.start_time = time.time()
        self.launcher = QsubLauncher(cmd, self.record.datastore.root)

    @property
    def finished(self):
        if not hasattr(self, '_finished'):
            self._finished = False
        if not self._finished:
            self._finished = self.launcher.finished
            if self._finished:
                self.record.duration = time.time() - self.record.start_time    
                self.record.output_data = self.record.datastore.find_new_data(self.record.timestamp)
                self.record.stdout_stderr = self.launcher.output

        return self._finished


class BatchSimulation(object):
    def __init__(self, script_file, parameter_file, poll_time=20.):
        self.script_file = script_file
        self.parameter_file = parameter_file
        self.poll_time = poll_time
        self.project = load_project()
        self.simulations = []

    def addSimulation(self, parameters={}, reason='', tags=()):
        record = self.project.new_record(parameters=build_parameters(self.parameter_file),
                                    main_file=os.path.join(os.path.split(__file__)[0], self.script_file),
                                    reason=reason)
        self.simulations += [Simulation(record, parameters, tags)]
        
    def run(self):
        for simulation in self.simulations:
            simulation.launch()

        while not np.all([s.finished for s in self.simulations]):
            time.sleep(self.poll_time)

        for simulation in self.simulations:
            self.project.add_record(simulation.record)

        self.project.save()


if __name__ == '__main__':
    import numpy as np

    batchSimulation = BatchSimulation('script.py', 'default.param', poll_time=2)
    for CFL in np.linspace(0.01, 0.1, 1):
        batchSimulation.addSimulation(reason="Testing QsubLaunch",
                                      tags=('CFL', 'test'),
                                      parameters={'CFL' : CFL, 'steps' : 1})

    batchSimulation.run()
