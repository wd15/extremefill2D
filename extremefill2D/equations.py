import fipy as fp
import fipy.solvers.scipy as scipy_solvers
from extremefill2D.variables import AreaVariable
import numpy as np
import scipy
import scipy.optimize


class AdvectionEquation(object):
    def __init__(self, params, variables):
        self.equation = fp.TransientTerm() + fp.AdvectionTerm(variables.extension)
        self.solver = scipy_solvers.LinearLUSolver()
        self.var = variables.distance

    def solve(self, dt):
        self.equation.solve(self.var, dt=dt, solver=self.solver)


class AppliedPotentialEquation(object):
    def __init__(self, params, variables):
        self.var = variables.appliedPotential
        self.I0 = params.current
        self._b0 = AreaVariable(variables.beta_forward0, variables.distance)
        self._b1 = AreaVariable(variables.beta_backward0, variables.distance)
        self._c0 = variables.coeff_forward0
        self._c1 = variables.coeff_backward0

    def sweep(self, dt):
        b0 = float(self._b0)
        b1 = float(self._b1)
        c0 = float(self._c0)
        c1 = float(self._c1)
        I0 = float(self.I0)

        f = lambda e: b0 * np.exp(-c0 * e) - b1 * np.exp(c1 * e) - I0
        fprime = lambda e: -b0 * c0 * np.exp(c0 * e) - b1 * c1 * np.exp(-c1 * e)

        delta = scipy.optimize.fsolve(f, 0., fprime=fprime)[0]
        delta = np.sign(delta) * min(abs(float(self.var)) / 10, abs(delta))
        self.var.setValue(float(self.var) + delta)

        return abs(delta)


class SweepEquation(object):
    def sweep(self, dt):
        return self.equation.sweep(self.var, dt=dt, solver=self.solver)


class PotentialEquation(SweepEquation):
    def __init__(self, params, variables):
        distance = variables.distance
        mesh = distance.mesh
        upper = fp.CellVariable(mesh=mesh)
        ID = mesh._getNearestCellID(mesh.faceCenters[:,mesh.facesTop.value])
        upper[ID] = params.kappa / mesh.dy[-1] / (params.deltaRef - params.delta + mesh.dy[-1])
        surface = variables.surface

        self.equation = fp.TransientTerm(params.capacitance * surface + (distance < 0)) == \
          fp.DiffusionTerm(params.kappa * variables.harmonic) \
        - surface * (variables.currentDensity - variables.potential * variables.currentDerivative) \
        - fp.ImplicitSourceTerm(surface * variables.currentDerivative) \
        - upper * variables.appliedPotential - fp.ImplicitSourceTerm(upper)
        self.solver = scipy_solvers.LinearLUSolver()
        self.var = variables.potential


class CupricEquation(SweepEquation):
    def __init__(self, params, variables):
        cap = variables.cap
        self.equation = fp.TransientTerm() == \
          fp.DiffusionTerm(params.diffusionCupric * variables.masked_harmonic) \
        - fp.ImplicitSourceTerm(variables.baseCurrent * variables.surface / \
                                (params.bulkCupric * params.charge * params.faradaysConstant)) \
        + 1e+5 * params.bulkCupric * cap - fp.ImplicitSourceTerm(1e+5 * cap)
        self.solver = scipy_solvers.LinearLUSolver()
        self.var = variables.cupric


class SuppressorEquation(SweepEquation):
    def __init__(self, params, variables):
        self.equation = fp.TransientTerm() == fp.DiffusionTerm(params.diffusionSuppressor * variables.harmonic) \
          - fp.ImplicitSourceTerm(params.gamma * params.kPlus * (1 - variables.interfaceTheta) * variables.surface)
        # self.solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        self.solver = scipy_solvers.LinearLUSolver()
        self.var = variables.suppressor


class ThetaEquation(SweepEquation):
    def __init__(self, params, variables):
        self.dt = fp.Variable(1.)
        adsorptionCoeff = self.dt * variables.suppressor * params.kPlus
        self.equation = fp.TransientTerm() == fp.ExplicitUpwindConvectionTerm(fp.SurfactantConvectionVariable(variables.distance)) \
          + adsorptionCoeff * variables.surface \
          - fp.ImplicitSourceTerm(adsorptionCoeff * variables.distance._cellInterfaceFlag) \
          - fp.ImplicitSourceTerm(params.kMinus * variables.depositionRate * self.dt)
        self.var = variables.theta
        # self.solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        self.solver = scipy_solvers.LinearLUSolver()

    def sweep(self, dt):
        self.dt.setValue(dt)
        return super(ThetaEquation, self).sweep(dt=1.)
