import os.path

import tables
import matplotlib.pyplot as plt
import numpy as np
from baseViewer import _BaseViewer


class FieldViewer(_BaseViewer):
    def _plot(self, y, scale, indices, ax):
        ny, nx = y.shape
        fields = ('suppressor', 'cupric', 'potential')
        bulkValues = (0.02, 1000.0, 0.25)

        for index in indices:
            for bulkValue, field in zip(bulkValues, fields):
                field = self.data[index][field]
                field = self.flip(field, scale=1.)
                plt.plot(field[: , nx / 2] / bulkValue, y[:, 0])

            theta = self.data[index]['interfaceTheta']
            theta = self.flip(theta, scale=1.)
            theta = np.amax(theta, axis=1)
            plt.plot(theta, y[:, 0])

        ax.set_xlim(0, 1.)


if __name__ == '__main__':
    viewer = FieldViewer(tags=['serialnumber18'], parameters={'Nx' : 600})
    viewer.plot(indices=200)
    
                     

