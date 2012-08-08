import pylab
import numpy

fontsize=16
from viewer import Viewer

class KPlusVKMinusViewer(Viewer):


    def V(self, data):
        return data['omega'] * data['i0'] * self.E(data['appliedPotential'], data) / data['charge'] / data['faradaysConstant']

    def figureOfMerit(self, data):
        depositionRate, theta, potential, cupric, suppressor, X, dx = self.getDepositionRate(data)
        derivative = (depositionRate[2:] - depositionRate[:-2]) / dx / 2
        depositionRate = depositionRate[1:-1]
        mask = (depositionRate > (self.V(data) / 10000)) & (depositionRate > (max(depositionRate) / 100))

        if mask.any():
            if mask.all():
                localized = 0
            else:
                localized = 1
            return max(derivative[mask]), min(derivative[mask]), max(depositionRate), localized
        else:
            return -1e-10, -1e-10, max(depositionRate), 0

    def makeBackGroudPlot(self, kPlus, kMinus, xpos, ypos, axisbg=None, axeslabel=False, align=False, mainaxes=None):
        alpha = 0.5
        a = pylab.axes((xpos, ypos, 0.08, 0.08), frame_on=True, axisbg='w', alpha=alpha)
        a.patch.set_alpha(alpha)
        data = self.generateData({'kPlus' : kPlus, 'kMinus' : kMinus})
        depositionRate, theta, potential, cupric, suppressor, X, dx = self.getDepositionRate(data)
        xlim = (-data['featureDepth'], 0)
        ylim = (0,1e-8)
        if axeslabel is True:
            pylab.xlabel(r'$\bm z$', fontsize=fontsize, labelpad=3.5, alpha=1)
            pylab.ylabel(r'$\bm v$', fontsize=fontsize, rotation='horizontal', labelpad=2, alpha=1)
            from matplotlib.patches import FancyArrowPatch
            disx = (xlim[1] - xlim[0]) * 1.4
            disy = (ylim[1] - ylim[0]) * 1.5
            a.add_patch(FancyArrowPatch((xlim[0] - disx * 0.025, ylim[0]),(xlim[0] + disx, ylim[0]),arrowstyle='-|>',mutation_scale=20, lw=2, clip_on=False, facecolor='black'))
            a.add_patch(FancyArrowPatch((xlim[0], ylim[0] - ylim[1] / 20),(xlim[0], ylim[0] + disy),arrowstyle='-|>',mutation_scale=20, lw=2, clip_on=False, facecolor='black'))

        pylab.plot(X, depositionRate, 'k', lw=2, alpha=alpha)
        pylab.setp(a, ylim=ylim, xlim=xlim, xticks=[], yticks=[], alpha=alpha)
        if align:
            pylab.plot((-data['featureDepth'] / 2,), (1e-8 / 2,), 'ks', lw=3) 
        if align:
            pylab.axes(mainaxes)
            pylab.loglog((data['kMinus'],), (data['kPlus'],), 'kx', lw=3, ms=8) 
        a.patch.set_alpha(alpha)
    
        

    def plot(self, filesuffix=('.png',)):

        pylab.figure()

        kPluses = 10**numpy.linspace(0, 3, 100)
        kMinuses = 10**numpy.linspace(6, 9, 100)
        figureOfMerits = numpy.zeros((len(kPluses), len(kMinuses), 4), 'd')
        for i, kPlus in enumerate(kPluses):
            for j, kMinus in enumerate(kMinuses):
                figureOfMerits[i, j, :] = self.figureOfMerit(self.generateData({'kPlus' : kPlus, 'kMinus' : kMinus}))
        data = self.generateData({'kPlus' : kPluses[0], 'kMinus' : kMinuses[0]})

        a = pylab.contourf(kMinuses, kPluses, figureOfMerits[...,0], (-1e+10, 1e+10), colors=('red',))
        a = pylab.contourf(kMinuses, kPluses, figureOfMerits[...,1], (-1e+10, 0), colors=('orange',))
        a = pylab.contourf(kMinuses, kPluses, figureOfMerits[...,0], (-1e+10, 0), colors=('green',))
        a = pylab.contourf(kMinuses, kPluses, figureOfMerits[...,2], (-1e+10, self.V(data) / 10000), colors=('blue',))
        
        a = pylab.contour(kMinuses, kPluses, figureOfMerits[...,3], (-1e+10, 0.5, 1e+10), linestyles='solid', linewidths=4, colors='k')

        a.ax.set_xscale('log')
        a.ax.set_yscale('log')
        pylab.xticks((10**6, 10**7, 10**8, 10**9), fontsize=fontsize)
        pylab.yticks((10**0, 10**1, 10**2, 10**3), fontsize=fontsize)
        pylab.xlabel(r'$k^-$ $\left(1\per\metre\right)$', fontsize=fontsize)
        pylab.ylabel(r'$k^+$ $\left(\power{\metre}{3}\per\mole\cdot\second\right)$', fontsize=fontsize)

        pylab.text(2 * 10**6, 7 * 10**2, r'I', fontsize=fontsize)
        pylab.text(3 * 10**7, 7 * 10**2, r'II', fontsize=fontsize)
        pylab.text(6 * 10**8, 7 * 10**2, r'III', fontsize=fontsize)
        pylab.text(6 * 10**8, 7 * 10**1, r'IV', fontsize=fontsize)



        for fP, kPlus, paxeslabel in ((1.143,3.51e+00, False), (0.975, 9.33e+00, False), (0.916, 3.51e+01, False), (0.89, 9.33e+01, False), (0.87, 3.51e+02, True)):
            for fM, kMinus, maxeslabel in ((1.4, 2.48e+06, False), (1.07, 7.05e+6, False), (0.96, 2.48e+07, False), (0.91, 7.05e+7, False), (0.88, 2.48e+08, True)):
                xpos = (numpy.log10(kMinus) - 6.) / 3. *  fM
                ypos = numpy.log10(kPlus) / 3. * fP        
                self.makeBackGroudPlot(kPlus, kMinus, xpos, ypos, axisbg=None, axeslabel=paxeslabel and maxeslabel, align=False, mainaxes=a.ax)

        for fs in filesuffix:
            pylab.savefig('kPlusVkMinus' + fs)

if __name__ == '__main__':
    KPlusVKMinusViewer().plot()

