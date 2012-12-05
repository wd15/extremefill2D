from extremefill.dicttable import DictTable
import pylab
import numpy as np
import fipy as fp


class BaseViewer(object):

    def getInterpolatedDistanceFunction(self, time, data):
        indexJump = 10

        if hasattr(data, 'index'):
            index = data.index
        else:
            index = indexJump

        latestIndex = data.getLatestIndex()
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
        return fp.Grid2D(nx=data[0]['nx'], ny=data[0]['ny'], dx=data[0]['dx'], dy=data[0]['dy']) 


class CFLViewer(BaseViewer):

    def __init__(self, datafiles, times=None):
        self.datafiles = datafiles
        self.times = times

    def plot(self):
        for datafile in self.datafiles[1:]:
            data = DictTable(datafile, 'r')
            t, d = self.getNormData(data)
            pylab.plot(t, d, label=datafile[:-3])
        pylab.ylabel(r'$\|\frac{\phi - \phi_0}{\Delta x}\|$', rotation='horizontal')
        pylab.xlabel(r'$t$ (s)')
        pylab.legend()
        pylab.savefig('CFLNorm2.png')
        pylab.show()

    def getNormData(self, data):
        basedata = DictTable(self.datafiles[0], 'r')
        norms = []
        dx = basedata[0]['dx']
        for time in self.times:
            phiBase = self.getInterpolatedDistanceFunction(time, basedata)
            phi = self.getInterpolatedDistanceFunction(time, data)
            phiInt = self.interpolateToBase(basedata, data, phi)
            diff = abs(phiInt - phiBase) / dx
            mask = abs(phiBase) > 10 * dx
            diff[mask] = 0.
            norm2 = np.sqrt(np.sum(diff**2) / np.sum(~mask))
            norms.append(norm2)

        return np.array(self.times), np.array(norms)

    def interpolateToBase(self, basedata, data, phi):
        baseGrid = self.getGrid(basedata)
        grid = self.getGrid(data)
        return np.array(fp.CellVariable(mesh=grid, value=phi)(baseGrid.cellCenters, order=1))
        

class ContourViewer(BaseViewer):

    def __init__(self, time, datafiles, contours=(0,)):
        self.time = time
        self.datafiles = datafiles
        self.contours = contours

    def plot(self):
        for datafile in self.datafiles:
            self._plot(datafile)
        pylab.show()
        
    def _plot(self, datafile):
        data = DictTable(datafile, 'r')
        mesh = self.getGrid(data)
        shape = mesh.shape[::-1]
        x = np.reshape(mesh.x.value, shape)
        y = np.reshape(mesh.y.value, shape)
        phi = self.getInterpolatedDistanceFunction(self.time, data)
        phi = np.reshape(phi, shape)
        pylab.contour(x, y, phi, self.contours, colors='black')
        pylab.savefig('contour.png')

if __name__ == '__main__':
    datafiles = ('CFL400Nx1200.h5', 'CFL400Nx600.h5', 'CFL400Nx300.h5', 'CFL400Nx150.h5')

    
    ## contour plot
    ContourViewer(40.404, datafiles, (-1e-5, -0.5e-5, 0, 0.5e-5, 1e-5)).plot()

    ## Norm 2 plot
    Npoints = 100
    viewer = CFLViewer(datafiles=datafiles, times=np.arange(Npoints) * 4000. / (Npoints - 1))
    viewer.plot()  
