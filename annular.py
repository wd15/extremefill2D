#!/usr/bin/env python

__docformat__ = 'restructuredtext'

import tables
import fipy as fp
from fipy import numerix
import numpy as np
import imp
import sys
import os
import tempfile
from tools import write_data
from fipy.variables.surfactantVariable import _InterfaceSurfactantVariable
import shutil

filename = sys.argv[1]
filenamec = filename + 'c'
params = imp.load_source('params', filename)
if os.path.exists(filenamec):
    os.remove(filenamec)

totalSteps = params.totalSteps
sweeps = params.sweeps
tol = params.tol
appliedPotential = params.appliedPotential
deltaRef = params.deltaRef
featureDepth = params.featureDepth
Nx = params.Nx
CFL = params.CFL
dataFile = os.path.join(tempfile.gettempdir(), 'data.h5')
kPlus = params.kPlus
kMinus = params.kMinus
featureDepth = params.featureDepth
bulkSuppressor = params.bulkSuppressor
rinner = params.rinner
router = params.router
rboundary = params.rboundary
dtMax = params.dtMax
levelset_update_frequency = params.levelset_update_frequency
totalTime=params.totalTime

dtMin = .5e-7
dt = 0.01
delta = 150e-6
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
data_frequency=1
NxBase=1000
solver_tol=1e-10

Fbar = faradaysConstant / gasConstant / temperature

distanceBelowTrench = delta * 0.1
L = delta + featureDepth + distanceBelowTrench
ny = Nx
dy = L / Nx
dx = dy
nx = int(rboundary / dx)
mesh = fp.CylindricalGrid2D(nx=nx, dx=dx, ny=ny, dy=dy) - [[-dx / 100.], [distanceBelowTrench + featureDepth]]

dt = fp.Variable(dt)

potential = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$\psi$')
potential[:] = -appliedPotential

cupric = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$c_{cu}$')
cupric[:] = bulkCupric
cupric.constrain(bulkCupric, mesh.facesTop)

suppressor = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$c_{\theta}$')
suppressor[:] = bulkSuppressor
suppressor.constrain(bulkSuppressor, mesh.facesTop)

distance = fp.DistanceVariable(mesh=mesh, value=1.)
distance.setValue(-1., where=mesh.y < -featureDepth)
distance.setValue(-1., where=(mesh.y < 0) & (mesh.x < rinner))        
distance.setValue(-1., where=(mesh.y < 0) & (mesh.x > router))
distance.calcDistanceFunction()

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
upper[ID] = kappa / mesh.dx / (deltaRef - delta)

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
          - fp.ImplicitSourceTerm(kMinus * depositionRate * dt)

advectionEq = fp.TransientTerm() + fp.AdvectionTerm(extension)

elapsedTime = 0.
step = 0

potentialBar = -potential / appliedPotential
potentialBar.name = r'$\bar{\eta}$'
cbar.name = r'$\bar{c_{cu}}$'
suppressorBar = suppressor / bulkSuppressor
suppressorBar.name = r'$\bar{c_{\theta}}$'

potentialSolver = fp.LinearPCGSolver(tolerance=solver_tol)
cupricSolver = fp.LinearPCGSolver(tolerance=solver_tol)
suppressorSolver = fp.LinearPCGSolver(tolerance=solver_tol)
thetaSolver = fp.LinearPCGSolver(tolerance=solver_tol)

while (step < totalSteps) and (elapsedTime < totalTime):
    
    potential.updateOld()
    cupric.updateOld()
    suppressor.updateOld()
    theta.updateOld()

    if dataFile is not None and step % data_frequency == 0:
        write_data(dataFile, elapsedTime, distance, step, potential, cupric, suppressor, interfaceTheta)
    
    if step % levelset_update_frequency == 0:
        distance.calcDistanceFunction()

    extension[:] = depositionRate

    distance.extendVariable(extension)

    dt.setValue(min(float(CFL * mesh.dx / max(extension.globalValue)), float(dt) * 1.1))
    dt.setValue(min((float(dt), dtMax)))
    dt.setValue(max((float(dt), dtMin)))

    advectionEq.solve(distance, dt=dt)

    for sweep in range(sweeps):

        potentialRes = potentialEq.sweep(potential, dt=dt, solver=potentialSolver)
        cupricRes = cupricEq.sweep(cupric, dt=dt, solver=cupricSolver)
        suppressorRes = suppressorEq.sweep(suppressor, dt=dt, solver=suppressorSolver)
        thetaRes = thetaEq.sweep(theta, dt=1., solver=thetaSolver)
        res = numerix.array((potentialRes, cupricRes, suppressorRes, thetaRes))

        print 'sweep: {0}, res: {0}'.format(sweep, res)


    print 'dt',dt
    print 'elapsed time',elapsedTime
    print 'step',step
    import datetime
    print 'time: ',datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print

    elapsedTime += float(dt)

    step += 1
        
if not hasattr(params, 'sumatra_label'):
    params.sumatra_label = '.'

finaldir = os.path.join('Data', params.sumatra_label)

shutil.move(dataFile, finaldir)


