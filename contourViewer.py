import tables
from baseViewer import _BaseSingleViewer
from tools import getSMTRecords
import brewer2mpl


class ContourViewer(_BaseSingleViewer):
    def _plot(self, y, scale, indices):
        x = self.flip(self.x, scale, negate=True)
        
        phi0 = self.data[0]['distance']
        phi0 = self.flip(phi0, scale)

        set1 = brewer2mpl.get_map('BuGn', 'sequential', 9).mpl_colors
        self.ax.contourf(x,y, phi0, (-1e+10, 0, 1e+10), colors=(set1[4], set1[1]))

        Greys = brewer2mpl.get_map('Greys', 'sequential', 9).mpl_colors

        for index in indices[1:]:
            phi = self.data[index]['distance']
            phi = self.flip(phi, scale)
            cc = self.ax.contour(x, y, phi, (0,), colors=(Greys[7],), linewidths=(1.5,))
            h = min(cc.collections[0].get_paths()[0].vertices[:,1])
            if h > -1:
                break

        self.height = min(cc.collections[0].get_paths()[0].vertices[:,1])

        self.ax.set_aspect(1.)
        xlim = 12e-6 * scale
        self.ax.set_xlim(0, xlim)
        self.ax.set_xticks((0, xlim))
        self.ax.set_xticklabels(('', r'${0:d}$'.format(int(xlim))))
        #self.ax.set_xlabel(r'$x$ ($\micro\metre$)')
        self.phi = phi


if __name__ == '__main__':
    records = getSMTRecords(tags=['serialnumber18'], parameters={'Nx' : 600})
    viewer = ContourViewer(record=records[0])
    viewer.plot(indices=200)
    
    
                     

