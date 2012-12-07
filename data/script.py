from extremefill.simulation2D import Simulation2D

def run(CFL=0.2, Nx=300):
    simulation = Simulation2D()
    simulation.run(view=False,
                   totalSteps=11,
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
                   data_frequency=10)

    return 'data.h5'

if __name__ == '__main__':
    from gitqsub import qsubmit
    for CFL in (0.025, 0.05, 0.1, 0.2, 0.4, 0.8):
        qsubmit(callBack=run, newbranch='CFL' + str(CFL), CFL=CFL)

    for Nx in (150, 300, 600, 1200):
        qsubmit(callBack=run, newbranch='Nx' + str(Nx), Nx=Nx)
