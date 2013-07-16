import os
import shutil
import imp
import sys


import tables
from extremefill2D.simulation2D import Simulation2D
import tempfile


pa = imp.load_source('pa', sys.argv[1])
datapath = os.path.join(tempfile.gettempdir(), 'data.h5')


simulation = Simulation2D()
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
               bulkSuppressor=pa.bulkSuppressor)


if not hasattr(pa, 'sumatra_label'):
    pa.sumatra_label = '.'


finaldir = os.path.join('Data', pa.sumatra_label)

shutil.move(datapath, finaldir)

