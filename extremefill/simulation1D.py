#!/usr/bin/env python

__docformat__ = 'restructuredtext'

import fipy as fp
from fipy import numerix as nx

class Simulation1D(object):
    r"""

    This class solves the 1D extreme fill problem modeled with the
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

    >>> import numpy as np

    
    >>> i0 = 40.
    >>> alpha = 0.4
    >>> F = 9.6485e4 ## C / mol = J / V / mol
    >>> R = 8.314 ## J / K / mol
    >>> T = 298. ## K
    >>> appliedPotential = -0.275
    >>> simulation = Simulation1D()
    >>> simulation.run(delta=100e-6,
    ...                deltaRef=200e-6,
    ...                i0=i0,
    ...                i1=0.0,
    ...                diffusionCupric=1e+10,
    ...                appliedPotential=appliedPotential,
    ...                faradaysConstant=F,
    ...                gasConstant=R,
    ...                alpha=alpha,
    ...                temperature=T,
    ...                totalSteps=200,
    ...                dt=.5e-7,
    ...                dtMax=.5e-7,
    ...                sweeps=5)

    >>> from simulation1DODE import Simulation1DODE
    >>> timesScipy, potentialsScipy = Simulation1DODE().run(deltaRef=200e-6)
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

    >>> simulation = Simulation1D()
    >>> simulation.run(i0=i0,
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

    >>> cupric0 = simulation.parameters['cupric0']

    >>> print np.allclose(1 / (1 + iF0() * delta / D / charge / F / cinf), cupric0 / cinf, rtol=1e-3)
    True

    """

    def run(self,
            dt=.5e-7,
            dtMax=1e+20,
            dtMin=.5e-7,
            totalSteps=400,
            view=False,
            PRINT=False,
            sweeps=5,
            tol=1e-10,
            delta=150e-6,
            deltaRef=0.03,
            i1=-40.,
            i0=40.,
            diffusionCupric=2.65e-10,
            appliedPotential=-0.25,
            faradaysConstant=9.6485e4,
            gasConstant=8.314,
            temperature=298.,
            alpha=0.4,
            charge=2,
            bulkCupric=1000.,
            bulkSuppressor=.02,
            diffusionSuppressor=9.2e-11,
            kappa=15.26,
            kPlus=150.,
            kMinus=2.45e7,
            omega=7.1e-6,
            gamma=2.5e-7,
            perimeterRatio=1. / 2.8e-6 * 0.093,
            areaRatio=0.093,
            capacitance=0.3):

        r"""
        Run an individual simulation.

        :Parameters:
          - `dt`: time step size
          - `dtMax`: maximum time step size
          - `dtMin`: minimum time step size
          - `totalSteps`: total time steps
          - `view`: whether to view the simulation while running
          - `PRINT`: print convergence data
          - `sweeps`: number of sweeps at each time step
          - `tol`: tolerance to exit sweep loop
          - `delta`: boundary layer depth
          - `deltaRef`: distance to reference electrode
          - `i1`: current density constant
          - `i0`: current density constant
          - `diffusionCupric`: cupric diffusion
          - `appliedPotential`: applied potential
          - `faradaysConstant`: Faraday's constant
          - `gasConstant`: gas constant
          - `temperature`: temperature
          - `alpha`: kinetic factor
          - `charge`: charge
          - `bulkCupric`: bulk cupric concentration
          - `bulkSuppressor`: bulk suppressor concentration
          - `diffusionSuppressor`: suppressor diffusion
          - `kappa`: conductivity
          - `kPlus`: suppressor adsorption factor
          - `kMinus`: suppressor incorporation factor
          - `omega`: copper molar volume
          - `gamma`: saturation suppressor coverage,
          - `perimeterRatio`: feature perimeter ratio
          - `areaRatio`: feature area ratio
          - `capacitance`: capacitance
        """

        Fbar = faradaysConstant / gasConstant / temperature
        self.parameters = locals().copy()
        del self.parameters['self']
        self.parameters['trenchWidth'] = 2 * 0.093 / perimeterRatio
        self.parameters['fieldWidth'] = 2 / perimeterRatio
        
        distanceBelowTrench = delta * 0.1
        L = delta + distanceBelowTrench
        N = 1000
        dx = L / N 
        mesh = fp.Grid1D(nx=N, dx=dx) - [[distanceBelowTrench]]

        dt = fp.Variable(dt)
        
        distance = fp.DistanceVariable(mesh=mesh)
        distance[:] = 1.
        distance.setValue(-1., where=mesh.x < 0)

        potential = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$\psi$')
        potential[:] = -appliedPotential

        cupric = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$c_{cu}$')
        cupric[:] = bulkCupric
        cupric.constrain(bulkCupric, mesh.facesRight)
        
        suppressor = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$c_{\theta}$')
        suppressor[:] = bulkSuppressor
        suppressor.constrain(bulkSuppressor, mesh.facesRight)
        
        theta = fp.SurfactantVariable(distanceVar=distance, hasOld=True, name=r'$\theta$', value=0.)

        I0 = (i0 + i1 * theta.interfaceVar)
        baseCurrent = I0 * (nx.exp(alpha * Fbar * potential) \
                                - nx.exp(-(2 - alpha) * Fbar * potential))
        cbar =  cupric / bulkCupric
        current = cbar * baseCurrent
        currentDerivative = cbar * I0 * (alpha * Fbar *  nx.exp(alpha * Fbar * potential) \
                                             + (2 - alpha) * Fbar * nx.exp(-(2 - alpha) * Fbar * potential))

        upper = fp.CellVariable(mesh=mesh)
        upper[-1] = kappa / dx / (deltaRef - delta)

        surface = distance.cellInterfaceAreas / mesh.cellVolumes
        diffCoeff = (distance >= 0).harmonicFaceValue
        
        potentialEq = fp.TransientTerm(capacitance * surface + (distance < 0)) == \
          fp.DiffusionTerm(kappa * diffCoeff) \
          - surface * (current - potential * currentDerivative) \
          - fp.ImplicitSourceTerm(surface * currentDerivative) \
          - upper * appliedPotential - fp.ImplicitSourceTerm(upper) 
            
        cupricEq = fp.TransientTerm() == fp.DiffusionTerm(diffusionCupric * diffCoeff) \
          - fp.ImplicitSourceTerm(baseCurrent * surface / (bulkCupric * charge * faradaysConstant))

        suppressorEq = fp.TransientTerm() == fp.DiffusionTerm(diffusionSuppressor * diffCoeff) \
          - fp.ImplicitSourceTerm(gamma * kPlus * (1 - theta.interfaceVar) * surface)

        depositionRate = current * omega / charge / faradaysConstant
        adsorptionCoeff = dt * suppressor * kPlus
        thetaEq = fp.TransientTerm() == fp.ExplicitUpwindConvectionTerm(fp.SurfactantConvectionVariable(distance)) \
          + adsorptionCoeff * surface \
          - fp.ImplicitSourceTerm(adsorptionCoeff * distance._cellInterfaceFlag) \
          - fp.ImplicitSourceTerm(kMinus * depositionRate * dt)
        theta.constrain(0, mesh.exteriorFaces)

        t = 0.

        if view:
            potentialBar = -potential / appliedPotential
            potentialBar.name = r'$\bar{\eta}$'
            cbar.name = r'$\bar{c_{cu}}$'
            suppressorBar = suppressor / bulkSuppressor
            suppressorBar.name = r'$\bar{c_{\theta}}$'

            viewer = fp.Viewer((theta.interfaceVar, suppressorBar, cbar, potentialBar), datamax=1, datamin=0.0)

        potentials = []
        for step in range(totalSteps):
            if view:
                viewer.axes.set_title(r'$t=%1.2e$' % t)
                viewer.plot()

            potential.updateOld()
            cupric.updateOld()
            suppressor.updateOld()
            theta.updateOld()
            
            distance.calcDistanceFunction()

            for sweep in range(sweeps):
                potentialRes = potentialEq.sweep(potential, dt=dt)
                cupricRes = cupricEq.sweep(cupric, dt=dt)
                suppressorRes = suppressorEq.sweep(suppressor, dt=dt)
                thetaRes = thetaEq.sweep(theta, dt=1.)
                res = nx.array((potentialRes, cupricRes, suppressorRes, thetaRes))

                if sweep == 0:
                    res0 = res
                else:
                    if ((res / res0) < tol).all():
                        break
                    
                if PRINT:
                    print res / res0

            if sweep == sweeps - 1 and PRINT:
                print 'Did not reach sufficient tolerance'
                print 'kPlus',kPlus
                print 'kMinus',kMinus
                print 'res',res

            if PRINT:
                print 'theta',theta[0]
                print 'cBar_supp',suppressor[0] / bulkSuppressor
                print 'cBar_cu',cupric[0] / bulkCupric
                print 'potentialBar',-potential[0] / appliedPotential
                print 'dt',dt
                print 'step',step

            t += float(dt)

            dt.setValue(float(dt) * 1e+10)
            dt.setValue(min((float(dt), dtMax)))
            dt.setValue(max((float(dt), dtMin)))
            
            potentials.append(-float(potential([[dx / 2]])))
        if view:
            viewer.plot()

        self.parameters['potential'] = nx.array(potential)
        self.parameters['cupric'] = nx.array(cupric)
        self.parameters['suppressor'] = nx.array(suppressor)
        self.parameters['theta'] = nx.array(theta)
        self.parameters['potentials'] = nx.array(potentials)
        self.parameters['cupric0'] = nx.array(cupric([[dx / 2]]))

if __name__ == '__main__':
    import doctest
    doctest.testmod()


