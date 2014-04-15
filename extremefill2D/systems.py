import os
import shutil
from collections import OrderedDict


import pandas as pd
import numpy as np
import fipy as fp
from extremefill2D.variables import Variables
from extremefill2D.equations import PotentialEquation, CupricEquation
from extremefill2D.equations import SuppressorEquation, ThetaEquation
from extremefill2D.equations import AdvectionEquation, AppliedPotentialEquation
from extremefill2D.dicttable import DictTable
from extremefill2D.variables import PotentialVariable, CupricVariable
from extremefill2D.variables import SuppressorVariable, DistanceVariableNonUniform
from extremefill2D.variables import _InterfaceVar, AreaVariable
from extremefill2D.meshes import ExtremeFill2DMesh

class ExtremeFillSystem(object):
    def __init__(self, params, datafile=None):
        self.params = params
        self.datafile = datafile

        mesh = ExtremeFill2DMesh(params)
        
        variables = Variables(params, mesh)
        self.distance = variables.distance
        self.extension = variables.extension
        self.current = variables.current
        self.depositionRate = variables.depositionRate
        self.variables = variables
        self.equations = (PotentialEquation(params, variables),
                          CupricEquation(params, variables),
                          SuppressorEquation(params, variables),
                          ThetaEquation(params, variables))
        
        self.advection = AdvectionEquation(params, variables)

    def sweep(self, dt):
        return OrderedDict([[eqn.var.name, eqn.sweep(dt)] for eqn in self.equations])

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

    def updateOld(self):
        for eqn in self.equations:
            eqn.var.updateOld()
        self.distanceOld = fp.numerix.array(self.distance).copy()
        
    def update_dt(self, dt, params, mesh):
        extensionGlobalValue = self.extend()
        dt = min(float(params.CFL * mesh.nominal_dx / extensionGlobalValue), dt * 1.1)
        dt = min(dt, params.dtMax)
        return max(dt, params.dtMin)

    def extend(self):
        self.extension[:] = self.depositionRate
        self.distance.extendVariable(self.extension)
        return max(self.extension.globalValue)

    def revert_step(self, dt):
        dt = dt * 0.1
        for eqn in self.equations:
            eqn.var[:] = eqn.var.old
        self.distance[:] = self.distanceOld
        return dt

    def print_data(self, step, elapsedTime, dt, redo_timestep, residuals):
        df = pd.DataFrame({'Step Number' : [step],
                           'Elapsed Time' : [elapsedTime],
                           'dt' : [dt],
                           'Redo Timestep' : [redo_timestep]})

        col_width = 15
        float_format=lambda x: ('{:10.3e}'.format(x)).rjust(col_width)
        df_residuals = pd.DataFrame(residuals)
        
        print
        print
        print df.to_string(columns=['Step Number', 'dt', 'Elapsed Time', 'Redo Timestep'],
                           index=False,
                           col_space=3,
                           justify='right',
                           formatters={'Elapsed Time' : float_format,
                                       'dt' : float_format,
                                       'Redo Timestep' : lambda x: str(x).rjust(col_width),
                                       'Step Number' : lambda x: str(x).rjust(col_width)})
        print
        print df_residuals.to_string(float_format=float_format)
        
    def run(self):
        params = self.params
        mesh = self.distance.mesh
        
        redo_timestep = False
        elapsedTime = 0.0
        step = 0
        dt = params.dt
        extensionGlobalValue = max(self.variables.extension.globalValue)

        while (step < params.totalSteps) and (elapsedTime < params.totalTime):

            self.updateOld()

            if self.datafile and (step % params.data_frequency == 0) and (not redo_timestep):
                self.write_data(elapsedTime, step)
                if step > 0 and extensionGlobalValue < params.shutdown_deposition_rate:
                    break

            if (step % int(params.levelset_update_ncell / params.CFL) == 0):
                self.distance.deleteIslands()
                self.distance.calcDistanceFunction(order=1)

            dt = self.update_dt(dt, params, mesh)

            self.advection.solve(dt)

            residuals = [self.sweep(dt) for _ in range(params.sweeps)]

            extensionGlobalValue = self.extend()

            if dt > (params.CFL * mesh.nominal_dx / extensionGlobalValue * 1.1):
                dt = self.revert_step(dt)
                redo_timestep = True
            else:
                elapsedTime += dt
                step += 1
                redo_timestep = False

            self.print_data(step, elapsedTime, dt, redo_timestep, residuals)


class ConstantCurrentSystem(ExtremeFillSystem):
    def __init__(self, params, datafile=None):
        super(ConstantCurrentSystem, self).__init__(params, datafile)
        self.appliedPotentialEqn = AppliedPotentialEquation(params, self.variables)
        
    def sweep(self, dt):
        residual = self.appliedPotentialEqn.sweep(dt)
        residuals = super(ConstantCurrentSystem, self).sweep(dt)
        residuals['appliedPotential'] = residual
        residuals['current'] = float(self.variables.current)
        return residuals
    
