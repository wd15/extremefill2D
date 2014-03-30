#!/usr/bin/env python
"""
Usage: script.py [<jsonfile>]

"""

__docformat__ = 'restructuredtext'

import tables

from docopt import docopt
from extremefill2D.tools import Parameters
import fipy as fp
from fipy import numerix
import numpy as np
import os
import tempfile
from extremefill2D.tools import write_data
from fipy.variables.surfactantVariable import _InterfaceSurfactantVariable
import shutil
from extremefill2D.tools import DistanceVariableNonUniform as DVNU
import fipy.solvers.trilinos as trilinos
from extremefill2D.tools import MeshBuilder

arguments = docopt(__doc__, version='Run script.py')
jsonfile = arguments['<jsonfile>']
if not jsonfile:
    
    jsonfile = 'telcom_script_test.json'
params = Parameters(jsonfile)

appliedPotential = params.appliedPotential
CFL = params.CFL
kPlus = params.kPlus
featureDepth = params.featureDepth
bulkSuppressor = params.bulkSuppressor

params.delta = 150e-6


dtMin = .5e-7
dt = 0.01
i1 = -40.
i0 = 40.
diffusionCupric = 2.65e-10
faradaysConstant = 9.6485e4
gasConstant = 8.314
temperature = 298.
alpha = 0.4
charge = 2
bulkCupric = 1000.
diffusionSuppressor = 9.2e-11
kappa = 15.26
omega = 7.1e-6
gamma = 2.5e-7
capacitance = 0.3
NxBase = 1000
solver_tol = 1e-10
elapsedTime = 0.
step = 0

Fbar = faradaysConstant / gasConstant / temperature

meshBuilder = MeshBuilder(params)
mesh = meshBuilder.mesh

dt = fp.Variable(dt)

potential = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$\psi$')
potential[:] = -appliedPotential

cupric = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$c_{cu}$')
cupric[:] = bulkCupric
cupric.constrain(bulkCupric, mesh.facesTop)

suppressor = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$c_{\theta}$')
suppressor[:] = bulkSuppressor
suppressor.constrain(bulkSuppressor, mesh.facesTop)

distance = DVNU(mesh=mesh, value=1.)
distance.setValue(-1., where=mesh.y < -featureDepth)
distance.setValue(-1., where=(mesh.y < 0) & (mesh.x < params.rinner))        
distance.setValue(-1., where=(mesh.y < 0) & (mesh.x > params.router))

distance.calcDistanceFunction(order=1)

# fp.Viewer(distance).plot()
# raw_input('stopped')

extension = fp.CellVariable(mesh=mesh)

class _InterfaceVar(_InterfaceSurfactantVariable):
    def _calcValue(self):
        return np.minimum(1, super(_InterfaceVar, self)._calcValue())

theta = fp.SurfactantVariable(distanceVar=distance, hasOld=True, name=r'$\theta$', value=0.)
interfaceTheta = _InterfaceVar(theta)

I0 = (i0 + i1 * interfaceTheta)
baseCurrent = I0 * (numerix.exp(alpha * Fbar * potential) \
                        - numerix.exp(-(2 - alpha) * Fbar * potential))
cbar =  cupric / bulkCupric
current = cbar * baseCurrent
currentDerivative = cbar * I0 * (alpha * Fbar *  numerix.exp(alpha * Fbar * potential) \
                                     + (2 - alpha) * Fbar * numerix.exp(-(2 - alpha) * Fbar * potential))

upper = fp.CellVariable(mesh=mesh)
ID = mesh._getNearestCellID(mesh.faceCenters[:,mesh.facesTop.value])

upper[ID] = kappa / mesh.dy[-1] / (params.deltaRef - params.delta + mesh.dy[-1])

surface = distance.cellInterfaceAreas / distance.mesh.cellVolumes
area = 1.
harmonic = (distance >= 0).harmonicFaceValue

potentialEq = fp.TransientTerm(capacitance * surface + (distance < 0)) == \
  fp.DiffusionTerm(kappa * area * harmonic) \
  - surface * (current - potential * currentDerivative) \
  - fp.ImplicitSourceTerm(surface * currentDerivative) \
  - upper * appliedPotential - fp.ImplicitSourceTerm(upper) 
    
cupricEq = fp.TransientTerm(area) == fp.DiffusionTerm(diffusionCupric * area * harmonic) \
  - fp.ImplicitSourceTerm(baseCurrent * surface / (bulkCupric * charge * faradaysConstant))

suppressorEq = fp.TransientTerm(area) == fp.DiffusionTerm(diffusionSuppressor * area * harmonic) \
  - fp.ImplicitSourceTerm(gamma * kPlus * (1 - interfaceTheta) * surface)

depositionRate = current * omega / charge / faradaysConstant
adsorptionCoeff = dt * suppressor * kPlus
thetaEq = fp.TransientTerm() == fp.ExplicitUpwindConvectionTerm(fp.SurfactantConvectionVariable(distance)) \
          + adsorptionCoeff * surface \
          - fp.ImplicitSourceTerm(adsorptionCoeff * distance._cellInterfaceFlag) \
          - fp.ImplicitSourceTerm(params.kMinus * depositionRate * dt)

advectionEq = fp.TransientTerm() + fp.AdvectionTerm(extension)


potentialBar = -potential / appliedPotential
potentialBar.name = r'$\bar{\eta}$'
cbar.name = r'$\bar{c_{cu}}$'
suppressorBar = suppressor / bulkSuppressor
suppressorBar.name = r'$\bar{c_{\theta}}$'

extensionGlobalValue = max(extension.globalValue)

def extend(depositionRate, extend, distance):
    extension[:] = depositionRate
    distance.extendVariable(extension)
    return max(extension.globalValue)

redo_timestep = False

variables = [potential, cupric, suppressor, theta]
equations =  [potentialEq, cupricEq, suppressorEq, thetaEq]
solvers = [fp.LinearPCGSolver(tolerance=solver_tol)] * 4
dts = [None, None, None, 1.]
zipped = zip(variables, equations, solvers, dts)

## create extra arguments for writing to the data file
writes = [params.write_potential, params.write_cupric, params.write_suppressor, params.write_theta]
names = ['potential', 'cupric', 'suppressor', 'theta']
data_args = dict((n, v) for w, n, v in zip(writes, names, variables) if w)
dataFile = os.path.join(tempfile.gettempdir(), 'data.h5')

while (step < params.totalSteps) and (elapsedTime < params.totalTime):

    for v in variables:
        v.updateOld()
    distanceOld = numerix.array(distance).copy()

    if (dataFile is not None) and (step % params.data_frequency == 0) and (not redo_timestep):
        write_data(dataFile, elapsedTime, distance, step,
                   extensionGlobalValue=extensionGlobalValue,
                   **data_args)
        print 'write'
        if step > 0 and extensionGlobalValue < params.shutdown_deposition_rate:
            break
        
    if (step % int(params.levelset_update_ncell / CFL) == 0):
        if params.delete_islands:
            distance.deleteIslands()
        distance.calcDistanceFunction(order=1)

    extensionGlobalValue = extend(depositionRate, extend, distance)

    dt.setValue(min(float(CFL * meshBuilder.dx / extensionGlobalValue), float(dt) * 1.1))
    dt.setValue(min((float(dt), params.dtMax)))
    dt.setValue(max((float(dt), dtMin)))

    advectionEq.solve(distance, dt=dt, solver=trilinos.LinearLUSolver())

    for sweep in range(params.sweeps):
        res = [eqn.sweep(v, dt=dt_ or dt, solver=s) for v, eqn, s, dt_ in zipped]
        print 'sweep: {0}, res: {1}'.format(sweep, res)

    extensionGlobalValue = extend(depositionRate, extend, distance)
    if float(dt) > (CFL * meshBuilder.dx / extensionGlobalValue * 1.1):
        dt.setValue(float(dt) * 0.1)
        print 'redo time step'
        print 'new dt',float(dt)
        potential[:] = potential.old
        cupric[:] = cupric.old
        suppressor[:] = suppressor.old
        theta[:] = theta.old
        distance[:] = distanceOld
        redo_timestep = True
    else:
        elapsedTime += float(dt)
        step += 1
        redo_timestep = False
    
    print 'dt',dt
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


    
