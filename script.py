import tables
from extremefill.simulation2D import Simulation2D


simulation = Simulation2D()

def run(totalSteps=10,
        Nx=300,
        CFL=0.1,
        dataFile='data.h5'):

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
                   dataFile='data.h5',
                   totalTime=5000.,
                   data_frequency=10,
                   NxBase=1200)


from smt import SMTSimulation

SMTSimulation(run, kwargs={'totalSteps' : 1}, tags=('test',), reason="testing decorator", main_file=__file__)

