import os
import shutil
from collections import OrderedDict


import numpy as np
from extremefill2D.tools import build_mesh, print_data
from extremefill2D.variables import Variables
from extremefill2D.equations import PotentialEquation, CupricEquation
from extremefill2D.equations import SuppressorEquation, ThetaEquation
from extremefill2D.equations import AdvectionEquation, AppliedPotentialEquation
from extremefill2D.dicttable import DictTable


class ExtremeFillSystem(object):
    def __init__(self, params, datafile=None):
        self.params = params
        self.datafile = datafile

        mesh = build_mesh(params)
        
        self.variables = Variables(params, mesh)
        
        self.potential = PotentialEquation(params, self.variables)
        self.cupric = CupricEquation(params, self.variables)
        self.suppressor = SuppressorEquation(params, self.variables)
        self.theta = ThetaEquation(params, self.variables)
        self.advection = AdvectionEquation(params, self.variables)

    def sweep(self, dt):
        residuals = OrderedDict()
        for name in ('potential', 'cupric', 'suppressor', 'theta'):
            residuals[name] = getattr(self, name).sweep(dt)
        return residuals

    def write_data(self, elapsedTime, timeStep, **kwargs):
        h5data = DictTable(self.datafile, 'a')
        mesh = self.variables.distance.mesh
        dataDict = {'elapsedTime' : elapsedTime,
                    'nx' : mesh.nx,
                    'ny' : mesh.ny,
                    'dx' : mesh.dx,
                    'dy' : mesh.dy,
                    'distance' : np.array(self.variables.distance)}
        # for k, v in self.params.write_data.iteritems():
        #     if v:
        #         dataDict[k] = np.array(getattr(self, k))
        h5data[timeStep] = dict(dataDict.items() + kwargs.items())
    
    def run(self):
        params = self.params
        variables = self.variables
        mesh = self.variables.distance.mesh
        
        redo_timestep = False
        elapsedTime = 0.0
        step = 0
        extensionGlobalValue = max(self.variables.extension.globalValue)

        while (step < params.totalSteps) and (elapsedTime < params.totalTime):

            variables.updateOld()

            if self.datafile and (step % params.data_frequency == 0) and (not redo_timestep):
                self.write_data(elapsedTime, step)
                if step > 0 and extensionGlobalValue < params.shutdown_deposition_rate:
                    break

            if (step % int(params.levelset_update_ncell / params.CFL) == 0):
                variables.distance.deleteIslands()
                variables.distance.calcDistanceFunction(order=1)

            variables.update_dt(params, mesh)

            self.advection.solve(dt=variables.dt)

            residuals = [self.sweep(variables.dt) for _ in range(params.sweeps)]

            extensionGlobalValue = variables.extend()

            if float(variables.dt) > (params.CFL * mesh.nominal_dx / extensionGlobalValue * 1.1):
                variables.retreat_step()
                redo_timestep = True
            else:
                elapsedTime += float(variables.dt)
                step += 1
                redo_timestep = False

            print_data(step, elapsedTime, variables.dt, redo_timestep, residuals, current=float(variables.current))


class ConstantCurrentSystem(ExtremeFillSystem):
    def __init__(self, params):
        super(ConstantCurrentSystem, self).__init__(params)
        self.appliedPotentialEqn = AppliedPotentialEquation(params, self.variables)
        
    def sweep(self, dt):
        residual = self.appliedPotentialEqn.sweep(dt)
        residuals = super(ConstantCurrentSystem, self).sweep(dt)
        residuals['appliedPotential'] = residual
        residuals['current'] = float(self.variables.current)
        return residuals
    
