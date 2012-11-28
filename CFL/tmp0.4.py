from extremefill.simulation2D import Simulation2D
import tempfile
import os

simulation = Simulation2D()
(f, datafile) = tempfile.mkstemp(suffix='.h5')
os.close(f)

simulation.run(view=False, totalSteps=5, sweeps=30, dt=0.01, tol=1e-1, Nx=300, CFL=0.4, PRINT=True, areaRatio=2 * 0.093, dtMax=100., dataFile=datafile, totalTime=5000., Nnarrow=100000000000)

tail, head = os.path.split(datafile)
tail, tmp = os.path.split(__file__)
print 'datafile',datafile
print 'os.path.join(tail, head)', 
os.rename(datafile, os.path.join(tail, head))





