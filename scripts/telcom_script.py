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
from extremefill2D.tools import build_mesh, print_data
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

## timestep and sweep
redo_timestep = False
elapsedTime = 0.0
step = 0
extensionGlobalValue = max(variables.extension.globalValue)

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

    equations.advection.solve(dt=variables.dt)

    residuals = [equations.sweep(variables.dt) for _ in range(params.sweeps)]
        
    extensionGlobalValue = variables.extend()
    
    if float(variables.dt) > (params.CFL * mesh.nominal_dx / extensionGlobalValue * 1.1):
        variables.retreat_step()
        redo_timestep = True
    else:
        elapsedTime += float(variables.dt)
        step += 1
        redo_timestep = False

    print_data(step, elapsedTime, variables.dt, redo_timestep, residuals)
    

if not hasattr(params, 'sumatra_label'):
    sumatra_label = '.'
else:
    sumatra_label = params.sumatra_label

finaldir = os.path.join('Data', sumatra_label)

shutil.move(variables.dataFile, finaldir)


    
