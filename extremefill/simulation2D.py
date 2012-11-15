#!/usr/bin/env python

__docformat__ = 'restructuredtext'

import fipy as fp
import fipy.tools.numerix as nx
from extremefill.simulationXD import SimulationXD
import numpy as np

class Simulation2D(SimulationXD):
    r"""

    This class solves the 2D extreme fill problem modeled with the
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
    >>> simulation = Simulation2D()
    >>> simulation.run(featureDepth=0.0,
    ...                delta=100e-6,
    ...                deltaRef=200e-6,
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
    ...                sweeps=5,
    ...                Nx=100)

    >>> from extremefill.simulation1DODE import Simulation1DODE
    >>> timesScipy, potentialsScipy = Simulation1DODE().run(deltaRef=200e-6, totalSteps=20)
    >>> print np.allclose(simulation.parameters['potentials'], potentialsScipy, atol=1e-4)
    True

    Another test is to check that the steady state cupric concentration is
    correct in the absence of any suppressor.
    
    >>> delta = 150e-6
    >>> D = 5.6e-10
    >>> charge = 2
    >>> cinf = 1000.

    >>> simulation = Simulation2D()
    >>> simulation.run(featureDepth=0.0,
    ...                i0=i0,
    ...                alpha=alpha,
    ...                i1=0.0,
    ...                view=False,
    ...                dt=1e-6,
    ...                dtMax=10.,
    ...                totalSteps=20,
    ...                PRINT=False,
    ...                appliedPotential=appliedPotential,
    ...                faradaysConstant=F,
    ...                gasConstant=R,
    ...                delta=delta,
    ...                diffusionCupric=D,
    ...                charge=charge,
    ...                bulkCupric=cinf,
    ...                Nx=100)

    >>> def iF0():
    ...     Fbar = F / R / T
    ...     V = simulation.parameters['potentials'][-1] 
    ...     return i0 * (np.exp(-alpha * Fbar * V) - np.exp((2 - alpha) * Fbar * V))

    >>> cupric0 = simulation.parameters['cupric0']

    >>> print np.allclose(1 / (1 + iF0() * delta / D / charge / F / cinf), cupric0 / cinf, rtol=1e-3)
    True

    The full base line simulation for a flat substrate.
    
    >>> simulation = Simulation2D()
    >>> simulation.run(view=False, totalSteps=1, sweeps=100, dt=1e+20, tol=1e-4, kPlus=25., featureDepth=0., Nx=100)

    >>> from extremefill.pseudo2DSimulation import Pseudo2DSimulation
    >>> pseudo2DSimulation = Pseudo2DSimulation()
    >>> pseudo2DSimulation.run(view=False, totalSteps=1, sweeps=100, dt=1e+20, tol=1e-4, kPlus=25., featureDepth=0., Nx=100)

    >>> print np.allclose(simulation.parameters['cupric0'], pseudo2DSimulation.parameters['cupric0'], rtol=1e-3)
    True
    
    >>> print np.allclose(simulation.parameters['theta0'], pseudo2DSimulation.parameters['theta0'], rtol=1e-3)
    True

    Test for the static 2D case but with an actual trench.

    >>> pseudo2Dsimulation = Pseudo2DSimulation()
    >>> pseudo2Dsimulation.run(totalSteps=1, sweeps=1, dt=1e+20, tol=1e-4, kPlus=25., Nx=1000)

    >>> simulation = Simulation2D()
    >>> simulation.run(totalSteps=1, sweeps=1, dt=1e+20, tol=1e-4, kPlus=25., Nx=1000)

    >>> def norm(v, vPseudo):
    ...     return np.sqrt(((v(vPseudo.mesh.cellCenters) - vPseudo)**2 ).sum() / v.mesh.nx )
    >>> print (np.array([norm(v, vPseudo) for v, vPseudo in zip(simulation.vars1D, pseudo2Dsimulation.vars1D)]) < 1e-2).all()
    True
    
    """

    def getMesh(self, Nx, dx, distanceBelowTrench, featureDepth, perimeterRatio):
        Ny = int(1 / perimeterRatio / dx)
        return fp.Grid2D(nx=Nx, dx=dx, ny=Ny, dy=dx) - [[distanceBelowTrench + featureDepth], [0]]

    def get1DVars(self, interfaceTheta, suppressorBar, cbar, potentialBar, distance):
        mesh2D = interfaceTheta.mesh
        mesh1D = fp.Grid1D(nx=mesh2D.nx, dx=mesh2D.dx) + mesh2D.origin[[0]]
        vars2D = super(self.__class__, self).get1DVars(interfaceTheta, suppressorBar, cbar, potentialBar)
        listOfVars = [_Interpolate1DVarMax(mesh1D, vars2D[0], distance)]
        return listOfVars + [_Interpolate1DVar(mesh1D, v, distance) for v in vars2D[1:]]

class _Interpolate1DVarBase(fp.CellVariable):
    def __init__(self, mesh, var2D, distance):
        super(_Interpolate1DVarBase, self).__init__(mesh=mesh, name=var2D.name)
        self.var2D = self._requires(var2D)
        self.distance = distance
        
class _Interpolate1DVar(_Interpolate1DVarBase):
    def _calcValue(self):
        value = self.var2D([self.mesh.x, nx.zeros(self.mesh.nx)])
        phi = self.distance([self.mesh.x, nx.zeros(self.mesh.nx)])
        value[phi < 0] = 0.
        return value

class _Interpolate1DVarMax(_Interpolate1DVarBase):
    def _calcValue(self):
        value = np.zeros(self.mesh.nx, 'd')
        inty = self.var2D.mesh.y[::self.var2D.mesh.nx]
        onesy = np.ones(self.var2D.mesh.ny, 'd')
        for i, x in enumerate(self.mesh.x):
            value[i] = np.max(self.var2D([x * onesy, inty]))
        return value
            
if __name__ == '__main__':
    import doctest
    doctest.testmod()


