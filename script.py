import os


import tables
from extremefill.simulation2D import Simulation2D


simulation = Simulation2D()

def run(totalSteps=10,
        Nx=300,
        CFL=0.1,
        datadir=os.path.split(__file__)[0]):
    
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


from smt import SMTSimulation

smtsim = SMTSimulation(run, kwargs={'totalSteps' : 1}, tags=('test',), reason="testing SMT class", main_file=__file__)
smtsim.launch()
