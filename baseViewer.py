import os.path


import tables
import fipy as fp
import matplotlib.pyplot as plt
import numpy as np
from dicttable import DictTable
import brewer2mpl

class _BaseViewer(object):
    def plot(self, indices=[0], filename=None, times=None, cutoffvalue=-1, mirror=False, cutoff=True, labels=False, show=True):
        self.mirror = mirror
        self.cutoff = cutoff
        self.cutoffvalue = cutoffvalue
        self.labels = labels
        self.show = show
        self.plotSetup(indices=indices, times=times, cutoff=cutoff)
        self.plotSave(filename)

    def plotSetup(self, indices=[0], cutoff=None):
        raise NotImplementedError

    def plotSave(self, filename):
        if filename:
            plt.savefig(filename)
        elif self.show:
            plt.show()



class _BaseSingleViewer(_BaseViewer):
    def __init__(self, record, ax=None, color='k', indexJump=10, mirror=False):
        datafile = os.path.join(record.datastore.root, record.output_data[0].path)
        self.record = record
        self.data = DictTable(datafile, 'r')
        data0 = self.data[0]

        mesh = fp.Grid2D(nx=data0['nx'], ny=data0['ny'], dx=data0['dx'], dy=data0['dy'])
        
        self.dy = mesh.dy
        self.shape = (mesh.ny, mesh.nx)
        self.x = mesh.x.value
        self.y = mesh.y.value
        if ax is None:
            fig = plt.figure()
            self.ax = fig.add_subplot(111)
        else:
            self.ax = ax
        self.color = color
        self.mirror = mirror

        self.indexJump = self.record.parameters['data_frequency']


    def flip(self, a, scale, negate=False):
        a = np.reshape(a, self.shape)
        a = a.swapaxes(0,1)
        return a * scale

    def getFeatureDepth(self):
        if self.record.parameters.as_dict().has_key('featureDepth'):
            featureDepth = self.record.parameters['featureDepth']
        else:
            featureDepth = 56e-6
        return featureDepth

    def plotSetup(self, indices=[0], times=None, maxFeatureDepth=None, cutoff=None):
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

        y0 = maxFeatureDepth + np.amin(self.dy) * 10
        scale = 1e+6
        y0 = y0 * scale
        ymin = -60e-6 * scale
        ymax = -ymin * 0.1

        y = self.flip(self.y, scale) - y0 + (maxFeatureDepth - featureDepth) * scale
        
        self._plot(y, scale, indices)

        xmin, xmax = self.ax.get_xlim()
        xmin += self.x[0] * 1e+6

        #set2 = brewer2mpl.get_map('Set2', 'qualitative', 8).mpl_colors
        set1 = brewer2mpl.get_map('BuGn', 'sequential', 9).mpl_colors
        if not self.mirror:
            rect = plt.Rectangle((xmin, ymin), xmax - xmin, (-featureDepth * scale - ymin) - delta * 0.05, facecolor=set1[4], linewidth=0)
            self.ax.add_patch(rect)

        self.ax.set_ylim(ymin, ymax)
        #self.ax.set_ylabel(r'$y$ ($\micro\metre$)')

    def _plot(self, y, scale, indices):
        raise NotImplementedError

    def getIndex(self, time, index):
        latestIndex = self.data.getLatestIndex()

        while index <= latestIndex and self.data[index, 'elapsedTime'] < time:
            index += self.indexJump

        if index > latestIndex:
            index = int(latestIndex)

        return index
