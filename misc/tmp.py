from extremefill.simulation2D import Simulation2D

simulation = Simulation2D()
simulation.run(view=True, totalSteps=10, sweeps=30, dt=0.01, tol=1e-1, Nx=300, CFL=0.2, PRINT=True, areaRatio=2 * 0.093, dtMax=100., dataFile='cfl0.2.h5')




