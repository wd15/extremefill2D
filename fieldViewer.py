import os.path

import tables
import matplotlib.pyplot as plt
import numpy as np
from extremefill2D.dicttable import DictTable
import fipy as fp


class FieldViewer(object):
    def __init__(self, data):
        self.data = data
        data0 = self.data[0]
        mesh = fp.Grid2D(nx=data0['nx'], ny=data0['ny'], dx=data0['dx'], dy=data0['dy'])
        self.shape = (mesh.ny, mesh.nx)
        self.x = mesh.x.value
        self.y = mesh.y.value

    def plot(self, indices=[0], filename=None):
        if type(indices) is int:
            indices = [indices]

        fig = plt.figure()

        ax = fig.add_subplot(111)

        delta = 150e-6
        featureDepth = 56e-6
        y0 = delta * 0.1 + featureDepth

        scale = 1e+6
#        xlim = 8e-6 * scale
        y0 = y0 * scale
        ymin = 1e-5 * scale - y0
        ymax = 7.5e-5 * scale - y0


        def flip(a, negate=False, scale=scale):
            a = np.reshape(a, self.shape)
            a = a.swapaxes(0,1)
            return np.concatenate((-(2 * negate -1) * a[:,::-1], a), axis=1) * scale

        y = flip(self.x) - y0        
        ny, nx = y.shape
        fields = ('suppressor', 'cupric', 'potential')
        bulkValues = (0.02, 1000.0, 0.25)

        for index in indices:
            for bulkValue, field in zip(bulkValues, fields):
                field = self.data[index][field]
                field = flip(field, scale=1.)
                plt.plot(field[: , nx / 2] / bulkValue, y[:, 0])

            theta = self.data[index]['theta']
            theta = np.maximum(theta, axis=1)

        ax.set_ylim(ymin, ymax)
        ax.set_xlim(0, 1.)
#        ax.set_xticks((-xlim, 0, xlim))
#        ax.set_xlabel(r'$x$ ($\micro\metre$)')
#        ax.set_ylabel(r'$y$ ($\micro\metre$)')
        if filename:
            plt.savefig(filename)
        else:
            plt.show()

        return fig


if __name__ == '__main__':
    from smtext import getSMTRecords
    records = getSMTRecords(tags=['serialnumber17'], parameters={'Nx' : 600})
    record = records[0]
    datafile = os.path.join(record.datastore.root, record.output_data[0].path)
    data = DictTable(datafile, 'r')
    viewer = FieldViewer(data)
    viewer.plot(indices=200)
    
                     

