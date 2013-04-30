import os.path


import tables
import fipy as fp
import matplotlib.pyplot as plt
import numpy as np
from smtext import getSMTRecords
from extremefill2D.dicttable import DictTable


class _BaseViewer(object):
    def plot(self, indices=[0], filename=None):
        self.plotSetup(indices=indices)
        self.plotSave(filename)

    def plotSetup(self, indices=[0]):
        raise NotImplementedError

    def plotSave(self, filename):
        if filename:
            plt.savefig(filename)
        else:
            plt.show()


class _BaseSingleViewer(_BaseViewer):
    def __init__(self, tags=[], parameters={}, ax=None):
        self.data = self.getData(tags, parameters)
        data0 = self.data[0]
        mesh = fp.Grid2D(nx=data0['nx'], ny=data0['ny'], dx=data0['dx'], dy=data0['dy'])
        self.shape = (mesh.ny, mesh.nx)
        self.x = mesh.x.value
        self.y = mesh.y.value
        if ax is None:
            fig = plt.figure()
            self.ax = fig.add_subplot(111)
        else:
            self.ax = ax

    def getData(self, tags, parameters):
        records = getSMTRecords(tags, parameters)
        record = records[0]
        self.record = record
        datafile = os.path.join(record.datastore.root, record.output_data[0].path)
        return DictTable(datafile, 'r')

    def flip(self, a, scale, negate=False):
        a = np.reshape(a, self.shape)
        a = a.swapaxes(0,1)
        return np.concatenate((-(2 * negate -1) * a[:,::-1], a), axis=1) * scale

    def plotSetup(self, indices=[0]):
        if type(indices) is int:
            indices = [indices]
        
        delta = 150e-6
        featureDepth = 56e-6
        y0 = delta * 0.1 + featureDepth

        scale = 1e+6
        y0 = y0 * scale
        ymin = 1e-5 * scale - y0
        ymax = 7.5e-5 * scale - y0

        y = self.flip(self.x, scale) - y0

        self._plot(y, scale, indices)

        self.ax.set_ylim(ymin, ymax)
        self.ax.set_ylabel(r'$y$ ($\micro\metre$)')

    def _plot(self, y, scale, indices):
        raise NotImplementedError


