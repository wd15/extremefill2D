import os
import shutil
import imp
import sys

import tables
import tempfile


pa = imp.load_source('pa', sys.argv[1])

if pa.symmetry:
    from extremefill2D.simulation2D import Simulation2D as Simulation
else:
    from extremefill2D.simulation2DNoSymmetry import Simulation2DNoSymmetry as Simulation

if pa.annular:
    from extremefill2D.simulation2DAnnular import Simulation2DAnnular as Simulation
    kwargs = {'rinner' : pa.rinner, 'router' : pa.router, 'rboundary' : pa.rboundary}
else:
    kwargs = {}

datapath = os.path.join(tempfile.gettempdir(), 'data.h5')


simulation = Simulation()
simulation.run(view=False,
               totalSteps=pa.totalSteps,
               sweeps=pa.sweeps,
               dt=0.01,
               tol=pa.tol,
               Nx=pa.Nx,
               CFL=pa.CFL,
               PRINT=True,
               areaRatio=pa.areaRatio,
               dtMax=pa.dtMax,
               dataFile=datapath,
               totalTime=pa.totalTime,
               data_frequency=10,
               NxBase=1200,
               solver_tol=pa.solver_tol,
               kPlus=pa.kPlus,
               kMinus=pa.kMinus,
               featureDepth=pa.featureDepth,
               deltaRef=pa.deltaRef,
               appliedPotential=pa.appliedPotential,
               bulkSuppressor=pa.bulkSuppressor,
               **kwargs)


if not hasattr(pa, 'sumatra_label'):
    pa.sumatra_label = '.'


finaldir = os.path.join('Data', pa.sumatra_label)

shutil.move(datapath, finaldir)

