from extremefill.dicttable import DictTable
import pylab
import numpy as np

class BaseViewer(object):
    def getInterpolatedDistanceFunction(self, time, data):
        if hasattr(data, 'index'):
            index = data.index
        else:
            index = 10

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
            print 'time',time
            phiBase = self.getInterpolatedDistanceFunction(time, basedata)
            phi = self.getInterpolatedDistanceFunction(time, data)
            diff = abs(phi - phiBase) / dx
            diff[abs(phiBase) > 10 * dx] = 0.
            norm2 = np.sqrt(np.sum(diff**2))
            norms.append(norm2)

        return np.array(self.times), np.array(norms)

class ContourViewer(BaseViewer):
    def __init__(self, time, h5nodes, contours=(0,), datafile='data.h5'):
        self.time = time
        self.h5nodes = h5nodes
        self.contours = contours
        self.datafile = datafile

    def plot(self):
        data = DictTable(self.datafile, 'r')
        for node in self.h5nodes:
            self._plot(data)
        pylab.show()
        
    def _plot(self, data):
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
        pylab.contour(x, y, phi, self.contours, colors='black')
        pylab.savefig('contour.png')
        
if __name__ == '__main__':
    h5nodes = ('CFL-25', 'CFL-50', 'CFL-100', 'CFL-200', 'CFL-400')
    ContourViewer(3000., h5nodes, (-1e-5, -0.5e-5, 0, 0.5e-5, 1e-5)).plot()
    # Npoints = 10
    # viewer = CFLViewer(datafiles=datafiles, times=np.arange(Npoints) * 4000. / (Npoints - 1))
    # viewer.plot()    ##   
 
