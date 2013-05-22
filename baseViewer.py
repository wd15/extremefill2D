import os.path


import tables
import fipy as fp
import matplotlib.pyplot as plt
import numpy as np
from extremefill2D.dicttable import DictTable


class _BaseViewer(object):
    def plot(self, indices=[0], filename=None, times=None):
        self.plotSetup(indices=indices, times=times)
        self.plotSave(filename)

    def plotSetup(self, indices=[0]):
        raise NotImplementedError

    def plotSave(self, filename):
        if filename:
            plt.savefig(filename)
        else:
            plt.show()



class _BaseSingleViewer(_BaseViewer):
    def __init__(self, record, ax=None, color='k'):
        datafile = os.path.join(record.datastore.root, record.output_data[0].path)
        self.record = record
        self.data = DictTable(datafile, 'r')
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
        self.color = color

    def flip(self, a, scale, negate=False):
        a = np.reshape(a, self.shape)
        a = a.swapaxes(0,1)
        return np.concatenate((-(2 * negate -1) * a[:,::-1], a), axis=1) * scale

    def getFeatureDepth(self):
        if self.record.parameters.as_dict().has_key('featureDepth'):
            featureDepth = self.record.parameters['featureDepth']
        else:
            featureDepth = 56e-6
        return featureDepth

    def plotSetup(self, indices=[0], times=None, maxFeatureDepth=None):
        if times is not None:
            indices = []
            index = 0
            for time in times:
                index = self.getIndex(time, index)
                indices.append(index)

        if type(indices) is int:
            indices = [indices]
        
        delta = 150e-6

        featureDepth = self.getFeatureDepth()
        if maxFeatureDepth is None:
            maxFeatureDepth = featureDepth

        y0 = delta * 0.1 + maxFeatureDepth

        scale = 1e+6
        y0 = y0 * scale
        ymin = 1e-5 * scale - y0
        # ymax = 7.5e-5 * scale - y0
        ymax = -ymin * 0.1

        y = self.flip(self.x, scale) - y0 + (maxFeatureDepth - featureDepth) * scale

        self._plot(y, scale, indices)

        xmin, xmax = self.ax.get_xlim()
        rect = plt.Rectangle((xmin, ymin), xmax - xmin, (-featureDepth * scale - ymin) - delta * 0.05, facecolor='0.8', linewidth=0)
        self.ax.add_patch(rect)

        self.ax.set_ylim(ymin, ymax)
        self.ax.set_ylabel(r'$y$ ($\micro\metre$)')

    def _plot(self, y, scale, indices):
        raise NotImplementedError

    def getIndex(self, time, index):
        indexJump = 10

        latestIndex = self.data.getLatestIndex()

        while index <= latestIndex and self.data[index]['elapsedTime'] < time:
            index += indexJump

        if index > latestIndex:
            index = latestIndex

        return index
