import tables
import numpy as np
from fipy.variables.surfactantVariable import _InterfaceSurfactantVariable
import fipy as fp
from fipy import numerix
from fipy.tools.numerix import MA
from extremefill2D.tools import find_all_zeros


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
            raise(Exception, "3D meshes not yet implemented")
        elif hasattr(mesh, 'ny'):
            dx = (min_dx(mesh.dy), min_dx(mesh.dx))
            shape = (mesh.ny, mesh.nx)
        elif hasattr(mesh, 'nx'):
            dx = (min_dx(mesh.dx),)
            shape = mesh.shape
        else:
            raise(Exception, "Non grid meshes can not be used for solving the FMM.")

        return dx, shape

    def deleteIslands(self):
        cellToCellIDs = self.mesh._cellToCellIDs
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


class DepositionMask(fp.CellVariable):
    def __init__(self, distance, params):
        super(DepositionMask, self).__init__(distance.mesh, hasOld=False)
        self.distance = self._requires(distance)
        self.params = params
        self.mask = self.get_mask()

    def get_mask(self):
        mesh = self.mesh
        mask = np.ones(mesh.x.shape, dtype=int)
        Y = mesh.nominal_dx
        X = self.params.router - mesh.nominal_dx
        mask[(mesh.y.value < Y) & (mesh.x.value > X)] = 0
        return mask

    def _calcValue(self):
        flag = MA.filled(numerix.take(self.distance._interfaceFlag, self.mesh.cellFaceIDs), 0)
        flag = numerix.sum(flag, axis=0)
        corner_flag = numerix.where(numerix.logical_and(self.distance.value > 0, flag > 1), 1, 0)

        return corner_flag | self.mask


class CapVariable(fp.CellVariable):
    def __init__(self, distance, params):
        super(CapVariable, self).__init__(distance.mesh, hasOld=False)
        self.distance = self._requires(distance)
        self.params = params
        self.ymin = min(self.mesh.y)
        self.ymax = max(self.mesh.y)
        N = 1000
        X = np.zeros(N)
        Y = np.linspace(self.ymin, self.ymax, 1000)
        self.X, self.Y = X, Y
        if not hasattr(self, 'nearestCellIDs'):
            self.nearestCellIDs = self.mesh._getNearestCellID((X, Y))

    def getInterfaceHeight(self):
        from scipy.interpolate import interp1d
        X, Y = self.X, self.Y
        phi = self.distance((X, Y), order=0, nearestCellIDs=self.nearestCellIDs)
        zeros = find_all_zeros(interp1d(Y, phi), Y[0], Y[-1])
        if len(zeros) > 0:
            height = zeros[-1]
        else:
            height = self.ymax
        return height

    def _calcValue(self):
        mesh = self.mesh
        y0 = self.getInterfaceHeight()
        if hasattr(self.params, 'cap_radius'):
            cap_radius = self.params.cap_radius
        else:
            cap_radius = 0.0
        if not hasattr(self, 'spacing'):
            self.spacing = self.ymax - y0
        center = (0.0, y0 + self.spacing)
        radius = np.sqrt((mesh.x - center[0])**2 + (mesh.y - center[1])**2)
        return np.where(radius > cap_radius, 0, 1)


class Variables(object):
    def __init__(self, params, mesh):
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
        self.harmonic = (self.distance >= 0).harmonicFaceValue
        self.masked_harmonic = self.harmonic
        self.surface = self.distance.cellInterfaceAreas / self.distance.mesh.cellVolumes
        self.cap = CapVariable(self.distance, params)

    def calc_dep_vars(self, params):
        Fbar = params.faradaysConstant / params.gasConstant / params.temperature
        self.coeff_forward0 = params.alpha0 * Fbar
        self.coeff_backward0 = (1 - params.alpha0) * Fbar
        self.coeff_forward1 = params.alpha1 * Fbar
        self.coeff_backward1 = (1 - params.alpha1) * Fbar
        exp_forward0 = numerix.exp(self.coeff_forward0 * self.potential)
        exp_backward0 = numerix.exp(-self.coeff_backward0 * self.potential)
        exp_forward1 = numerix.exp(self.coeff_forward1 * self.potential)
        exp_backward1 = numerix.exp(-self.coeff_backward1 * self.potential)
        cbar =  self.cupric / params.bulkCupric

        I0 = params.i0 * (1 - self.theta)
        I1 = params.i1 * self.theta

        self.beta_forward0 = cbar * I0 * exp_forward0
        self.beta_backward0 = cbar * I0 * exp_backward0
        self.beta_forward1 = cbar * I1 * exp_forward1
        self.beta_backward1 = cbar * I1 * exp_backward1

        self.baseCurrent = I0 * (exp_forward0 - exp_backward0) + I1 * (exp_forward1 - exp_backward1)
        self.currentDensity = cbar * self.baseCurrent
        self.currentDerivative = cbar * (I0 * (self.coeff_forward0 *  exp_forward0 + self.coeff_backward0 * exp_backward0) \
                                         + I1 * (self.coeff_forward1 *  exp_forward1 + self.coeff_backward1 * exp_backward1))
        self.depositionRate = self.currentDensity * params.omega / params.charge / params.faradaysConstant


class MaskedVariablesCorner(Variables):
    def __init__(self, params, mesh):
        super(MaskedVariablesCorner, self).__init__(params, mesh)
        deposition_mask = DepositionMask(self.distance, params).mask
        self.masked_harmonic = ((self.distance > 0) * deposition_mask).harmonicFaceValue


class MaskedVariablesNoCorner(Variables):
    def __init__(self, params, mesh):
        super(MaskedVariablesNoCorner, self).__init__(params, mesh)
        deposition_mask = DepositionMask(self.distance, params)
        self.masked_harmonic = ((self.distance > 0) * deposition_mask).harmonicFaceValue
