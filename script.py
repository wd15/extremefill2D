import os
import shutil


import tables
from extremefill.simulation2D import Simulation2D
from sumatra.smtdecorator import SMTDecorator
import tempfile

@SMTDecorator
def run(totalSteps=10,
        Nx=300,
        CFL=0.1,
        datadir=os.path.split(__file__)[0]):
    
    final_datadir = datadir
    datadir = tempfile.gettempdir()
    datapath = os.path.join(datadir, 'data.h5')

    simulation = Simulation2D()
    simulation.run(view=False,
                   totalSteps=totalSteps,
                   sweeps=30,
                   dt=0.01,
                   tol=1e-1,
                   Nx=Nx,
                   CFL=CFL,
                   PRINT=True,
                   areaRatio=2 * 0.093,
                   dtMax=100.,
                   dataFile=datapath,
                   totalTime=5000.,
                   data_frequency=10,
                   NxBase=1200)

    shutil.move(datapath, final_datadir)

if __name__ == '__main__':
    run(totalSteps=2, CFL=0.1, Nx=300)

