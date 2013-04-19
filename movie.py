import os.path


import matplotlib.pyplot as plt
import numpy as np
from extremefill2D.dicttable import DictTable
import fipy as fp


class ContourViewer(object):
    def __init__(self, datafile):
        self.data = DictTable(datafile, 'r')
        data0 = self.data[0]
        mesh = fp.Grid2D(nx=data0['nx'], ny=data0['ny'], dx=data0['dx'], dy=data0['dy'])
        self.shape = (mesh.ny, mesh.nx)
        self.x = np.reshape(mesh.x.value, self.shape)
        self.y = np.reshape(mesh.y.value, self.shape)

    def plot(self, index=0):
        phi = self.data[index]['distance']
        phi = np.reshape(phi, self.shape)
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_aspect(1.)
        
        ## vertical
        # pylab.contour(self.y.swapaxes(0,1), self.x.swapaxes(0,1), phi.swapaxes(0,1), (0,), colors=('k',), extent=(0, 1e-5, 0, 1e-4))
        # pylab.ylim(1e-5, 7.5e-5)
        # pylab.xlim(0, 8e-6)

        def flip(a, negate=False):
            a = a.swapaxes(0,1)
            return np.concatenate((-(2 * negate -1) * a[:,::-1], a), axis=1)

        scale = 1e+6
        x = flip(self.y, negate=True) * scale
        y = flip(self.x) * scale
        phi = flip(phi) * scale
        xlim = 8e-6 * scale
        ymin = 1e-5 * scale
        ymax = 7.5e-5 * scale

        plt.contour(x, y, phi, (0,), colors=('k',))
        ax.set_ylim(ymin, ymax)
        ax.set_xlim(-xlim, xlim)
        ax.set_xticks((-xlim, 0, xlim))
        ax.set_xlabel(r'$x$ ($\micro\metre$)')
        ax.set_ylabel(r'$y$ ($\micro\metre$)')
        plt.show()

 
class FieldViewer(object):
    def __init__(self, datafile):
        pass



if __name__ == '__main__':
    from smtext import getSMTRecords
    records = getSMTRecords(tags=['serialnumber10'], parameters={'kPlus' : 100.0, 'Nx' : 1200})
    record = records[0]
    datafile = os.path.join(record.datastore.root, record.output_data[0].path)
    ContourViewer(datafile).plot()
