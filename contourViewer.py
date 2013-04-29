import os.path

import tables
import matplotlib.pyplot as plt
from baseViewer import _BaseViewer


class ContourViewer(_BaseViewer):
    def _plot(self, y, scale, indices, ax):
        x = self.flip(self.y, scale, negate=True)

        phi0 = self.data[0]['distance']
        phi0 = self.flip(phi0, scale)

        plt.contourf(x,y, phi0, (-1e+10, 0, 1e+10), colors=('k', 'w'), alpha=0.1)

        for index in indices:
            phi = self.data[index]['distance']
            phi = self.flip(phi, scale)
            plt.contour(x, y, phi, (0,), colors=('k',))

        ax.set_aspect(1.)
        xlim = 8e-6 * scale
        ax.set_xlim(-xlim, xlim)
        ax.set_xticks((-xlim, 0, xlim))
        ax.set_xlabel(r'$x$ ($\micro\metre$)')


if __name__ == '__main__':
    viewer = ContourViewer(tags=['serialnumber18'], parameters={'Nx' : 600})
    viewer.plot(indices=200)
    
    
                     

