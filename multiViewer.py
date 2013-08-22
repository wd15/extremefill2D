import tables
from contourViewer import ContourViewer
from baseViewer import _BaseViewer
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from tools import getSMTRecords
import numpy as np

class DummyViewer(object):
    def __init__(self, reocrd, ax=None, color='k'):
        self.ax = ax

    def plotSetup(self, indices=None, times=None, maxFeatureDepth=None):
        pass

    def getFeatureDepth(self):
        return 56e-6

class MultiViewer(_BaseViewer):
    def __init__(self, records, baseRecords=None, rowtitle=None, columntitle=None, figsize=(1.5, 6)):

        self.rowtitle = rowtitle
        if hasattr(records[0], 'label'):
            records = [records]
        recordset = records[0]
        self.fig = plt.figure(figsize=np.array(figsize) * np.array((len(recordset), len(records))))
        gs = gridspec.GridSpec(len(records), len(recordset))
        self.viewers = []
        if type(baseRecords) not in (list, tuple):
            baseRecords = [baseRecords] * len(recordset)
            
        for j, recordset in enumerate(records):
            for i, (record, baseRecord) in enumerate(zip(recordset, baseRecords)):
                ax = self.fig.add_subplot(gs[j,i])
                if record and len(record.output_data) > 0:
                    v = ContourViewer(record, ax=ax, color='k')
                else:
                    v = DummyViewer(record, ax=ax, color='k')
                self.viewers.append(v)
                if j == 0 and columntitle:
                    self.viewers[-1].ax.set_title(columntitle(v.record))
                if baseRecord:
                    self.viewers.append(ContourViewer(baseRecord, ax=ax, color='r'))

    def plotSetup(self, indices=[0], times=None):
        maxFeatureDepth = 0
        for viewer in self.viewers:
            maxFeatureDepth = max(maxFeatureDepth, viewer.getFeatureDepth())

        size = self.fig.get_size_inches()
        size[1] = size[1] * maxFeatureDepth / 56e-6
        self.fig.set_size_inches(size)

        for i, viewer in enumerate(self.viewers):
            viewer.plotSetup(indices=indices, times=times, maxFeatureDepth=maxFeatureDepth)
            ax = viewer.ax
            if ax.colNum > 0:
                labels = [''] * len(ax.get_yticklabels())
                ax.set_yticklabels(labels)
                ax.set_ylabel('')
            else:
                ylabel = ax.get_ylabel()
                if self.rowtitle:
                    ylabel += ", " + self.rowtitle(viewer.record)
                ax.set_ylabel(ylabel)
            if ax.colNum != ax.numCols / 2 or ax.rowNum < ax.numRows - 1:
                ax.set_xlabel('')
                labels = [''] * len(ax.get_xticklabels())
                ax.set_xticklabels(labels)

def plot1DFigure(figNum):
    import extremefill
    if figNum == 5:
        extremefill.generateFigures(datafile='/users/wd15/git/extremefill/data.h5', fignumbers=(figNum,), filesuffix=())
    else:
        extremefill.generateFigures(datafile='/users/wd15/git/extremefill/data.h5', fignumbers=(figNum,), filesuffix=(), deposition_only=True)
    fig = plt.gcf()
    fig.set_size_inches(10, 8)
    plt.show()

def plotFeatures(parameter, parameterValues, Nxs, tags, title=r'{0:1.1e}', figsize=None):
    from smtext import getSMTRecords, smt_ipy_table
    records = []
    for tag in tags:
        records += getSMTRecords(tags=[tag])
    records = [[getSMTRecords(records=records, parameters={parameter : v, 'Nx' : Nx})[0] for v in parameterValues] for Nx in Nxs]
    title = [title.format(r.parameters[parameter]) for r in records[0]]
    viewer = MultiViewer(records, title=title, figsize=(1.2 * len(records[0]), 3.8 * len(records)))
    plt.tight_layout(pad=0, w_pad=-2, h_pad=-1)
    viewer.plot(times=(0., 1000., 2000., 3000., 4000., 5000.))
    return smt_ipy_table([r for rs in records for r in rs], fields=['label', 'timestamp', 'parameters', 'repository', 'version', 'duration'], parameters=[parameter, 'Nx'])

if __name__ == '__main__':
    kPluses = (0.01, 5.0, 25.0, 50.0, 100.0, 1000.0)
    records = getSMTRecords(tags=['serialnumber9']) + getSMTRecords(tags=['serialnumber10'])
    records = [[getSMTRecords(records=records, parameters={'kPlus' : kPlus, 'Nx' : Nx})[0] for kPlus in kPluses] for Nx in (300, 600, 1200)]
    title = [r'$k^+$={0:1.1e}'.format(r.parameters['kPlus']) for r in records[0]]
    viewer = MultiViewer(records, title=title, figsize=(12, 9))
    viewer.plot(times=(0., 1000., 2000., 3000., 4000., 5000.))

