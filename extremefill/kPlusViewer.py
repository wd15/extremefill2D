## Need to import PyTables before importing fipy for some reason.
import pylab
import numpy

from depositionViewer import DepositionViewer

class KPlusViewer(DepositionViewer):

    def __init__(self):
        parameter = 'kPlus'
        super(KPlusViewer, self).__init__(parameter, (1e-2, 5e0, 2.5e1, 5e1, 1e2, 1e3), r'$k^+=%4.2f$ $\power{\metre}{3}\per\mole\cdot\second$', lfs=8)
        self.inlayDataset = self.generateDataSet(parameter=parameter, values=['%1.2e' % kPlus for kPlus in 10**numpy.linspace(0, 3, 100)])

    def plot(self, filesuffix='.png'):
        super(KPlusViewer, self).plot(filesuffix=filesuffix) 

    def _legend(self, ax):
        if ax.colNum == 0 and ax.rowNum == 1:
            self.legend =  pylab.legend(loc='upper left')

    def subplot(self, fig):
        ax = pylab.axes(fig)
        from plotkPlusVPotentialDrop import plotkPlusVPotential
        abg = pylab.axes((0.2, 0.7, 0.18, 0.18), frame_on=True, axisbg='y')
        plotkPlusVPotential(self.inlayDataset)
        from matplotlib.patches import FancyArrowPatch
        abg.add_patch(FancyArrowPatch((25, 0.13), (13, -0.05), arrowstyle='<-', mutation_scale=20, lw=2, color='red', clip_on=False, alpha=0.7))
        abg.add_patch(FancyArrowPatch((5, 0.07), (5, -0.085), arrowstyle='<-', mutation_scale=20, lw=2, color='green', clip_on=False, alpha=0.7))
        pylab.text(1.5, 0.21, r'(e)', fontsize=12)

    def getPotentials(self):
        X, ID = self.getX(self.inlayDataset[0])
        potentials = numpy.zeros(len(self.inlayDataset), 'd')
        for i, kPlus in enumerate(self.inlayDataset):
            potentials[i] = self.inlayDataset[i]['potential'][ID]

        return potentials

    def plotkPlusVPotential(self):
        kPluses = [data['kPlus'] for data in self.inlayDataset]
        pylab.semilogx(kPluses, self.getPotentials(), 'k', lw=1)
        pylab.semilogx((1, 1000), (0.25, 0.25), 'k--', lw=1)
        pylab.xlabel(r'$k^+$', fontsize=10, labelpad=-3)
        pylab.xticks((1, 10, 100, 1000), (r'$1$', r'$10$', r'$100$', r'$1000$'), fontsize=8)
        pylab.yticks((0.1, 0.2), (r'$-0.1$', r'$-0.2$'), fontsize=8)
        pylab.ylim(0.04, 0.27)
        pylab.xlim(1, 1000)
        pylab.ylabel(r'$\eta$', fontsize=10, rotation='horizontal', labelpad=-8)

    def replaceString(self, Label):
        return Label.replace('.00$', '$')

    # plotDeposition(numpy.array((15e-6, 25e-6, 35e-6, 45e-6, 55e-6, 65e-6, 75e-6, 85e-6))[::-1],
    #                'tmp/base-featureDepth-',
    #                r'$h=%1.0f$ $\micro\metre$',
    #                'featureDepth',
    #                mulFactor=1000000,
    #                legend=3,
    #                filesuffix=filesuffix,
    #                xticks=(-80, -60, -40, -20, 0),
    #                colors = numpy.array(['b', 'g', 'r', 'c', 'm', 'y', 'k', '#663300'])[::-1])

if __name__ == '__main__':
    KPlusViewer().plot()
