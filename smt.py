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
    def __init__(self, record, parameter_changeset):
        self.record = record
        self.record.parameters.update({"sumatra_label": self.record.label})
        self.record.parameters.update(parameter_changeset)
        lines = ["%s = %s\n" % (k, repr(v)) for k, v in self.record.parameters.values.iteritems()]
        self.paramfile = TempFile(lines=lines, suffix='.param')
        self.record.datastore.root = os.path.join(self.record.datastore.root, self.record.label)
    # @property
    # def paramlines(self):
    #     _lines = []
    #     for k, v in self.record.parameters.values.iteritems():
    #         s = "%s = %s\n"
    #         _lines += [s % (k, repr(v))]

    #     return _line

    def launch(self):
        cmd = ['python', self.record.main_file, self.paramfile.name] 
        self.record.start_time = time.time()
        self.process = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        ##print self.process.stdout.read()
        ##print self.process.stderr.read()

    @property
    def finished(self):
        if not hasattr(self, '_finished'):
            self._finished = False
        if not self._finished:
            self._finished = bool(self.process.poll())
            if self._finished:
                self.record.duration = time.time() - self.record.start_time    
                self.record.output_data = self.record.datastore.find_new_data(self.record.timestamp)

        return self._finished


class BatchSimulation(object):
    def __init__(self, script_file, parameter_file, reason='', parameter_changesets=({},), poll_time=20):
        simulations = []
        project = load_project()

        for parameter_changeset in parameter_changesets:
            record = project.new_record(parameters=build_parameters(parameter_file),
                                        main_file=os.path.join(os.path.split(__file__)[0], script_file),
                                        reason=reason)
            simulation = Simulation(record, parameter_changeset)
            simulation.launch()
            simulations += [simulation]

        while not np.all([s.finished for s in simulations]):
            time.sleep(poll_time)

        for simulation in simulations:
            project.add_record(simulation.record)

        project.save()


if __name__ == '__main__':
    import numpy as np
    CFLs = ()
    for CFL in np.linspace(0.01, 0.01, 1):
        CFLs += ({'CFL' : CFL, 'steps' : 1},)
        
    BatchSimulation('script.py', 'default.param', 'testing BatchSimulation again', CFLs, poll_time=2)
