import tables
from contourViewer import ContourViewer
from baseViewer import _BaseViewer
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from smtext import getData


class MultiViewer(_BaseViewer):
    def __init__(self, datasets):
        self.fig = plt.figure()
        gs = gridspec.GridSpec(1, len(datasets))
        self.viewers = []
        for i, dataset in enumerate(datasets):
            ax = self.fig.add_subplot(gs[i])
            for tags, parameters, color in dataset:
                datafile = getData(tags=tags, parameters=parameters)                
                self.viewers.append(ContourViewer(datafile, ax=ax, color=color))

    def plotSetup(self, indices=[0]):
        self.fig.tight_layout()  
        for viewer in self.viewers:
            viewer.plotSetup(indices=indices)


if __name__ == '__main__':
    datasets = [
        [[['serialnumber18'], {'Nx' : 600}, 'r'], [['serialnumber18'], {'Nx' : 300}, 'k']],
        [[['serialnumber18'], {'Nx' : 600}, 'r'], [['serialnumber18'], {'Nx' : 300}, 'k']]
        ]
        
    viewer = MultiViewer(datasets)
    viewer.plot(indices=(0, 1000, 2000))

                     

