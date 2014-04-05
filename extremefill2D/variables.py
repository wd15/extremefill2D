import os
import tempfile


import numpy as np
from fipy.variables.surfactantVariable import _InterfaceSurfactantVariable
import fipy as fp
from fipy import numerix
from dicttable import DictTable


class _InterfaceVar(_InterfaceSurfactantVariable):
    def _calcValue(self):
        return np.minimum(1, super(_InterfaceVar, self)._calcValue())

    
class ExtremeFillVariable(fp.CellVariable):
    def __init__(self, params, *args, **kwargs):
        super(ExtremeFillVariable, self).__init__(*args, **kwargs)
        self.initialize(params)

    def initialize(self, params):
        raise NotImplementedError
    
    
class PotentialVariable(ExtremeFillVariable):
    def initialize(self, params):
        self[:] = -params.appliedPotential

        
class CupricVariable(ExtremeFillVariable):
    def initialize(self, params):
        self[:] = params.bulkCupric
        self.constrain(params.bulkCupric, self.mesh.facesTop)

        
class SuppressorVariable(ExtremeFillVariable):
    def initialize(self, params):
        self[:] = params.bulkSuppressor
        self.constrain(params.bulkSuppressor, self.mesh.facesTop)


class DistanceVariableNonUniform(fp.DistanceVariable):
    def __init__(self, params, *args, **kwargs):
        super(DistanceVariableNonUniform, self).__init__(*args, **kwargs)
        self.setValue(-1., where=self.mesh.y < -params.featureDepth)
        self.setValue(-1., where=(self.mesh.y < 0) & (self.mesh.x < params.rinner))        
        self.setValue(-1., where=(self.mesh.y < 0) & (self.mesh.x > params.router))
        self.calcDistanceFunction(order=1)
        
    def getLSMshape(self):
        mesh = self.mesh

        min_dx = lambda x: fp.numerix.amin(x) if len(fp.numerix.shape(x)) > 0 else x
        
        if hasattr(mesh, 'nz'):
            raise Exception, "3D meshes not yet implemented"
        elif hasattr(mesh, 'ny'):
            dx = (min_dx(mesh.dy), min_dx(mesh.dx))
            shape = (mesh.ny, mesh.nx)
        elif hasattr(mesh, 'nx'):
            dx = (min_dx(mesh.dx),)
            shape = mesh.shape
        else:
            raise Exception, "Non grid meshes can not be used for solving the FMM."

        return dx, shape

    def deleteIslands(self):
        from fipy.tools.numerix import MA

        cellToCellIDs = self.mesh._getCellToCellIDs()
        adjVals = numerix.take(self.value, cellToCellIDs)
        adjInterfaceValues = MA.masked_array(adjVals, mask = (adjVals * self.value) > 0)
        masksum = numerix.sum(numerix.logical_not(MA.getmask(adjInterfaceValues)), 0)
        tmp = MA.logical_and(masksum == 4, self.value > 0)
        self.value = numerix.array(MA.where(tmp, -1, self.value))


class AreaVariable(fp.Variable):
    def __init__(self, var, distance):
        super(AreaVariable, self).__init__()
        self.var = self._requires(var)
        self.distance = self._requires(distance)
        
    def _calcValue(self):
        return float(numerix.sum(np.array(self.var) * np.array(self.distance.cellInterfaceAreas)))

    
class Variables(object):
    def __init__(self, params, mesh):
        self.dt = fp.Variable(params.dt)
        self.potential = PotentialVariable(params, mesh=mesh, hasOld=True, name=r'$\psi$')
        self.cupric = CupricVariable(params, mesh=mesh, hasOld=True, name=r'$c_{cu}$')
        self.suppressor = SuppressorVariable(params, mesh=mesh, hasOld=True, name=r'$c_{\theta}$')
        self.distance = DistanceVariableNonUniform(params, mesh=mesh, value=1.)
        self.extension = fp.CellVariable(mesh=mesh)
        self.theta = fp.SurfactantVariable(distanceVar=self.distance, hasOld=True, name=r'$\theta$', value=0.)
        self.interfaceTheta = _InterfaceVar(self.theta)
        self.calc_dep_vars(params)
        self.vars = (self.potential, self.cupric, self.suppressor, self.theta)
        self.dataFile = os.path.join(tempfile.gettempdir(), 'data.h5')
        self.params = params
        self.appliedPotential = fp.Variable(params.appliedPotential)
        self.current = AreaVariable(self.currentDensity, self.distance)
        self.harmonic = (self.distance >= 0).harmonicFaceValue
        self.surface = self.distance.cellInterfaceAreas / self.distance.mesh.cellVolumes
                
    def calc_dep_vars(self, params):
        Fbar = params.faradaysConstant / params.gasConstant / params.temperature
        self.coeff_forward = params.alpha * Fbar
        self.coeff_backward = (2 - params.alpha) * Fbar
        exp_forward = numerix.exp(self.coeff_forward * self.potential)
        exp_backward = numerix.exp(-self.coeff_backward * self.potential)
        I0 = (params.i0 + params.i1 * self.interfaceTheta)
        cbar =  self.cupric / params.bulkCupric

        self.beta_forward = cbar * I0 * exp_forward
        self.beta_backward = cbar * I0 * exp_backward
        self.baseCurrent = I0 * (exp_forward - exp_backward)
        self.currentDensity = cbar * self.baseCurrent
        self.currentDerivative = cbar * I0 * (self.coeff_forward *  exp_forward + self.coeff_backward * exp_backward)
        self.depositionRate = self.currentDensity * params.omega / params.charge / params.faradaysConstant

    def extend(self):
        self.extension[:] = self.depositionRate
        self.distance.extendVariable(self.extension)
        return max(self.extension.globalValue)

    def updateOld(self):
        for v in self.vars:
            v.updateOld()
        self.distanceOld = numerix.array(self.distance).copy()

    def retreat_step(self):
        self.dt.setValue(float(self.dt) * 0.1)
        for v in self.vars:
            v[:] = v.old
        self.distance[:] = self.distanceOld

    def update_dt(self, params, mesh):
        extensionGlobalValue = self.extend()
        self.dt.setValue(min(float(params.CFL * mesh.nominal_dx / extensionGlobalValue), float(self.dt) * 1.1))
        self.dt.setValue(min((float(self.dt), params.dtMax)))
        self.dt.setValue(max((float(self.dt), params.dtMin)))

    def write_data(self, elapsedTime, timeStep, **kwargs):
        h5data = DictTable(self.dataFile, 'a')
        mesh = self.distance.mesh
        dataDict = {'elapsedTime' : elapsedTime,
                    'nx' : mesh.nx,
                    'ny' : mesh.ny,
                    'dx' : mesh.dx,
                    'dy' : mesh.dy,
                    'distance' : np.array(self.distance)}
        for k, v in self.params.write_data.iteritems():
            if v:
                dataDict[k] = np.array(getattr(self, k))
        h5data[timeStep] = dict(dataDict.items() + kwargs.items())

