import pylab

from matplotlib.patches import FancyArrowPatch

# from matplotlib import rc
# matplotlib.use('Agg')
# rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
# rc('text', usetex=True)
# pylab.ioff()
# pylab.hold(True)

class SchematicViewer(object):
    def __init__(self, datafile=None):
        pass

    def plot(self, filename=None):
        scale = 1e6
        delta = 150e-6
        perimeterRatio=1. / 2.8e-6 * 0.093
        fieldWidth = 2 / perimeterRatio
        featureDepth = 56e-6
        trenchWidth = 2 * 0.093 / perimeterRatio
        d = delta * scale * 0.5
        r = fieldWidth * scale * 1.1
        h = featureDepth * scale
        w = trenchWidth * scale * 2
        L = d + 0.00002 * scale * 2
        y1 = L + 0.00001 * scale
        x0 = -0.00004 * scale
        x1 = 0.00007 * scale
        y0 = -h - 0.00001 * scale

        eqnFont = 9

        fig = pylab.figure(figsize=(8, 6), dpi=200)
        ax = fig.add_subplot(111, aspect='equal')


        ax.add_patch(pylab.Rectangle((-w / 2, -h), w, h, alpha=0.2, color='black', ec='none', zorder=1))
        ax.add_patch(pylab.Rectangle((-r / 2, 0), r + r / 3, d, alpha=0.2, color='black', ec='none', zorder=1))
        ax.add_patch(pylab.Rectangle((-r / 2, d), r + r / 3, L - d, alpha=0.1, color='black', ec='none', zorder=1))

        pylab.plot((-r / 2, -w / 2, -w / 2, w / 2, w / 2, r / 2 + r / 3),
                   (0, 0, -h, -h, 0, 0), 'k', lw=3, alpha=0.5)

        pylab.plot((-r / 2, -r / 2),
                   (d, 0), 'k--', lw=3, alpha=0.5)

        pylab.plot((r / 2 + r / 3, r / 2 + r / 3),
                   (d, 0), 'k--', lw=3, alpha=0.5)

        pylab.plot((-r / 2, r / 2 + r / 3),
                   (L, L), 'k', lw=3, alpha=0.5)


        pylab.ion()
        pylab.xticks([])
        pylab.yticks((-h, 0, d, L), (r'$-h$', 0, r'$\delta$', r'$L$'))

        pylab.axes(ax, aspect='equal')
        pylab.ylim(ymin=y0)
        pylab.ylim(ymax=y1)
        pylab.xlim(xmax=x1)
        pylab.xlim(xmin=x0)
        pylab.xlabel(r'')
        pylab.ylabel(r'$z$', fontsize=16, rotation='horizontal')

        pylab.text(-20, d / 2 - 10, 
                    r'\['
                    r'\begin{split}'
                    r'     & \hspace{-25pt} \text{Boundary Layer} \\'
                    r'    \nabla^2 \phi &= 0 \\'
                    r'    \partial_t C_{\text{Sup}} &= D_{\text{Sup}} \nabla^2 C_{\text{Sup}}^{} \\'
                    r'    \partial_t C_{\text{Cu}} &= D_{\text{Cu}} \nabla^2 C_{\text{Cu}}^{}'
                    r'\end{split}'
                    r'\]', fontsize=eqnFont)


        pylab.text(-2, -25, r'Annular TSV', rotation='vertical', fontsize=eqnFont)

        kX = 14
        kY = -16
        pylab.text(kX, kY - 10,
                   r'\['
                   r'\begin{cases}'
                   r'    & \hspace*{-8pt} \partial_t \theta = k_+ C_{\text{Sup}}^{} \left(1 - \theta\right) \\'
                   r'    & \hspace*{16pt} - k_- \theta v \\'
                   r'    & \hspace*{-8pt}  \text{and Eqs. 5, 7 and 8} '
                   r'\end{cases}'
                   r'\]', rotation='horizontal', fontsize=eqnFont)


#                   r'$\partial_t C_{\text{Sup}}^{} =  k^+ C_{\text{Sup}}^{} \left(1 - \theta\right) - k^- \theta v$', fontsize=eqnFont)

        caseX = 13
        caseY = -55
        # pylab.text(caseX, caseY,
        #             r'\['
        #             r'\begin{cases}'
        #             r'    & \hspace*{-8pt} \partial_z^2  \eta = \frac{\rho n F}{\Omega} v \frac{P}{a_f}, \\'
        #             r'    & \hspace*{-8pt} D_{\text{Sup}}^{} \partial_z^2 C_{\text{Sup}}^{} = \\'
        #             r'    & \Gamma k^+ C_{\text{Sup}}^{} \left(1-\theta\right) \frac{P}{a_f},\\'
        #             r'    & \hspace*{-8pt} D_{\text{Cu}}^{} \partial_z^2 C_{\text{Cu}}^{} = \frac{v}{\Omega} \frac{P}{a_f}'
        #             r'\end{cases}'
        #             r'\]', rotation='horizontal', fontsize=eqnFont)

        pylab.text(-28, d - 7, 
                    r'\['
                    r'    C_{\text{Sup}}^{} = C_{\text{Sup}}^{\infty}, C_{\text{Cu}}^{} = C_{\text{Cu}}^{\infty}'
                    r'\]', fontsize=eqnFont)

        pylab.text(-27, L - 8, 
                    r'\['
                    r'\begin{split}'
                    r'     & \hspace{-20pt} \text{Reference Electrode} \\'
                    r'     & \phi = -E_{\text{App}}^{}'
                    r'\end{split}'
                    r'\]', fontsize=eqnFont)

        y910 = -15

#        pylab.text(-r / 2 - 3, y910, r'Eqs. (5, 7)', fontsize=eqnFont) 
        # ax.add_patch(FancyArrowPatch((-r / 4 - 5, y910 + 3.5),(-r / 4 + 5, 1.5), arrowstyle='->',mutation_scale=10, lw=1))

        y1112 = -h + 15
        # pylab.text(-r / 2 - 3, y1112, r'Eqs. (11, 12)', fontsize=eqnFont) 
        # ax.add_patch(FancyArrowPatch((-r / 4 - 5, y1112),(0, -h-0.8), arrowstyle='->',mutation_scale=10, lw=1))

        asw = r * 1.02
        afy = -h + h * 0.8
        afw = w * 1.1
        ax.add_patch(FancyArrowPatch((-asw / 2, afy),(afw / 2, afy), arrowstyle='<->',mutation_scale=10, lw=1))
        pylab.text(-20, afy + 2, r'$R_o$', fontsize=eqnFont) 


        afy = -h + h * 0.8
        afw = w * 1.1
        ax.add_patch(FancyArrowPatch((-asw / 2, afy - 10),(-afw / 2, afy - 10), arrowstyle='<->',mutation_scale=10, lw=1))
        pylab.text(-20, afy + 2 - 10, r'$R_i$', fontsize=eqnFont) 




        asy = 0 + d * 0.1
        
        ax.add_patch(FancyArrowPatch((-asw / 2, asy),(asw / 2 + r / 3, asy), arrowstyle='<->',mutation_scale=15, lw=1))
        pylab.text(-2, asy + 2, r'$R_{\text{Cell}}$', fontsize=eqnFont)

        caseYY = caseY + 16
        caseYYY = caseYY - 8
        # ax.add_patch(FancyArrowPatch((caseX, caseYY),(-1, caseYYY), arrowstyle='->',mutation_scale=10, lw=1)

        kYY = kY + 3
        kYYY = kYY + 4
        # ax.add_patch(FancyArrowPatch((kX, kYY),(w / 2 - 1.5, kYYY), arrowstyle='->',mutation_scale=10, lw=1))

        kkYY = kY + 3
        ax.add_patch(FancyArrowPatch((kX, kkYY),(w / 2 + 4, 1.5), arrowstyle='->',mutation_scale=10, lw=1))

        ## break in axes
        breakX = d + (L - d) / 2
        hX = 10
        ls = 10
        diag = 5
        ax.add_patch(pylab.Rectangle((x0, breakX - hX / 2), x1 - x0 + 0.0, hX, alpha=1.0, color='white', ec='white', zorder=100, clip_on=False))
        ax.plot((x0 - ls / 2, x0 + ls / 2), (breakX - hX / 2 + diag / 2, breakX - hX / 2 - diag / 2), 'k', clip_on=False, zorder=101)
        ax.plot((x0 - ls / 2, x0 + ls / 2), (breakX + hX / 2 + diag / 2, breakX + hX / 2 - diag / 2), 'k', clip_on=False, zorder=101)
        ax.plot((x1 - ls / 2, x1 + ls / 2), (breakX - hX / 2 + diag / 2, breakX - hX / 2 - diag / 2), 'k', clip_on=False, zorder=101)
        ax.plot((x1 - ls / 2, x1 + ls / 2), (breakX + hX / 2 + diag / 2, breakX + hX / 2 - diag / 2), 'k', clip_on=False, zorder=101)

        if filename:
            pylab.savefig(filename, dpi=200)

if __name__ == '__main__':
    SchematicViewer().plot()
