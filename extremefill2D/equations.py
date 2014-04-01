import fipy as fp
import fipy.solvers.trilinos as trilinos

class AdvectionEquation(object):
    def __init__(self, params, variables):
        self.equation = fp.TransientTerm() + fp.AdvectionTerm(variables.extension)
        self.solver = trilinos.LinearLUSolver()
        self.var = variables.distance

    def solve(self, dt):
        self.equation.solve(self.var, dt=dt, solver=self.solver)

class Equations(object):
    def __init__(self, params, variables):
        self.harmonic = (variables.distance >= 0).harmonicFaceValue
        self.surface = variables.distance.cellInterfaceAreas / variables.distance.mesh.cellVolumes
        self.calc_potential(params, variables)
        self.calc_cupric(params, variables)
        self.calc_suppressor(params, variables)
        self.calc_theta(params, variables)
        self.advection = AdvectionEquation(params, variables)
        
    def calc_potential(self, params, variables):
        distance = variables.distance
        mesh = distance.mesh
        upper = fp.CellVariable(mesh=mesh)
        ID = mesh._getNearestCellID(mesh.faceCenters[:,mesh.facesTop.value])
        upper[ID] = params.kappa / mesh.dy[-1] / (params.deltaRef - params.delta + mesh.dy[-1])
        
        self.potential = fp.TransientTerm(params.capacitance * self.surface + (distance < 0)) == \
          fp.DiffusionTerm(params.kappa * self.harmonic) \
        - self.surface * (variables.current - variables.potential * variables.currentDerivative) \
        - fp.ImplicitSourceTerm(self.surface * variables.currentDerivative) \
        - upper * params.appliedPotential - fp.ImplicitSourceTerm(upper) 
        self.potential.ef_solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        self.potential.ef_var = variables.potential
        self.potential.ef_dt = None
        
    def calc_cupric(self, params, variables):
        self.cupric = fp.TransientTerm() == fp.DiffusionTerm(params.diffusionCupric * self.harmonic) \
          - fp.ImplicitSourceTerm(variables.baseCurrent * self.surface / (params.bulkCupric * params.charge * params.faradaysConstant))
        self.cupric.ef_solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        self.cupric.ef_var = variables.cupric
        self.cupric.ef_dt = None
        
    def calc_suppressor(self, params, variables):
        self.suppressor = fp.TransientTerm() == fp.DiffusionTerm(params.diffusionSuppressor * self.harmonic) \
          - fp.ImplicitSourceTerm(params.gamma * params.kPlus * (1 - variables.interfaceTheta) * self.surface)
        self.suppressor.ef_solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        self.suppressor.ef_var = variables.suppressor
        self.suppressor.ef_dt = None
        
    def calc_theta(self, params, variables):
        adsorptionCoeff = variables.dt * variables.suppressor * params.kPlus
        self.theta = fp.TransientTerm() == fp.ExplicitUpwindConvectionTerm(fp.SurfactantConvectionVariable(variables.distance)) \
          + adsorptionCoeff * self.surface \
          - fp.ImplicitSourceTerm(adsorptionCoeff * variables.distance._cellInterfaceFlag) \
          - fp.ImplicitSourceTerm(params.kMinus * variables.depositionRate * variables.dt)
        self.theta.ef_dt = 1.
        self.theta.ef_var = variables.theta
        self.theta.ef_solver = fp.LinearPCGSolver(tolerance=params.solver_tol)
        
    def sweep(self, dt):
        eqns = (self.potential, self.cupric, self.suppressor, self.theta)
        return [eqn.sweep(eqn.ef_var, dt=eqn.ef_dt or dt, solver=eqn.ef_solver) for eqn in eqns]

        
        
