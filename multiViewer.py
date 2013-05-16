import tables
from contourViewer import ContourViewer
from baseViewer import _BaseViewer
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from smtext import getSMTRecords


class MultiViewer(_BaseViewer):
    def __init__(self, records, baseRecords=None, title='', figsize=(8, 6)):
        self.fig = plt.figure(figsize=figsize)
        
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
            if baseRecord:
                self.viewers.append(ContourViewer(baseRecord, ax=ax, color='r'))

    def plotSetup(self, indices=[0], times=None):
        maxFeatureDepth = 0
        for viewer in self.viewers:
            maxFeatureDepth = max(maxFeatureDepth, viewer.record.parameters['featureDepth'])

        for i, viewer in enumerate(self.viewers):
            viewer.plotSetup(indices=indices, times=times, maxFeatureDepth=maxFeatureDepth)
            ax = viewer.ax
            if ax.colNum > 0:
                labels = [''] * len(ax.get_yticklabels())
                ax.set_yticklabels(labels)
                ax.set_ylabel('')
            if ax.colNum != ax.numCols / 2:
                ax.set_xlabel('')
                labels = [''] * len(ax.get_xticklabels())
                ax.set_xticklabels(labels)

if __name__ == '__main__':
    records = getSMTRecords(tags=['CFL', 'production'])
    records = [getSMTRecords(records=records, parameters={'CFL' : CFL})[0] for CFL in (0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64)]
    title = [r'CFL={0:1.2f}'.format(r.parameters['CFL']) for r in records[1:]]
    viewer = MultiViewer(records[1:], baseRecords=records[0], title=title)
    viewer.plot(times=(0., 1000., 2000., 3000., 4000.))

