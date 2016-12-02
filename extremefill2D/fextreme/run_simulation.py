"""Functions to run an ExtremeFill2D simulation
"""

from toolz.curried import curry
from collections import OrderedDict

import numpy as np
import fipy as fp

from ..meshes import ExtremeFill2DMesh
from ..variables import Variables
from ..equations import AdvectionEquation
from ..equations import PotentialEquation, CupricEquation
from ..equations import SuppressorEquation, ThetaEquation


@curry
def run(params, total_steps, logger=None, input_values=None):
    """Run an ExtremeFill2D simulation

    Args:
      params: a namedtuple of parameters, see `params.json` for more
        details
      elapsed_time: the current elapsed simulation time
      time_step_duration: the current dt
      total_steps: the total number of steps to run the simulation
      logger: a logger to log output details
      np_variables: the starting values of the variables

    Returns:
      the value of the variables after running the simulation

    """
    mesh = ExtremeFill2DMesh(params)

    variables = Variables(params, mesh)
    if input_values is not None:
        variables.distance[:] = input_values['distance']
        variables.cupric[:] = input_values['cupric']
        variables.suppressor[:] = input_values['suppressor']
        variables.potential[:] = input_values['potential']
        variables.theta[:] = input_values['theta']
        elapsed_time = input_values['elapsed_time']
        time_step_duration = input_values['time_step_duration']
    else:
        elapsed_time = 0.0
        time_step_duration = params.dt

    equations = get_equations(params, variables)
    advection = AdvectionEquation(params, variables)

    redo_timestep = False
    step = 0
    extension_global = max(variables.extension.globalValue)

    while step < total_steps:

        distance_old = update_old(variables.distance, equations)

        if step > 0 and extension_global < params.shutdown_deposition_rate:
            break

        if step % int(params.levelset_update_ncell / params.CFL) == 0:
            variables.distance.deleteIslands()
            variables.distance.calcDistanceFunction(order=1)

        time_step_duration = update_dt(time_step_duration,
                                       params,
                                       mesh,
                                       variables)

        advection.solve(time_step_duration)

        residuals = [sweep(time_step_duration, equations) for _ in range(params.sweeps)]

        extension_global = extend(variables.extension,
                                  variables.depositionRate,
                                  variables.distance)

        if time_step_duration > (params.CFL * mesh.nominal_dx / extension_global * 1.1):
            time_step_duration = revert_step(time_step_duration,
                                             equations,
                                             variables.distance,
                                             distance_old)
            if redo_timestep:
                break
            else:
                redo_timestep = True
            print("CFL number has been exceeded")
        else:
            elapsed_time += time_step_duration
            step += 1
            redo_timestep = False

        if logger is not None:
            logger.log(step, elapsed_time, time_step_duration, redo_timestep, residuals)

    return dict(distance=np.array(variables.distance),
                cupric=np.array(variables.cupric),
                suppressor=np.array(variables.suppressor),
                potential=np.array(variables.potential),
                theta=np.array(variables.theta),
                time_step_duration=time_step_duration,
                elapsed_time=elapsed_time)


def update_old(distance, equations):
    """Update old values
    """
    for eqn in equations:
        eqn.var.updateOld()
    return fp.numerix.array(distance).copy()

def get_equations(params, variables):
    """Create the equations
    """
    return (PotentialEquation(params, variables),
            CupricEquation(params, variables),
            SuppressorEquation(params, variables),
            ThetaEquation(params, variables))

def update_dt(time_step_duration, params, mesh, variables):
    """Update the time step
    """
    extension_global = extend(variables.extension, variables.depositionRate, variables.distance)
    time_step_duration = min(float(params.CFL * mesh.nominal_dx / extension_global),
                             time_step_duration * 1.1)
    time_step_duration = min(time_step_duration, params.dtMax)
    return max(time_step_duration, params.dtMin)

def extend(extension, deposition_rate, distance):
    """Calculate the extension velocity
    """
    extension[:] = deposition_rate
    distance.extendVariable(extension)
    return max(extension.globalValue)

def sweep(time_step_duration, equations):
    """Sweep the equations
    """
    OrderedDict([[eqn.var.name, eqn.sweep(time_step_duration)] for eqn in equations])

def revert_step(time_step_duration, equations, distance, distance_old):
    """Revert the time step.
    """
    time_step_duration = time_step_duration * 0.1
    for eqn in equations:
        eqn.var[:] = eqn.var.old
    distance[:] = distance_old
    return time_step_duration
