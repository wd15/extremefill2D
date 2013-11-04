import os
import tables
import fipy as fp
import numpy as np
from scipy.interpolate import interp1d


def find_all_zeros(f, x0, x1, N=1000):
    x = np.linspace(x0, x1, N)
    y = f(x)
    sign = y[1:] * y[:-1]
    mask = sign < 0
    IDs = np.array(np.nonzero(mask)).flatten()
    from scipy.optimize import brentq
    return np.array([brentq(f, x[ID], x[ID + 1]) for ID in IDs])

class FeatureProperty(object):
    def __init__(self, record):
        self.record = record
        datafile = os.path.join(self.record.datastore.root, self.record.output_data[0].path)
        self.h5file = tables.openFile(datafile, mode='r')

    def __del__(self):
        self.close()

    def close(self):
        self.h5file.close()

    def getLatestIndex(self):
        return self.h5file.root._v_attrs.latestIndex

    def getZeros(self, index=None):
        if not index:
            index = self.getLatestIndex()

        data = self.h5file.getNode('/ID' + str(int(index)))

        mindx = min(data.dx.read())
        featureDepth = self.record.parameters['featureDepth']
        distanceBelowTrench = 10 * mindx

        if not hasattr(self, 'mesh'):
            self.mesh = fp.Grid2D(nx=data.nx.read(), ny=data.ny.read(), dx=data.dx.read(), dy=data.dy.read()) - [[-mindx / 100.], [distanceBelowTrench + featureDepth]]
        phi = fp.CellVariable(mesh=self.mesh, value=data.distance.read())

        N = 1000
        rinner = self.record.parameters['rinner']
        router = self.record.parameters['router']
        X = (rinner + router) / 2. * np.ones(N)
        Y = np.linspace(-featureDepth, 10e-6, 1000)
        points = (X, Y)
        if not hasattr(self, 'nearestCellIDs'):
            self.nearestCellIDs = self.mesh._getNearestCellID(points)
        phiInterpolated = phi(points, order=1, nearestCellIDs=self.nearestCellIDs)

        f = interp1d(Y, phiInterpolated)
        zeros = find_all_zeros(f, Y[0], Y[-1])

        return zeros
    
    def getVoidSize(self, index=None):
        zeros = self.getZeros(index)
        featureDepth = self.record.parameters['featureDepth']
        if len(zeros) < 2:
            void_size = 0.
        else:
            void_size = max((zeros[1:] - zeros[:-1])[::2]) / featureDepth
            if void_size > 1:
                void_size = 1.

        return void_size

    def getHeight(self, index=None):
        zeros = self.getZeros(index)
        featureDepth = self.record.parameters['featureDepth']
        if len(zeros) % 2 == 0:
            height = 1.
        else:
            height = (featureDepth + zeros[-1]) / featureDepth 
            height = min(height, 1.)
        return height

    def getTime(self, index=None):
        if index is None:
            index = self.getLatestIndex()
        data = self.h5file.getNode('/ID' + str(int(index)))
        return float(data.elapsedTime.read())

    def getPotential(self, index=None):
        if not index:
            index = self.getLatestIndex()
        data = self.h5file.getNode('/ID' + str(int(index)))

        mindx = min(data.dx.read())
        featureDepth = self.record.parameters['featureDepth']
        distanceBelowTrench = 10 * mindx

        if not hasattr(self, 'mesh'):
            self.mesh = fp.Grid2D(nx=data.nx.read(), ny=data.ny.read(), dx=data.dx.read(), dy=data.dy.read()) - [[-mindx / 100.], [distanceBelowTrench + featureDepth]]
        potential = fp.CellVariable(mesh=self.mesh, value=data.potential.read())

        rinner = self.record.parameters['rinner']
        router = self.record.parameters['router']
        X = (rinner + router) / 2.
        Y = 0.0
        point = ((X,), (Y,))
        if not hasattr(self, 'nearestCellIDsPotential'):
            self.nearestCellIDsPotential = self.mesh._getNearestCellID(point)
        monitorValue = potential(point, order=1, nearestCellIDs=self.nearestCellIDsPotential)

        return float(monitorValue[0])

    def getTheta(self, index=None):
        if not index:
            index = self.getLatestIndex()
        data = self.h5file.getNode('/ID' + str(int(index)))

        mindx = min(data.dx.read())
        featureDepth = self.record.parameters['featureDepth']
        distanceBelowTrench = 10 * mindx

        if not hasattr(self, 'mesh'):
            self.mesh = fp.Grid2D(nx=data.nx.read(), ny=data.ny.read(), dx=data.dx.read(), dy=data.dy.read()) - [[-mindx / 100.], [distanceBelowTrench + featureDepth]]
        theta = fp.CellVariable(mesh=self.mesh, value=data.interfaceTheta.read())

        rinner = self.record.parameters['rinner']
        router = self.record.parameters['router']
        N = 1000
        X = np.ones(N) * (rinner + router) / 2.
        Y = np.linspace(-distanceBelowTrench - featureDepth, featureDepth / 5., N)
        points = (X, Y)
        if not hasattr(self, 'nearestCellIDsTheta'):
            self.nearestCellIDsTheta = self.mesh._getNearestCellID(points)
        values = theta(points, order=0, nearestCellIDs=self.nearestCellIDsTheta)
        return float(max(values))
