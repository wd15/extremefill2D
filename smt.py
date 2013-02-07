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
from sumatra.projects import load_project
from sumatra.parameters import build_parameters
from subprocess import Popen, PIPE, call
import tempfile
import os


class TempFile(object):
    def __init__(self, lines=[], suffix=''):
        (f, self.name) = tempfile.mkstemp(suffix='.param')
        ff = os.fdopen(f, 'w')
        ff.writelines(lines)
        ff.close()

    def __del__(self):
        os.remove(self.name)


class Simulation(object):
    def __init__(self, record, parameters, tags):
        self.record = record
        self.record.parameters.update({"sumatra_label": self.record.label})
        self.record.parameters.update(parameters)
        lines = ["%s = %s\n" % (k, repr(v)) for k, v in self.record.parameters.values.iteritems()]
        self.paramfile = TempFile(lines=lines, suffix='.param')
        self.record.datastore.root = os.path.join(self.record.datastore.root, self.record.label)
        for tag in tags:
            self.record.tags.add(tag)

    def launch(self):
        cmd = ['python', self.record.main_file, self.paramfile.name] 
        self.record.start_time = time.time()
        self.process = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

    @property
    def finished(self):
        if not hasattr(self, '_finished'):
            self._finished = False
        if not self._finished:
            self._finished = not (self.process.poll() is None)
            if self._finished:
                self.record.duration = time.time() - self.record.start_time    
                self.record.output_data = self.record.datastore.find_new_data(self.record.timestamp)
                self.record.stdout_stderr = self.process.stdout.read() + self.process.stderr.read()

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
        for simulation in simulations:
            simulation.launch()

        while not np.all([s.finished for s in self.simulations]):
            time.sleep(self.poll_time)

        for simulation in self.simulations:
            self.project.add_record(simulation.record)

        self.project.save()


if __name__ == '__main__':
    import numpy as np

    batchSimulation = BatchSimulation('script.py', 'default.param', poll_time=2)
    for CFL in np.linspace(0.01, 0.1, 3):
        batchSimulation.addSimulation(reason="Testing the BatchSimulation script for tags",
                                      tags=('CFL', 'test'),
                                      parameters={'CFL' : CFL, 'steps' : 1})

    batchSimulation.run()
