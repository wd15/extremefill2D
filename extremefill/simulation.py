#!/usr/bin/env python

__docformat__ = 'restructuredtext'

import fipy as fp
from fipy import numerix as nx

class Simulation(object):
    r"""
    This is an abstract base class. Please use one of it's children.    
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
            featureDepth=56e-6,
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
          - `featureDepth`: depth of the feature
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

        distanceBelowTrench = self.getDistanceBelowTrench(delta)
        L = delta + featureDepth + distanceBelowTrench
        N = 1000
        dx = L / N 
        mesh = fp.Grid1D(nx=N, dx=dx) - [[distanceBelowTrench + featureDepth]]

        dt = fp.Variable(dt)

        potential = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$\psi$')
        potential[:] = -appliedPotential

        cupric = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$c_{cu}$')
        cupric[:] = bulkCupric
        cupric.constrain(bulkCupric, mesh.facesRight)
        
        suppressor = fp.CellVariable(mesh=mesh, hasOld=True, name=r'$c_{\theta}$')
        suppressor[:] = bulkSuppressor
        suppressor.constrain(bulkSuppressor, mesh.facesRight)

        distance = fp.DistanceVariable(mesh=mesh)
        distance[:] = 1.
        distance.setValue(-1., where=mesh.x < -featureDepth)     

        theta, interfaceTheta = self.getTheta(mesh, r'$\theta$', distance)

        I0 = (i0 + i1 * interfaceTheta)
        baseCurrent = I0 * (nx.exp(alpha * Fbar * potential) \
                                - nx.exp(-(2 - alpha) * Fbar * potential))
        cbar =  cupric / bulkCupric
        current = cbar * baseCurrent
        currentDerivative = cbar * I0 * (alpha * Fbar *  nx.exp(alpha * Fbar * potential) \
                                             + (2 - alpha) * Fbar * nx.exp(-(2 - alpha) * Fbar * potential))

        upper = fp.CellVariable(mesh=mesh)
        upper[-1] = kappa / dx / (deltaRef - delta)

        surface, area, harmonic = self.getCoeffs(distance, perimeterRatio, areaRatio, featureDepth)
        
        potentialEq = fp.TransientTerm(capacitance * surface + (distance < 0)) == \
          fp.DiffusionTerm(kappa * area * harmonic) \
          - surface * (current - potential * currentDerivative) \
          - fp.ImplicitSourceTerm(surface * currentDerivative) \
          - upper * appliedPotential - fp.ImplicitSourceTerm(upper) 
            
        cupricEq = fp.TransientTerm(area) == fp.DiffusionTerm(diffusionCupric * area * harmonic) \
          - fp.ImplicitSourceTerm(baseCurrent * surface / (bulkCupric * charge * faradaysConstant))

        suppressorEq = fp.TransientTerm(area) == fp.DiffusionTerm(diffusionSuppressor * area * harmonic) \
          - fp.ImplicitSourceTerm(gamma * kPlus * (1 - interfaceTheta) * surface)

        depositionRate = current * omega / charge / faradaysConstant
        thetaEq = self.getThetaEq(depositionRate, dt, kPlus, suppressor, distance, surface, kMinus, theta)
        
        t = 0.

        if view:
            potentialBar = -potential / appliedPotential
            potentialBar.name = r'$\bar{\eta}$'
            cbar.name = r'$\bar{c_{cu}}$'
            suppressorBar = suppressor / bulkSuppressor
            suppressorBar.name = r'$\bar{c_{\theta}}$'

            viewer = fp.Viewer((interfaceTheta, suppressorBar, cbar, potentialBar), datamax=1, datamin=0.0)

        potentials = []
        for step in range(totalSteps):
            if view:
                viewer.axes.set_title(r'$t=%1.2e$' % t)
                viewer.plot()

            potential.updateOld()
            cupric.updateOld()
            suppressor.updateOld()
            theta.updateOld()

            self.calcDistanceFunction(distance)

            for sweep in range(sweeps):
                potentialRes = potentialEq.sweep(potential, dt=dt)
                cupricRes = cupricEq.sweep(cupric, dt=dt)
                suppressorRes = suppressorEq.sweep(suppressor, dt=dt)
                thetaRes = thetaEq.sweep(theta, dt=self.getThetaDt(dt))
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
        self.parameters['theta'] = nx.array(interfaceTheta)
        self.parameters['potentials'] = nx.array(potentials)

        self.parameters['potential0'] = nx.array(potential([[dx / 2]]))
        self.parameters['cupric0'] = nx.array(cupric([[dx / 2]]))
        self.parameters['suppressor0'] = nx.array(suppressor([[dx / 2]]))
        self.parameters['theta0'] = nx.array(interfaceTheta([[dx / 2]]))

    def getDistanceBelowTrench(self, delta):
        raise NotImplementedError

    def getTheta(self, mesh, name):
        raise NotImplementedError

    def getCoeffs(self, distance, perimeterRatio, areaRatio, featureDepth):
        raise NotImplementedError

    def getThetaEq(self, depositionRate, dt, kPlus, suppressor, distance, surface, kMinus, theta):
        raise NotImplementedError

    def getThetaDt(self, dt):
        raise NotImplementedError

    def calcDistanceFunction(self, distance):
        raise NotImplementedError
    
if __name__ == '__main__':
    import doctest
    doctest.testmod()


