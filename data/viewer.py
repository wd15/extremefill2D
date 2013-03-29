import tables
from extremefill.dicttable import DictTable
import pylab
import numpy as np
from gitqsub import gitCloneToTemp, cleanTempRepo, gitMediaSync
import os


class BaseViewer(object):
    def __init__(self, branches=None, datafile=None, datafiles=None):
        if datafiles is None:
            self.datafilesFromBranches(branches, datafile)
        else:
            for count, datafile in enumerate(datafiles):
                print 'datafile',datafile
                if count == 0:
                    self.addBaseData(datafile)
                else:
                    self.addData(datafile, datafile)

    def datafilesFromBranches(self, branches, datafile):
        cwd = os.getcwd()
        for count, branch in enumerate(branches):
            print 'branch',branch
            tempdir = gitCloneToTemp(branch=branch, repositoryPath='ssh://wd15@genie.nist.gov/users/wd15/git/extremefill')
            repopath = os.path.join(tempdir, 'extremefill')
            datapath = os.path.join(repopath, datafile)
            gitMediaSync()
            if count == 0:
                self.addBaseData(datapath)
                basetempdir = tempdir
            else:
                self.addData(datapath, branch)
                cleanTempRepo(tempdir)   

        cleanTempRepo(basetempdir)
        os.chdir(cwd)
        
    def addBaseData(self, datapath):
        raise NotImplementedError

    def addData(self, datapath, branch):
        raise NotImplementedError
    
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

    def getGrid(self, data):
        import fipy as fp
        return fp.Grid2D(nx=data[0]['nx'], ny=data[0]['ny'], dx=data[0]['dx'], dy=data[0]['dy'])
    
class NormViewer(BaseViewer):
    def __init__(self, times=None, branches=None, datafile=None):
        self.times = times
        self.data = []
        super(NormViewer, self).__init__(branches, datafile)

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
        pylab.savefig('Norm2.png')
        pylab.show()

    def getNormData(self, data):
        norms = []
        dx = self.basedata[0]['dx']

        if hasattr(self.basedata, 'index'):
            del self.basedata.index
            
        for time in self.times:
            phiBase = self.getInterpolatedDistanceFunction(time, self.basedata)
            phi = self.getInterpolatedDistanceFunction(time, data)
            phiInt = self.interpolateToBase(self.basedata, data, phi)
            diff = abs(phiInt - phiBase) / dx
            diff[abs(phiBase) > 10 * dx] = 0.
            norm2 = np.sqrt(np.sum(diff**2) / len(diff))
            norms.append(norm2)

        return np.array(self.times), np.array(norms)

    def interpolateToBase(self, basedata, data, phi):
        baseGrid = self.getGrid(basedata)
        grid = self.getGrid(data)
        import fipy as fp
        return np.array(fp.CellVariable(mesh=grid, value=phi)(baseGrid.cellCenters, order=1))
    
    
class ContourViewer(BaseViewer):
    def __init__(self, times, contours=(0,), branches=None, datafile=None, datafiles=None):
        self.times = times
        self.contours = contours
        self.data = []
        super(ContourViewer, self).__init__(branches=branches, datafile=datafiles, datafiles=datafiles)
        
    def plot(self):
        import matplotlib.pyplot as plt
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_aspect(1.)
        for x, y, phi in self.data:
            pylab.contour(x, y, phi, self.contours, colors='black', extent=(0, 1e-4, 0, 1e-5))
        pylab.xlim(1e-5, 7.5e-5)
        pylab.ylim(0, 8e-6)
        pylab.savefig('contour.png')
        
    def addData(self, datafile, label):
        for time in self.times:
            self.addDataAtTime(datafile, time)

    def addBaseData(self, datafile):
        self.addData(datafile, None)
            
    def addDataAtTime(self, datafile, time):
        data = DictTable(datafile, 'r')
        mesh = self.getGrid(data)
        shape = (mesh.ny, mesh.nx)
        x = np.reshape(mesh.x.value, shape)
        y = np.reshape(mesh.y.value, shape)
        phi = self.getInterpolatedDistanceFunction(time, data)
        phi = np.reshape(phi, shape)
        self.data.append((x, y, phi))

def plotNx():
    branches = ('Nx600', 'Nx300', 'Nx150')
    datafile = os.path.join('data', 'data.h5')
    Npoints = 10
    end_time = 4000.
    times = np.arange(Npoints + 1)[1:] * end_time / Npoints
    viewer = NormViewer(times=times, branches=branches, datafile=datafile)
    viewer.plot()
        
def plotCFL():
    # branches = ('CFL0.0125', 'CFL0.025', 'CFL0.05', 'CFL0.1', 'CFL0.2', 'CFL0.4', 'CFL0.8', 'CFL1.6')
    # branches = ('CFL0.0125', 'CFL0.025', 'CFL0.05', 'CFL0.1', 'CFL0.2', 'CFL0.4', 'CFL0.8', 'CFL1.6')
    branches = ('CFL0.2', 'CFL0.4')
    datafile = os.path.join('data', 'data.h5')
    Npoints = 10
    end_time = 4000.
    times = np.arange(Npoints + 1)[1:] * end_time / Npoints
    viewer = NormViewer(times=times, branches=branches, datafile=datafile)
    viewer.plot()

def plotContour():
    # branches = ('CFL0.0125', 'CFL0.025', 'CFL0.05', 'CFL0.1', 'CFL0.2', 'CFL0.4', 'CFL0.8', 'CFL1.6')
    branches = ('Nx600', 'Nx150')
    #    branches = ('CFL0.025', 'CFL0.05')
    datafile = os.path.join('data', 'data.h5')
    times = (0,)
    # times = (0., 1000., 2000., 3000., 4000.)
    #    viewer = ContourViewer(times=times, branches=branches, datafile=datafile)
    viewer = ContourViewer(times=times, branches=branches, datafile=datafile, datafiles=('data150.h5', 'data600.h5'))
    viewer.plot()
        
if __name__ == '__main__':
    # from profiler import Profiler
    # from profiler import calibrate_profiler
    # fudge = calibrate_profiler(10000)
    # profile = Profiler('profile', fudge=fudge)
    plotCFL()
    # profile.stop()

