import os.path
import sys


import tables
from contourViewer import ContourViewer
from fieldViewer import FieldViewer
from baseViewer import _BaseViewer
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

def update_progress(progress):
    progress = int(progress * 100)
    dec = progress / 10
    sys.stdout.write('\r[{0}] {1}%'.format('#' * dec + '-' * (10  - dec), progress))
    sys.stdout.flush()


class DoubleViewer(_BaseViewer):
    def __init__(self, tags=[], parameters={}):
        self.fig = plt.figure()
        gs = gridspec.GridSpec(1, 2, width_ratios=[1.0, 0.5])
        ax = self.fig.add_subplot(gs[0])
        self.contourViewer = ContourViewer(tags=tags, parameters=parameters, ax=ax)
        ax = self.fig.add_subplot(gs[1])
        self.fieldViewer = FieldViewer(tags=tags, parameters=parameters, ax=ax)

    def plotSetup(self, indices=[0]):
        self.fig.tight_layout()  
        self.contourViewer.ax.cla()
        self.fieldViewer.ax.cla()
        self.contourViewer.plotSetup(indices=indices)
        self.fieldViewer.plotSetup(indices=indices)
        self.fieldViewer.ax.set_ylabel('')
        labels = [''] * len(self.fieldViewer.ax.get_yticklabels())
        self.fieldViewer.ax.set_yticklabels(labels)
        ymin = self.fieldViewer.ax.get_ylim()[0]
        h = self.contourViewer.height
        self.fieldViewer.ax.axhspan(ymin, h, facecolor='0.8', linewidth=0)
        elapsedTime = self.fieldViewer.data[indices]['elapsedTime']
        timestring = r'$t={0:1.2f}$ ($\second$)'.format(elapsedTime)
        if not hasattr(self, 'title'):
            self.title = self.fig.suptitle(timestring, verticalalignment='bottom', x=0.7, y=0.05)
        else:
            self.title.set_text(timestring)
        

if __name__ == '__main__':
    viewer = DoubleViewer(tags=['serialnumber18'], parameters={'Nx' : 600})
    latestIndex = viewer.contourViewer.data.getLatestIndex()
    index = 0
    dataPath = os.path.join('Data', viewer.contourViewer.record.label)
    print 'dataPath',dataPath
    count = 0
    while index <= latestIndex:
        filename = os.path.join(dataPath, 'step%s.png' % str(index).rjust(6, '0'))
        fig = viewer.plot(indices=index, filename=filename)
        count += 1
        if count > 10:
            index += 10
        update_progress(float(index) / latestIndex)
    print 'finished'
                     

