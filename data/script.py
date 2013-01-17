import tables
from extremefill.simulation2D import Simulation2D

def run(CFL=0.2, Nx=300, NxBase=2400, totalTime=5000., totalSteps=10000000000000):
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
                   totalTime=totalTime,
                   data_frequency=10,
                   NxBase=NxBase)

    return 'data.h5'

if __name__ == '__main__':
    from gitqsub import qsubmit
    # for CFL in (0.0125, 1.6):
    #     qsubmit(callBack=run, verbose=True, newbranch='CFL' + str(CFL), CFL=CFL)
    for Nx in (150, 300, 600, 1200):
        qsubmit(callBack=run, verbose=True, newbranch='Nx' + str(Nx), CFL=0.2, Nx=Nx)

