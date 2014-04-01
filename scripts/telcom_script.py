#!/usr/bin/env python
"""
Usage: script.py [<jsonfile>]

"""

__docformat__ = 'restructuredtext'

import os
import tempfile
import shutil
from collections import namedtuple
import json


import tables
from docopt import docopt
import fipy as fp

from extremefill2D.tools import build_mesh, write_data
from extremefill2D.variables import Variables
from extremefill2D.equations import Equations


## read parameters
arguments = docopt(__doc__, version='Run script.py')
jsonfile = arguments['<jsonfile>']
if not jsonfile:
    jsonfile = 'telcom_script_test.json'
with open(jsonfile, 'rb') as ff:
    params_dict = json.load(ff)
params = namedtuple('ParamClass', params_dict.keys())(*params_dict.values())

## create mesh
mesh = build_mesh(params)

## create variables
variables = Variables(params, mesh)

## create equations
equations = Equations(params, variables)

## other stuff
extensionGlobalValue = max(variables.extension.globalValue)
redo_timestep = False

vars_ = [variables.potential, variables.cupric, variables.suppressor, variables.theta]
eqs =  [equations.potential, equations.cupric, equations.suppressor, equations.theta]
solvers = [fp.LinearPCGSolver(tolerance=params.solver_tol)] * 4
dts = [None, None, None, 1.]
zipped = zip(vars_, eqs, solvers, dts)

## create extra arguments for writing to the data file
writes = [params.write_potential, params.write_cupric, params.write_suppressor, params.write_theta]
names = ['potential', 'cupric', 'suppressor', 'theta']
data_args = dict((n, v) for w, n, v in zip(writes, names, vars_) if w)
dataFile = os.path.join(tempfile.gettempdir(), 'data.h5')

elapsedTime = 0.0
step = 0
while (step < params.totalSteps) and (elapsedTime < params.totalTime):

    variables.updateOld()
    
    if (dataFile is not None) and (step % params.data_frequency == 0) and (not redo_timestep):
        write_data(dataFile, elapsedTime, variables.distance, step,
                   extensionGlobalValue=extensionGlobalValue,
                   **data_args)
        if step > 0 and extensionGlobalValue < params.shutdown_deposition_rate:
            break
        
    if (step % int(params.levelset_update_ncell / params.CFL) == 0):
        if params.delete_islands:
            variables.distance.deleteIslands()
        variables.distance.calcDistanceFunction(order=1)

    variables.update_dt(params, mesh)

    import fipy.solvers.trilinos as trilinos
    equations.advection.solve(variables.distance, dt=variables.dt, solver=trilinos.LinearLUSolver())
    
    for sweep in range(params.sweeps):
        residuals = equations.sweep(variables.dt)
        print 'sweep: {0}, residuals: {1}'.format(sweep, residuals)

    # for sweep in range(params.sweeps):
    #     res = [eqn.sweep(v, dt=dt_ or variables.dt, solver=s) for v, eqn, s, dt_ in zipped]
    #     print 'sweep: {0}, res: {1}'.format(sweep, res)

    extensionGlobalValue = variables.extend()
    
    if float(variables.dt) > (params.CFL * mesh.nominal_dx / extensionGlobalValue * 1.1):
        print 'redo time step'
        print 'new dt',float(variables.dt)
        variables.retreat_step()
        redo_timestep = True
    else:
        elapsedTime += float(variables.dt)
        step += 1
        redo_timestep = False
    
    print 'dt',variables.dt
    print 'elapsed time',elapsedTime
    print 'step',step
    import datetime
    print 'time: ',datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print

if not hasattr(params, 'sumatra_label'):
    sumatra_label = '.'
else:
    sumatra_label = params.sumatra_label

finaldir = os.path.join('Data', sumatra_label)

shutil.move(dataFile, finaldir)


    
