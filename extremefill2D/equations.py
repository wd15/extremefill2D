import fipy as fp
import fipy.solvers.trilinos as trilinos
from extremefill2D.variables import AreaVariable
import numpy as np
import scipy


class AdvectionEquation(object):
    def __init__(self, params, variables):
        self.equation = fp.TransientTerm() + fp.AdvectionTerm(variables.extension)
        self.solver = trilinos.LinearLUSolver()
        self.var = variables.distance

    def solve(self, dt):
        self.equation.solve(self.var, dt=dt, solver=self.solver)


class AppliedPotentialEquation(object):
    def __init__(self, variables):
        self.var = variables.appliedPotential
        self.I0 = variables.current
        self._b0 = AreaVariable(variables.beta_forward, variables.distance)
        self._b1 = AreaVariable(variables.beta_backward, variables.distance)
        self._c0 = self.variables.coeff_forward
        self._c1 = self.variables.coeff_backward

    def sweep(self, dt):
        b0 = float(self._b0)
        b1 = float(self._b1)
        c0 = float(self._c0)
        c1 = float(self._c1)
        I0 = float(self.I0)

        f = lambda e: b0 * np.exp(c0 * e) - b1 * np.exp(-c1 * e) - I0
        fprime = lambda e: b0 * c0 * np.exp(c0 * e) + b1 * c1 * np.exp(-c1 * e)
        
        e = scipy.fsolve(f, 0., fprime=fprime)
        self.var.setValue(float(self.var) + e)

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
        - upper * params.appliedPotential - fp.ImplicitSourceTerm(upper) 
        self.solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        self.var = variables.potential


class CupricEquation(SweepEquation):
    def __init__(self, params, variables):
        self.equation = fp.TransientTerm() == fp.DiffusionTerm(params.diffusionCupric * variables.harmonic) \
          - fp.ImplicitSourceTerm(variables.baseCurrent * variables.surface / (params.bulkCupric * params.charge * params.faradaysConstant))
        self.solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        self.var = variables.cupric


class SuppressorEquation(SweepEquation):
    def __init__(self, params, variables):
        self.equation = fp.TransientTerm() == fp.DiffusionTerm(params.diffusionSuppressor * variables.harmonic) \
          - fp.ImplicitSourceTerm(params.gamma * params.kPlus * (1 - variables.interfaceTheta) * variables.surface)
        self.solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        self.var = variables.suppressor


class ThetaEquation(SweepEquation):
    def __init__(self, params, variables):
        adsorptionCoeff = variables.dt * variables.suppressor * params.kPlus
        self.equation = fp.TransientTerm() == fp.ExplicitUpwindConvectionTerm(fp.SurfactantConvectionVariable(variables.distance)) \
          + adsorptionCoeff * variables.surface \
          - fp.ImplicitSourceTerm(adsorptionCoeff * variables.distance._cellInterfaceFlag) \
          - fp.ImplicitSourceTerm(params.kMinus * variables.depositionRate * variables.dt)
        self.var = variables.theta
        self.solver = fp.LinearPCGSolver(tolerance=params.solver_tol)

    def sweep(self, dt):
        return super(ThetaEquation, self).sweep(dt=1.)

    
class Equations(object):
    def __init__(self, params, variables):
        self.potential = PotentialEquation(params, variables)
        self.cupric = CupricEquation(params, variables)
        self.suppressor = SuppressorEquation(params, variables)
        self.theta = ThetaEquation(params, variables)
        self.advection = AdvectionEquation(params, variables)

    def sweep(self, dt):
        eqns = (self.potential, self.cupric, self.suppressor, self.theta)
        return [eqn.sweep(dt) for eqn in eqns]

        
        
