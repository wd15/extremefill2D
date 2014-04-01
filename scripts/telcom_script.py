#!/usr/bin/env python
"""
Usage: script.py [<jsonfile>]

"""

__docformat__ = 'restructuredtext'

import os
import shutil
from collections import namedtuple
import json


import tables
from docopt import docopt
from extremefill2D.tools import build_mesh
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

## timestep and sweep
redo_timestep = False
elapsedTime = 0.0
step = 0

while (step < params.totalSteps) and (elapsedTime < params.totalTime):

    variables.updateOld()
    
    if (step % params.data_frequency == 0) and (not redo_timestep):
        variables.write_data(elapsedTime, step)
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

    extensionGlobalValue = variables.extend()
    
    if float(variables.dt) > (params.CFL * mesh.nominal_dx / extensionGlobalValue * 1.1):
        print 'redo time step'
        variables.retreat_step()
        print 'new dt',float(variables.dt)
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

shutil.move(variables.dataFile, finaldir)


    
