#!/usr/bin/env python

__docformat__ = 'restructuredtext'

import fipy as fp
from fipy import numerix as nx
import numpy as np
from extremefill.simulation import Simulation

class Pseudo2DSimulation(Simulation):
    r"""

    This class solves the pseudo 2D extreme fill problem modeled with the
    equations below. It can represent either a via or a trench
    geometry depending on the choice of the geometric parameters. It
    is assumed that there is no lateral variation in any of the fields
    and the deposition rate is slow compared with the adjustment of
    the fields. These are gross approximations, but the model
    demonstrates how the critical phenomenon of extreme fill is
    initiated.

    The equations in order of potential, cupric concentration and
    suppressor concentration and surfactant suppressor integrated over
    space.

    .. math::

        \int_{-h}^{\delta}  dz \left[ c_{DL} \frac{\partial \psi}{\partial t} \Theta \left( z \right) =
        \kappa \frac{\partial^2 \psi}{\partial z^2} A \left(z \right) -
        i_F \left(z\right) \Theta \left(z \right)  \right]

    ..
    .. math::

        \int_{-h}^{\delta}  dz  \left[\frac{\partial c_{\text{cu}}}{\partial t} A \left( z \right)  =
        D_{cu} \frac{\partial^2 c_{\text{cu}}}{\partial z^2} A \left(z \right)  -
        \frac{i_F\left(z\right)}{n F} \Theta \left(z \right) \right]

    ..
    .. math::

        \int_{-h}^{\delta}  dz \left[\frac{\partial c_{\theta}}{\partial t} A \left( z \right) =
        D_{\theta} \frac{\partial^2 c_{\theta}}{\partial z^2} A \left(z \right)  -
        \Gamma k^+ c_{\theta} \left(1 - \theta \right)  \Theta \left(z \right)  \right]

    ..
    .. math::

        \int_{-h}^{\delta}  dz \left[\frac{\partial \theta}{\partial t} \Theta \left( z \right) =
        k^+ c_{\theta} \left(1 - \theta \right)  \Theta \left(z \right)  -
        k^- \theta \frac{i_F \Omega}{n F} \Theta \left(z \right) \right]

    where :math:`\Theta\left( z \right) = H\left(- z \right) \frac{l
    \left( z \right)}{A_F} + \delta \left( z \right)\left(1 -
    \frac{A_T}{A_F} \right) + \delta(z + h) \frac{A_T}{A_F}`. The
    cross-sectional area ratio is given by,

    .. math::

       A \left( z \right) = \begin{cases}
       1 & \text{when $z > 0$,} \\
       \frac{A_T}{A_F} & \text{when $z \le 0$,}
       \end{cases}

    where :math:`A_F` is the cross-sectional area above of the modeling
    domain and :math:`A_S` is the cross-sectional area in the
    trench/via. The length of the perimeter is given by
    :math:`l\left(z\right)` and is a step-function through 0. Also,
    :math:`\delta\left(z\right)` is the Dirac delta function and
    :math:`H\left(z\right)` is the Heaviside step function with
    :math:`z=-h` at the bottom of the trench.  The current density is
    given by,

    .. math::

        i_F = \frac{c_{\text{cu}}}{c_{\text{cu}}^{\infty}} \left(i_0 + i_{\theta} \theta\right) \left[\exp{\left(\frac{\alpha F \psi}{R T} \right)} -  \exp{\left(-\frac{\left(2 -\alpha\right) F \psi}{R T} \right)}  \right]

    The boundary conditions on the working electrode are
    included in the volume integrals. Additionally,

    .. math::

         \psi = -\eta_{\text{applied}} \;\; & \text{at $z = \delta_{\text{ref}}$} \\
         \psi = -\eta_{\text{applied}} \;\; & \text{at $t = 0$} \\
         c_{\text{cu}} = c_{\text{cu}}^{\infty} \;\; & \text{at $z = \delta$} \\
         c_{\text{cu}} = c_{\text{cu}}^{\infty} \;\; & \text{at $t = 0$} \\
         c_{\theta} = c_{\theta}^{\infty} \;\; & \text{at $z = \delta$} \\
         c_{\theta} = c_{\theta}^{\infty} \;\; & \text{at $t = 0$}\\
         \theta=0 \;\; & \text{at $t = 0$}

    and

    .. math::

         \psi_{\text{ref}} = \psi\left(0\right) \left(1 - \frac{\delta_{\text{ref}}}{\delta}\right)

    The following code compares the full 1D feature model (but with no
    feature) with the simple 1D ODE for solving the electrical equation
    with no suppressor and no cupric depeletion.

    >>> i0 = 40.
    >>> alpha = 0.4
    >>> F = 9.6485e4 ## C / mol = J / V / mol
    >>> R = 8.314 ## J / K / mol
    >>> T = 298. ## K
    >>> appliedPotential = -0.275
    >>> simulation = Pseudo2DSimulation()
    >>> simulation.run(delta=100e-6,
    ...                deltaRef=200e-6,
    ...                featureDepth=0.0,
    ...                i0=i0,
    ...                i1=0.0,
    ...                diffusionCupric=1e+10,
    ...                appliedPotential=appliedPotential,
    ...                faradaysConstant=F,
    ...                gasConstant=R,
    ...                alpha=alpha,
    ...                temperature=T,
    ...                totalSteps=20,
    ...                dt=.5e-7,
    ...                dtMax=.5e-7,
    ...                sweeps=5)

    >>> from extremefill.simulation1DODE import Simulation1DODE
    >>> timesScipy, potentialsScipy = Simulation1DODE().run(deltaRef=200e-6, totalSteps=20)
    >>> print np.allclose(simulation.parameters['potentials'], potentialsScipy, atol=1e-4)
    True

    >>> ##import pylab
    >>> ##pylab.figure()
    >>> ##pylab.plot(timesScipy, simulation.parameters['potentials'], timesScipy, potentialsScipy)
    >>> ##pylab.ylabel(r'$\phi\left(0\right)$ (V)')
    >>> ##pylab.xlabel(r'$t$ (s)')
    >>> ##pylab.savefig('FiPyVScipy.png')
    >>> ##raw_input('stopped')

    Agreement is good for :math:`\psi`.

    .. image:: FiPyVScipy.*
       :width: 50%
       :align: center
       :alt: comparison of FiPy and SciPy for the potential equation

    Another test is to check that the steady state cupric concentration is
    correct in the absence of any suppressor.

    >>> delta = 150e-6
    >>> D = 5.6e-10
    >>> charge = 2
    >>> cinf = 1000.

    >>> simulation = Pseudo2DSimulation()
    >>> simulation.run(featureDepth=0.0,
    ...                i0=i0,
    ...                alpha=alpha,
    ...                i1=0.0,
    ...                view=False,
    ...                dt=1e-6,
    ...                dtMax=10.,
    ...                totalSteps=200,
    ...                PRINT=False,
    ...                appliedPotential=appliedPotential,
    ...                faradaysConstant=F,
    ...                gasConstant=R,
    ...                delta=delta,
    ...                diffusionCupric=D,
    ...                charge=charge,
    ...                bulkCupric=cinf)

    >>> def iF0():
    ...     Fbar = F / R / T
    ...     V = simulation.parameters['potentials'][-1] 
    ...     return i0 * (np.exp(-alpha * Fbar * V) - np.exp((2 - alpha) * Fbar * V))

    >>> cupric = simulation.parameters['cupric']
    >>> print np.allclose(1 / (1 + iF0() * delta / D / charge / F / cinf), cupric[0] / cinf, rtol=1e-3)
    True

    """

    def getDistanceBelowTrench(self, delta):
        return 0.

    def getTheta(self, mesh, name, distance):
        theta = fp.CellVariable(mesh=mesh, hasOld=True, name=name)
        return theta, theta

    def getCoeffs(self, distance, perimeterRatio, areaRatio, featureDepth):
        mesh = distance.mesh
        dx = mesh.dx
        def dirac(x):
            value = nx.zeros(distance.mesh.numberOfCells, 'd')
            ID = nx.argmin(abs(mesh.x - x))
            if mesh.x[ID] < x:
                ID = ID + 1
            value[ID] = 1. / dx
            return value

        THETA = (mesh.x < 0) * perimeterRatio + dirac(0) * (1 - areaRatio) + dirac(-featureDepth) * areaRatio
        AREA = (mesh.x < 0) * (areaRatio - 1) + 1 

        return THETA, AREA, 1.

    def getThetaEq(self, depositionRate, dt, kPlus, suppressor, distance, surface, kMinus, theta):
        epsilon = 1e-30
        return fp.TransientTerm(surface + epsilon) == kPlus * suppressor * surface \
          - fp.ImplicitSourceTerm(surface * (kPlus * suppressor + kMinus * depositionRate))

    def getThetaDt(self, dt):
        return dt

    def calcDistanceFunction(self, distance):
        pass

    def getMesh(self, *args):
        return self.getMesh1D(*args)
    
if __name__ == '__main__':
    import doctest
    doctest.testmod()


