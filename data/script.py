from extremefill.simulation2D import Simulation2D

def run(CFL=0.4):
    simulation = Simulation2D()
    simulation.run(view=False,
                   totalSteps=3,
                   sweeps=30,
                   dt=0.01,
                   tol=1e-1,
                   Nx=300,
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
    qsubmit(callBack=run, newbranch='CFL0.2', CFL=0.2)
