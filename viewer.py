import os


import tables
from extremefill.dicttable import DictTable
import pylab
import numpy as np
from sumatra.projects import load_project


class BaseViewer(object):
    def __init__(self, basedatafile=None, datafiles=None, labels=None, times=None):
        self.times = times
        self.data = []
        self.addBaseData(basedatafile)
        if labels is None:
            labels = [''] * len(datafiles)
        for datafile, label in zip(datafiles, labels):
            print 'datafile',datafile
            self.addData(datafile, label)

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
    
    def plot(self, filename=None, filedir=None):
        raise NotImplementedError

class NormViewer(BaseViewer):
    def addBaseData(self, datafile):
        self.basedata = DictTable(datafile, 'r')
        
    def addData(self, datafile, label):
        data = DictTable(datafile, 'r')
        self.data.append(self.__getNormData(data) + (label,))
    
    def plot(self, filename='Norm2.png', filedir='png'):        
        for t, d, l in self.data:
            pylab.semilogy(t, d, label=l)

        pylab.ylabel(r'$\|\frac{\phi - \phi_0}{\Delta x}\|$', rotation='horizontal')
        pylab.xlabel(r'$t$ (s)')
        pylab.legend()
        pylab.savefig(os.path.join(filedir, filename))

    def __getNormData(self, data):
        norms = []
        dx = self.basedata[0]['dx']

        if hasattr(self.basedata, 'index'):
            del self.basedata.index
            
        for time in self.times:
            phiBase = self.getInterpolatedDistanceFunction(time, self.basedata)
            phi = self.getInterpolatedDistanceFunction(time, data)
            phiInt = self.__interpolateToBase(self.basedata, data, phi)
            diff = abs(phiInt - phiBase) / dx
            diff[abs(phiBase) > 10 * dx] = 0.
            norm2 = np.sqrt(np.sum(diff**2) / len(diff))
            norms.append(norm2)

        return np.array(self.times), np.array(norms)

    def __interpolateToBase(self, basedata, data, phi):
        baseGrid = self.getGrid(basedata)
        grid = self.getGrid(data)
        import fipy as fp
        return np.array(fp.CellVariable(mesh=grid, value=phi)(baseGrid.cellCenters, order=1))
    
    
class _ContourViewer(BaseViewer):
    def __init__(self, basedatafile=None, datafiles=None, labels=None, times=None, contours=(0,)):
        self.contours = contours
        super(_ContourViewer, self).__init__(basedatafile=basedatafile, datafiles=datafiles, labels=labels, times=times)
        
    def plot(self, filename=None):
        import matplotlib.pyplot as plt
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_aspect(1.)
        for x, y, phi in self.data:
            pylab.contour(x, y, phi, self.contours, colors='k', extent=(0, 1e-4, 0, 1e-5))
        pylab.xlim(1e-5, 7.5e-5)
        pylab.ylim(0, 8e-6)
        if filename:
            pylab.savefig(filename)
        pylab.show()
            
        
        
    def addData(self, datafile, label):
        for time in self.times:
            self.__addDataAtTime(datafile, time)

    def addBaseData(self, datafile):
        self.addData(datafile, None)
            
    def __addDataAtTime(self, datafile, time):
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


class CFLNormViewer(NormViewer):
    def __init__(self):    
        records = Records().by_tag('CFL').by_tag('production')
        basedatafile = records.by_parameter('CFL', 0.01).datafiles[0]
        records = records.by_parameter('CFL', (0.02, 0.04, 0.08, 0.16, 0.32, 0.64))

        labels = ["CFL=%1.1e" % record.parameters['CFL'] for record in records]        
        
        Npoints = 10
        end_time = 4000.
        times = np.arange(Npoints + 1)[1:] * end_time / Npoints

        super(CFLNormViewer, self).__init__(basedatafile=basedatafile,
                                            datafiles=records.datafiles,
                                            labels=labels,
                                            times=times)

class ContourViewer(_ContourViewer):
    def __init__(self, baseRecord, records, times=(0., 1000., 2000., 3000., 4000.)):
        super(ContourViewer, self).__init__(basedatafile=baseRecord.datafiles[0],
                                               datafiles=records.datafiles,
                                               labels=None,
                                               times=times)


class Records:
    def __init__(self, records=None):
        if records is None:
            project = load_project()
            self.records = project.record_store.list(project.name)
        else:
            self.records = records
        
    def by_tag(self, tag):
        return self.getRecords(lambda r: tag in r.tags)

    def by_parameter(self, parameter, values):
        try:
            values = list(values)
        except TypeError:
            values = [values]
        return self.getRecords(lambda r: r.parameters[parameter] in values)

    def getRecords(self, func):
        records = []
        for r in self:
            if func(r):
                records += [r]
        return Records(records)

    @property
    def datafiles(self):
        datafiles = []
        for r in self:
            datafiles += [os.path.join(r.datastore.root, r.output_data[0].path)]
        return datafiles

    def __len__(self):
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    def __getitem__(self, index):
        return self.records[index]
        
if __name__ == '__main__':
    # for v in (0.02, 0.04, 0.08, 0.16):
    #     CFLContourViewer(v).plot('contour%1.2f.png' % v) 
    records = Records().by_tag('CFL').by_tag('production')
    baseRecord = records.by_parameter('CFL', 0.01)
    otherRecord = records.by_parameter('CFL', 0.02)
    print baseRecord
    print otherRecord
    v = ContourViewer(baseRecord, otherRecord)
    v.plot()
    # profile.stop()
    # print len(Records().by_tag('CFL').by_tag('production').by_parameter('CFL', 0.08))
