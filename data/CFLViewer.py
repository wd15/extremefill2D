import tables
from extremefill.dicttable import DictTable
import pylab
import numpy as np
from gitqsub import gitCloneToTemp, cleanTempRepo, gitMediaSync
import os


class BaseViewer(object):
    def getInterpolatedDistanceFunction(self, time, data):
        indexJump = 10

        if hasattr(data, 'index'):
            index = data.index
        else:
            index = indexJump

        latestIndex = data.getLatestIndex()
        indexJump = 10
        while index <= latestIndex and data[index]['elapsedTime'] < time:
            index += indexJump

        data.index = index - indexJump
            
        t0 = data[index - indexJump]['elapsedTime']
        t1 = data[index]['elapsedTime']

        alpha = (time - t0) / (t1 - t0)
        phi0 = data[index - indexJump]['distance']
        phi1 = data[index]['distance']
        return phi0 * (1 - alpha) + phi1 * alpha

    
class CFLViewer(BaseViewer):
    def __init__(self, times=None):
        self.times = times
        self.data = []

    def addBaseData(self, datafile):
        self.basedata = DictTable(datafile, 'r')
        
    def addData(self, datafile, label):
        data = DictTable(datafile, 'r')
        self.data.append(self.getNormData(data) + (label,))
    
    def plot(self):        
        for t, d, l in self.data:
            pylab.semilogy(t, d, label=l)

        pylab.ylabel(r'$\|\frac{\phi - \phi_0}{\Delta x}\|$', rotation='horizontal')
        pylab.xlabel(r'$t$ (s)')
        pylab.legend()
        pylab.savefig('CFLNorm2.png')

    def getNormData(self, data):
        norms = []
        dx = self.basedata[0]['dx']

        if hasattr(self.basedata, 'index'):
            del self.basedata.index
            
        for time in self.times:
            phiBase = self.getInterpolatedDistanceFunction(time, self.basedata)
            phi = self.getInterpolatedDistanceFunction(time, data)
            diff = abs(phi - phiBase) / dx
            diff[abs(phiBase) > 10 * dx] = 0.
            norm2 = np.sqrt(np.sum(diff**2))
            norms.append(norm2)

        return np.array(self.times), np.array(norms)

    
class ContourViewer(BaseViewer):
    def __init__(self, time, contours=(0,)):
        self.time = time
        self.contours = contours
        self.data = []
        
    def plot(self):
        for x, y, phi in self.data:
            pylab.contour(x, y, phi, self.contours, colors='black')
        pylab.savefig('contour.png')
        
    def addData(self, datafile):
        data = DictTable(datafile, 'r')
        data0 = data[0]
        dx = data0['dx']
        dy = data0['dy']
        nx = data0['nx']
        ny = data0['ny']
        import fipy as fp
        mesh = fp.Grid2D(nx=nx, ny=ny, dx=dx, dy=dy)
        shape = (ny, nx)
        x = np.reshape(mesh.x.value, shape)
        y = np.reshape(mesh.y.value, shape)
        phi = self.getInterpolatedDistanceFunction(self.time, data)
        phi = np.reshape(phi, shape)
        self.data.append((x, y, phi))

        
def plotCFL():
    branches = ('CFL0.025', 'CFL0.05', 'CFL0.1', 'CFL0.2', 'CFL0.4', 'CFL0.8')
    # branches = ('CFL0.025', 'CFL0.2', 'CFL0.4')
    datafile = os.path.join('data', 'data.h5')
    Npoints = 10
    end_time = 4000.
    cwd = os.getcwd()
    times = np.arange(Npoints + 1)[1:] * end_time / Npoints
    viewer = CFLViewer(times=times)
    for count, branch in enumerate(branches):
        print 'branch',branch
        tempdir = gitCloneToTemp(branch=branch, repositoryPath='ssh://wd15@genie.nist.gov/users/wd15/git/extremefill')
        repopath = os.path.join(tempdir, 'extremefill')
        datapath = os.path.join(repopath, datafile)
        gitMediaSync()
        if count == 0:
            viewer.addBaseData(datapath)
            basetempdir = tempdir
        else:
            viewer.addData(datapath, branch)
            cleanTempRepo(tempdir)            
    cleanTempRepo(basetempdir)
    os.chdir(cwd)
    viewer.plot()

def plotContour():
    branches = ('CFL0.025', 'CFL0.05', 'CFL0.1', 'CFL0.2', 'CFL0.4', 'CFL0.8')
    branches = ('CFL0.025', 'CFL0.05')
    datafile = os.path.join('data', 'data.h5')
    cwd = os.getcwd()
    viewer = ContourViewer(3000., (-1e-5, -0.5e-5, 0, 0.5e-5, 1e-5))
    for count, branch in enumerate(branches):
        tempdir = gitCloneToTemp(branch=branch, repositoryPath='ssh://wd15@genie.nist.gov/users/wd15/git/extremefill', verbose=True)
        gitMediaSync()
        viewer.addData(datafile)
        
        cleanTempRepo(tempdir)
        
    os.chdir(cwd)
    viewer.plot()
        
if __name__ == '__main__':
    # from profiler import Profiler
    # from profiler import calibrate_profiler
    # fudge = calibrate_profiler(10000)
    # profile = Profiler('profile', fudge=fudge)
    plotCFL()
    # profile.stop()

