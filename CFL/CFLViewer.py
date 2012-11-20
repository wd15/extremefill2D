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
    def __init__(self, datafiles, basedatafile):
        self.datafiles = datafiles
        self.basedatafile = basedatafile

    def plot(self):
        times, normdata = self.getNormData() 
        for index in xrange(len(normdata[0])):
            pylab.plot(times, normdata[:, index])
        pylab.show()
        
    def getNormData(self):
        basedata = DictTable(self.basedatafile, 'r')
        norms = []
        times = []
        latestIndex = basedata.getLatestIndex()
        datas = [DictTable(datafile, 'r') for datafile in self.datafiles]
        
        for index in xrange(0, latestIndex, 30):
            print index
            elapsedTime = basedata[index]['elapsedTime']
            phiBase = basedata[index]['distance']
            norms0 = []
            for data in datas:
                norm = self.getNorm(data, elapsedTime, phiBase)
                norms0.append(norm)
            norms.append(norms0)
            times.append(elapsedTime)

        return np.array(times), np.array(norms)

    def getNorm(self, data, elapsedTime, phiBase):
        phi = self.getInterpolatedDistanceFunction(elapsedTime, data)
        dx = data[0]['dx']
        diff = abs(phi - phiBase) / dx
        diff[abs(phiBase) > 4 * dx] = 0.
        
        return max(diff)
    
#     if elapsedTime > 1000:
#         ID = np.argmax(abs(phi - phiBase))
#         diff = abs(phi - phiBase)
#         diff[abs(phiBase) > 2 * dx] = 0.
#         print 'diff max',max(diff) / dx
#         print 'max(abs(phi - phiBase)) / dx',max(abs(phi - phiBase)) / dx
#         print 'elapsedTime',elapsedTime
#         print 't0',t0,'t1',t1
#         print 'phi[ID]',phi[ID]
#         print 'phiBase[ID]',phiBase[ID]
#         print 'phi0[ID]',phi0[ID]
#         print 'phi1[ID]',phi1[ID]
#         print 'dx',dx
#         print "ID",ID
#         raw_input('stopped')
#     return max(abs(phi - phiBase)) / dx
# #    return np.sum((phi - phiBase)**2)


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
    for datafile in ('cfl0.05.h5', 'cfl0.1.h5', 'cfl0.2.h5'):
        datafiles += [os.path.join(os.path.split(__file__)[0], datafile)]

    ContourViewer(4000., datafiles, (-1e-5, 0, 1e-5)).plot()
    # viewer = CFLViewer(basedatafile=datafiles[0], datafiles=datafiles[1:])
    # viewer.plot()
    ##    profile.stop()
