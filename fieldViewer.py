import tables
import numpy as np
from baseViewer import _BaseSingleViewer
from smtext import getSMTRecords


class FieldViewer(_BaseSingleViewer):
    def _plot(self, y, scale, indices):
        ny, nx = y.shape
        fields = ('suppressor', 'cupric', 'potential')
        bulkValues = (0.02, 1000.0, 0.25)
        labels = (r'$\bar{c}_{\theta}$', r'$\bar{c}_{\text{cu}}$', r'$\bar{\eta}$')

        for index in indices:
            for bulkValue, field, label in zip(bulkValues, fields, labels):
                field = self.data[index][field]
                field = self.flip(field, scale=1.)
                self.ax.plot(field[: , nx / 2] / bulkValue, y[:, 0], zorder=0.9, lw=2, label=label)

            theta = self.data[index]['interfaceTheta']
            theta = self.flip(theta, scale=1.)
            theta = np.amax(theta, axis=1)
            self.ax.plot(theta, y[:, 0], zorder=0.9, lw=2, label=r'$\theta$')
            

        self.ax.set_xlim(0, 1.05)
        self.ax.legend(loc='upper left')


if __name__ == '__main__':
    records = getSMTRecords(tags=['serialnumber18'], parameters={'Nx' : 600})
    viewer = FieldViewer(record=records[0])
    viewer.plot(indices=200)

    
                     

