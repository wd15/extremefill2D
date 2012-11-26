from extremefill.dicttable import DictTable
import pylab
import numpy as np

class BaseViewer(object):
    def getInterpolatedDistanceFunction(self, time, data):
        if hasattr(data, 'index'):
            index = data.index
        else:
            index = 1
        latestIndex = data.getLatestIndex()
        while index <= latestIndex and data[index]['elapsedTime'] < time:
            index += 1
        data.index = index - 1
            
        t0 = data[index - 1]['elapsedTime']
        t1 = data[index]['elapsedTime']
        alpha = (time - t0) / (t1 - t0)
        phi0 = data[index - 1]['distance']
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
            pylab.plot(t, d, label=datafile[7:-3])
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
            diff = abs(phi - phiBase) / dx
            diff[abs(phiBase) > 10 * dx] = 0.
            norm2 = np.sqrt(np.sum(diff**2))
            norms.append(norm2)

        return np.array(self.times), np.array(norms)

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
        
if __name__ == '__main__':
    ##    from profiler import calibrate_profiler
    ##    from profiler import Profiler
    ##    fudge = calibrate_profiler(10000)
    ##    profile = Profiler('profile', fudge=fudge)
    import os
    datafiles = []
    for datafile in ('cfl0.025.h5', 'cfl0.05.h5', 'cfl0.1.h5', 'cfl0.2.h5', 'cfl0.4.h5'):
        datafiles += [os.path.join(os.path.split(__file__)[0], datafile)]

    # ContourViewer(4000., datafiles, (-1e-5, -0.5e-5, 0, 0.5e-5, 1e-5)).plot()
    Npoints = 10
    viewer = CFLViewer(datafiles=datafiles, times=np.arange(Npoints) * 4000. / (Npoints - 1))
    viewer.plot()
    ##    profile.stop()
