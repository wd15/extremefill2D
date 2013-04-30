import tables
from baseViewer import _BaseSingleViewer


class ContourViewer(_BaseSingleViewer):
    def _plot(self, y, scale, indices):
        x = self.flip(self.y, scale, negate=True)

        phi0 = self.data[0]['distance']
        phi0 = self.flip(phi0, scale)

        self.ax.contourf(x,y, phi0, (-1e+10, 0, 1e+10), colors=('0.8', 'w'))


        for index in indices:
            phi = self.data[index]['distance']
            phi = self.flip(phi, scale)
            cc = self.ax.contour(x, y, phi, (0,), colors=('k',))

        self.height = min(cc.collections[0].get_paths()[0].vertices[:,1])

        self.ax.set_aspect(1.)
        xlim = 8e-6 * scale
        self.ax.set_xlim(-xlim, xlim)
        self.ax.set_xticks((-xlim, 0, xlim))
        self.ax.set_xlabel(r'$x$ ($\micro\metre$)')


if __name__ == '__main__':
    viewer = ContourViewer(tags=['serialnumber18'], parameters={'Nx' : 600})
    viewer.plot(indices=200)
    
    
                     

