#!/usr/bin/env python

r"""

This example is the 1D solution, but with a via or trench, where we
assume that there is no lateral variation in any of the fields and the
deposition rate is negligible. Let's start with the equations in order
of potential, cupric concentration and suppressor concentration and
surfactant supressor integrated over space.

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

>>> import numpy

>>> i0 = 40.
>>> alpha = 0.4
>>> F = 9.6485e4 ## C / mol = J / V / mol
>>> R = 8.314 ## J / K / mol
>>> T = 298. ## K
>>> appliedPotential = -0.275

>>> times, potentials = feature(delta=100e-6,
...                             deltaRef=50e-6,
...                             featureDepth=0.0,
...                             i0=i0,
...                             i1=0.0,
...                             diffusionCupric=1e+10,
...                             relaxation=1,
...                             appliedPotential=appliedPotential,
...                             faradaysConstant=F,
...                             gasConstant=R,
...                             alpha=alpha)[:2]

>>> timesScipy, potentialsScipy = noFeatureODE()
>>> print numpy.allclose(potentials, potentialsScipy, atol=1e-4)
True

>>> ##import pylab
>>> ##pylab.figure()
>>> ##pylab.plot(times, potentials, timesScipy, potentialsScipy)
>>> ##pylab.ylabel(r'$\phi\left(0\right)$ (V)')
>>> ##pylab.xlabel(r'$t$ (s)')
>>> ##pylab.savefig('FiPyVScipy.png')

Agreement is good for :math:`\psi`.

.. image:: FiPyVScipy.*
   :width: 90%
   :align: center
   :alt: comparison of FiPy and SciPy for the potential equation

Another test is to check that the steady state cupric concentration is
correct in the absence of any suppressor.


>>> delta = 150e-6
>>> D = 5.6e-10
>>> charge = 2
>>> cinf = 1000.

>>> times, potentials, cupric = feature(featureDepth=0.0,
...                                     i0=i0,
...                                     alpha=alpha,
...                                     i1=0.0,
...                                     view=True,
...                                     dt=1e-6,
...                                     dtMax=10.,
...                                     totalSteps=200,
...                                     PRINT=True,
...                                     appliedPotential=appliedPotential,
...                                     faradaysConstant=F,
...                                     gasConstant=R,
...                                     delta=delta,
...                                     diffusionCupric=D,
...                                     charge=charge,
...                                     bulkCupric=cinf)

>>> def iF0():
...     Fbar = F / R / T
...     V = potentials[-1] 
...     return i0 * (numpy.exp(-alpha * Fbar * V) - numpy.exp((2 - alpha) * Fbar * V))

>>> print numpy.allclose(1 / (1 + iF0() * delta / D / charge / F / cinf), cupric[0] / cinf, rtol=1e-3)
True

"""
__docformat__ = 'restructuredtext'

from fipy import Grid1D, CellVariable, Variable, numerix, TransientTerm, DiffusionTerm, ImplicitSourceTerm, Viewer

def feature(delta=150e-6,
            deltaRef=0.03,
            featureDepth=56e-6,
            i1=-40.,
            i0=40.,
            diffusionCupric=5.6e-10,
            dt=.5e-7,
            dtMax=.5e-7,
            dtMin=.5e-7,
            totalSteps=200,
            appliedPotential=-0.275,
            view=False,
            PRINT=False,
            relaxation=0.2,
            faradaysConstant=9.6485e4,
            gasConstant=8.314,
            temperature=298.,
            alpha=0.4,
            charge=2,
            bulkCupric=1000.,
            bulkSuppressor=.02,
            diffusionSuppressor=1e-9,
            kappa=15.26,
            kPlus=125.,
            kMinus=2.45e7,
            omega=7.1e-6,
            gamma=2.5e-7):

    Fbar = faradaysConstant / gasConstant / temperature ## 1 / V
    capicatance = 0.3 ## F / m**2 = A s / V / m**2  
    areaRatio = 0.093
    perimeterRatio = 1. / 2.8e-6  
    epsilon = 1e-30

    L = delta + featureDepth
    N = 400
    dx = L / N 
    mesh = Grid1D(nx=N, dx=dx) - [[featureDepth]]

    potential = CellVariable(mesh=mesh, hasOld=True, name=r'$\psi$')
    potential[:] = -appliedPotential

    cupric = CellVariable(mesh=mesh, hasOld=True, name=r'$c_{cu}$')
    cupric[:] = bulkCupric
    cupric.constrain(bulkCupric, mesh.facesRight)

    suppressor = CellVariable(mesh=mesh, hasOld=True, name=r'$c_{\theta}$')
    suppressor[:] = bulkSuppressor
    suppressor.constrain(bulkSuppressor, mesh.facesRight)

    theta = CellVariable(mesh=mesh, hasOld=True, name=r'$\theta$')

    I0 = (i0 + i1 * theta)
    baseCurrent = I0 * (numerix.exp(alpha * Fbar * potential) \
                            - numerix.exp(-(2 - alpha) * Fbar * potential))
    cbar =  cupric / bulkCupric
    current = cbar * baseCurrent
    currentDerivative = cbar * I0 * (alpha * Fbar *  numerix.exp(alpha * Fbar * potential) \
                                         + (2 - alpha) * Fbar * numerix.exp(-(2 - alpha) * Fbar * potential))

    def dirac(x):
        value = numerix.zeros(mesh.numberOfCells, 'd')
        ID = numerix.argmin(abs(mesh.x - x))
        if mesh.x[ID] < x:
            ID = ID + 1
        value[ID] = 1. / dx
        return value

    THETA = (mesh.x < 0) * perimeterRatio + dirac(0) * (1 - areaRatio) + dirac(-featureDepth) * areaRatio 
    AREA = (mesh.x < 0) * (areaRatio - 1) + 1 
    THETA_UPPER = CellVariable(mesh=mesh)
    THETA_UPPER[-1] = kappa / dx / (deltaRef - delta)

    potentialEq = TransientTerm(capicatance * THETA) == DiffusionTerm(kappa * AREA) \
        - THETA * (current - potential * currentDerivative) \
        - ImplicitSourceTerm(THETA * currentDerivative) \
        - THETA_UPPER * appliedPotential - ImplicitSourceTerm(THETA_UPPER) 

    cupricEq = TransientTerm(AREA) == DiffusionTerm(diffusionCupric * AREA) \
        - ImplicitSourceTerm(baseCurrent * THETA / (bulkCupric * charge * faradaysConstant))

    suppressorEq = TransientTerm(AREA) == DiffusionTerm(diffusionSuppressor * AREA) \
        - ImplicitSourceTerm(gamma * kPlus * (1 - theta) * THETA)

    thetaEq =  TransientTerm(THETA + epsilon) == kPlus * suppressor * THETA \
        - ImplicitSourceTerm(THETA * (kPlus * suppressor + kMinus * current * (omega / charge / faradaysConstant)))

    t = 0.
    
    if view:
        viewers = (Viewer(potential, datamax=0, datamin=0.3), Viewer(cupric), Viewer(suppressor), Viewer(theta))

    potentials = []
    times = []

    for step in range(totalSteps):
        potential.updateOld()
        cupric.updateOld()
        suppressor.updateOld()
        theta.updateOld()

        for sweep in range(5):
            potentialRes = potentialEq.sweep(potential, dt=dt)
            cupricRes = cupricEq.sweep(cupric, dt=dt)
            suppressorRes = suppressorEq.sweep(suppressor, dt=dt)
            thetaRes = thetaEq.sweep(theta, dt=dt)
            
            if PRINT:
                print potentialRes, cupricRes, suppressorRes, thetaRes
        
        if view:
            for viewer in viewers:
                viewer.plot()

        if PRINT:
            print 'theta',theta[0]
            print 'cBar_supp',suppressor[0] / bulkSuppressor
            print 'cBar_cu',cupric[0] / bulkCupric
            print 'potentialBar',-potential[0] / appliedPotential
            print 'dt',dt
            print 'step',step

        t += dt
        times += [t]
        potentials += [-potential([[0]])]
        dt = dt * 1.1
        dt = min((dt, dtMax))
        dt = max((dt, dtMin))
##        print 'time',t

    if view:
        for viewer in viewers:
            viewer.plot()
        
    return numerix.array(times), numerix.array(potentials)[:,0], cupric.value

def noFeatureODE():
    import numpy
    delta = 100e-6 ## m
    deltaRef = 50e-6 ## m
    faradaysConstant = 9.6485e4 ## C / mol = J / V / mol
    gasConstant = 8.314 ## J / K / mol
    temperature = 298. ## K
    Fbar = faradaysConstant / gasConstant / temperature ## 1 / V
    alpha = 0.4
    appliedVoltage = -0.275  ## V
    i0 = 40. ## A / m**2 
    capacitance = 0.3 ## F / m**2 = A s / V / m**2  
    kappa = 15.26 ## S / m = A / V / m

    def iF(xi):
        V = appliedVoltage - xi
        return i0 * (numpy.exp(-alpha * Fbar * V) - numpy.exp((2 - alpha) * Fbar * V))

    def iFderivative(xi):
        V = appliedVoltage - xi
        return i0 * (alpha * Fbar * numpy.exp(-alpha * Fbar * V) \
               + (2 - alpha) * Fbar * numpy.exp((2 - alpha) * Fbar * V))

    def RHS(t, y):
        psi = y[0]
        psi0 = (1 - deltaRef / delta) * psi
        return numpy.array((-iF(psi - psi0) / capacitance  - kappa * psi / delta / capacitance,))

    def jacobian(t, y):
        psi = y[0]
        psi0 = (1 - deltaRef / delta) * psi
        return numpy.array((-iFderivative(psi - psi0) / capacitance  - kappa / delta / capacitance,))

    from scipy.integrate import ode
    integrator = ode(RHS, jacobian).set_integrator('vode', method='bdf', with_jacobian=True)
    initialValue = 0 ##appliedVoltage + (delta - deltaRef) / deltaRef * appliedVoltage
    s = integrator.set_initial_value((initialValue,), 0.)

    totalSteps = 200
    dt = .5e-7
    times = numpy.zeros(totalSteps)
    potentialSciPy = numpy.zeros(totalSteps)
    step = 0

    while integrator.successful() and step < totalSteps:
        null = integrator.integrate(integrator.t + dt)
        times[step] = integrator.t
        psi =  integrator.y[0]
        psi0 = (1 - deltaRef / delta) * psi
        potentialSciPy[step] = appliedVoltage - psi + psi0
        step += 1

    return numpy.array(times), numpy.array(potentialSciPy)

if __name__ == '__main__':
    import fipy.tests.doctestPlus
    exec(fipy.tests.doctestPlus._getScript())

