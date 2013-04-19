import os.path


import matplotlib.pyplot as plt
import numpy as np
from extremefill2D.dicttable import DictTable
import fipy as fp


class ContourViewer(object):
    def __init__(self, data):
        self.data = data
        data0 = self.data[0]
        mesh = fp.Grid2D(nx=data0['nx'], ny=data0['ny'], dx=data0['dx'], dy=data0['dy'])
        self.shape = (mesh.ny, mesh.nx)
        self.x = mesh.x.value
        self.y = mesh.y.value

    def plot(self, index=0, filename=None):
        phi = self.data[index]['distance']
        phi0 = self.data[0]['distance']
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_aspect(1.)

        delta = 150e-6
        featureDepth = 56e-6
        y0 = delta * 0.1 + featureDepth

        scale = 1e+6
        xlim = 8e-6 * scale
        y0 = y0 * scale
        ymin = 1e-5 * scale - y0
        ymax = 7.5e-5 * scale - y0


        def flip(a, negate=False):
            a = np.reshape(a, self.shape)
            a = a.swapaxes(0,1)
            return np.concatenate((-(2 * negate -1) * a[:,::-1], a), axis=1) * scale

        x = flip(self.y, negate=True)
        y = flip(self.x) - y0
        phi = flip(phi)
        phi0 = flip(phi0)

        plt.contourf(x,y, phi0, (-1e+10, 0, 1e+10), colors=('k', 'w'), alpha=0.1)
        plt.contour(x, y, phi, (0,), colors=('k',))
        ax.set_ylim(ymin, ymax)
        ax.set_xlim(-xlim, xlim)
        ax.set_xticks((-xlim, 0, xlim))
        ax.set_xlabel(r'$x$ ($\micro\metre$)')
        ax.set_ylabel(r'$y$ ($\micro\metre$)')
        if filename:
            plt.savefig(filename)
        else:
            plt.show()

 
if __name__ == '__main__':
    from smtext import getSMTRecords
    records = getSMTRecords(tags=['serialnumber10'], parameters={'kPlus' : 100.0, 'Nx' : 600})
    record = records[0]
    datafile = os.path.join(record.datastore.root, record.output_data[0].path)
    data = DictTable(datafile, 'r')
    viewer = ContourViewer(data)
    latestIndex = data.getLatestIndex()
    print 'latestIndex',latestIndex
    index = 0
    while index <= latestIndex:
        filename = os.path.join('movie600', 'step%s.png' % str(index).rjust(6, '0'))
        viewer.plot(index=index, filename=filename)
        index += 10
    
                     

