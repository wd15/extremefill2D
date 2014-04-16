import tables
import numpy as np
from fipy.variables.surfactantVariable import _InterfaceSurfactantVariable
import fipy as fp
from fipy import numerix


class _InterfaceVar(_InterfaceSurfactantVariable):
    def _calcValue(self):
        return np.minimum(1, super(_InterfaceVar, self)._calcValue())

    
class PotentialVariable(fp.CellVariable):
    def __init__(self, params, mesh):
        super(PotentialVariable, self).__init__(mesh=mesh, hasOld=True, name=r'$\psi$')
        self[:] = -params.appliedPotential


class CupricVariable(fp.CellVariable):
    def __init__(self, params, mesh):
        super(CupricVariable, self).__init__(mesh=mesh, hasOld=True, name=r'$c_{cu}$')
        self[:] = params.bulkCupric
        self.constrain(params.bulkCupric, self.mesh.facesTop)

        
class SuppressorVariable(fp.CellVariable):
    def __init__(self, params, mesh):
        super(SuppressorVariable, self).__init__(mesh=mesh, hasOld=True, name=r'$c_{\theta}$')
        self[:] = params.bulkSuppressor
        self.constrain(params.bulkSuppressor, self.mesh.facesTop)

        
class DistanceVariableNonUniform(fp.DistanceVariable):
    def __init__(self, params, mesh):
        super(DistanceVariableNonUniform, self).__init__(mesh=mesh, value=1.)
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
    def __init__(self, params, mesh, deposition_mask=True):
        self.potential = PotentialVariable(params, mesh)
        self.cupric = CupricVariable(params, mesh)
        self.suppressor = SuppressorVariable(params, mesh)
        self.distance = DistanceVariableNonUniform(params, mesh)
        self.extension = fp.CellVariable(mesh=mesh)
        self.theta = fp.SurfactantVariable(distanceVar=self.distance, hasOld=True, name=r'$\theta$', value=0.)
        self.interfaceTheta = _InterfaceVar(self.theta)
        self.calc_dep_vars(params)
        self.vars = (self.potential, self.cupric, self.suppressor, self.theta)
        self.params = params
        self.appliedPotential = fp.Variable(params.appliedPotential)
        self.current = AreaVariable(self.currentDensity, self.distance)
        self.harmonic = (self.distance > 0).harmonicFaceValue
        self.masked_harmonic = ((self.distance > 0) * deposition_mask).harmonicFaceValue
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

