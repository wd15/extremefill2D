import os
import shutil


import tables
from extremefill2D.simulation2D import Simulation2D
from sumatra.smtdecorator import SMTDecorator
import tempfile

@SMTDecorator
def run(totalSteps=10,
        Nx=300,
        CFL=0.1,
        sweeps=30,
        tol=1e-1,
        solver_tol=1e-10,
        areaRatio=2 * 0.093,
        kPlus=150.,
        kMinus=2.45e7,
        featureDepth=56e-6,
        deltaRef=0.03,
        dtMax=100.,
        totalTime=5000.,
        datadir=os.path.split(__file__)[0],
        appliedPotential=-0.25):
    
    final_datadir = datadir
    datadir = tempfile.gettempdir()
    datapath = os.path.join(datadir, 'data.h5')

    simulation = Simulation2D()
    simulation.run(view=False,
                   totalSteps=totalSteps,
                   sweeps=sweeps,
                   dt=0.01,
                   tol=tol,
                   Nx=Nx,
                   CFL=CFL,
                   PRINT=True,
                   areaRatio=areaRatio,
                   dtMax=dtMax,
                   dataFile=datapath,
                   totalTime=totalTime,
                   data_frequency=10,
                   NxBase=1200,
                   solver_tol=solver_tol,
                   kPlus=kPlus,
                   kMinus=kMinus,
                   featureDepth=featureDepth,
                   deltaRef=deltaRef,
                   appliedPotential=appliedPotential)

    shutil.move(datapath, final_datadir)

if __name__ == '__main__':
    run(totalSteps=2,
        CFL=0.1,
        Nx=300,
        tol=1e-1,
        sweeps=30,
        solver_tol=1e-10,
        areaRatio=2 * 0.093,
        kPlus=150.,
        kMinus=2.45e7,
        featureDepth=56e-6,
        deltaRef=0.03,
        dtMax=100.,
        totalTime=5000.,
        appliedPotential=-0.25)

