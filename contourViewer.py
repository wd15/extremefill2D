import tables
from baseViewer import _BaseSingleViewer
from tools import getSMTRecords
import brewer2mpl
import numpy as np


class ContourViewer(_BaseSingleViewer):
    def _plot(self, y, scale, indices):
        x = self.flip(self.x, scale, negate=True)
        
        phi0 = self.data[0]['distance']
        phi0 = self.flip(phi0, scale)

        set1 = brewer2mpl.get_map('BuGn', 'sequential', 9).mpl_colors

        if self.mirror:
            x = np.concatenate((-x[::-1], x))
            y = np.concatenate((y[::-1], y))
            phi0 =  np.concatenate((phi0[::-1], phi0))

        self.ax.contourf(x,y, phi0, (-1e+10, 0, 1e+10), colors=(set1[4], set1[1]))

        Greys = brewer2mpl.get_map('Greys', 'sequential', 9).mpl_colors

        for index in indices[1:]:
            phi = self.data[index]['distance']
            phi = self.flip(phi, scale)

            if self.mirror:
                phi = np.concatenate((phi[::-1], phi))

            cc = self.ax.contour(x, y, phi, (0,), colors=(Greys[7],), linewidths=(1.5,))
            h = min(cc.collections[0].get_paths()[0].vertices[:,1])
            print 
            if self.cutoff and h > self.cutoffvalue:
                break

        self.height = min(cc.collections[0].get_paths()[0].vertices[:,1])

        self.ax.set_aspect(1.)
        xlim = 12e-6 * scale
        if self.mirror:
            self.ax.set_xlim(-xlim, xlim)
        else:
            self.ax.set_xlim(0, xlim)
        self.ax.set_xticks(())
        self.ax.set_yticks(())
#        self.ax.set_xticklabels(('', r'${0:d}$'.format(int(xlim))))
        #self.ax.set_xlabel(r'$x$ ($\micro\metre$)')
        self.phi = phi

if __name__ == '__main__':
    records = getSMTRecords(tags=['serialnumber18'], parameters={'Nx' : 600})
    viewer = ContourViewer(record=records[0])
    viewer.plot(indices=200)
    
    
                     

