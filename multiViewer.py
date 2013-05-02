import tables
from contourViewer import ContourViewer
from baseViewer import _BaseViewer
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from smtext import getSMTRecords


class MultiViewer(_BaseViewer):
    def __init__(self, records, baseRecords, title=''):
        self.fig = plt.figure()
        gs = gridspec.GridSpec(1, len(records))
        self.viewers = []
        if title is str:
            title = [title] * len(records)
        if type(baseRecords) not in (list, tuple):
            baseRecords = [baseRecords] * len(records)
        for i, (record, title, baseRecord) in enumerate(zip(records, title, baseRecords)):
            ax = self.fig.add_subplot(gs[i])
            self.viewers.append(ContourViewer(record, ax=ax, color='k'))
            self.viewers[-1].ax.set_title(title)
            self.viewers.append(ContourViewer(baseRecord, ax=ax, color='r'))

    def plotSetup(self, indices=[0], times=None):
        for i, viewer in enumerate(self.viewers):
            viewer.plotSetup(indices=indices, times=times)
            ax = viewer.ax
            if i > 1:
                labels = [''] * len(ax.get_yticklabels())
                ax.set_yticklabels(labels)
                ax.set_ylabel('')
            if i != (len(self.viewers) / 2) and i != (len(self.viewers) / 2 - 1):
                ax.set_xlabel('')
                labels = [''] * len(ax.get_xticklabels())
                ax.set_xticklabels(labels)

if __name__ == '__main__':
    CFLs = (0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64)
    viewers = []
    records = getSMTRecords(tags=['CFL', 'production'])
    records = [getSMTRecords(records=records, parameters={'CFL' : CFL})[0] for CFL in CFLs]
    title = [r'CFL={0:1.2f}'.format(r.parameters['CFL']) for r in records]
    viewer = MultiViewer(records[1:], baseRecords=records[0], title=title)
    viewer.plot(indices=(0, 50, 100), times=(0., 1000., 2000., 3000., 4000.))

