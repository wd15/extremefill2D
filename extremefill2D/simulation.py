#!/usr/bin/env python

__docformat__ = 'restructuredtext'

import fipy as fp
from fipy import numerix as nx
import numpy as np
from extremefill2D.dicttable import DictTable

class Simulation(object):
    r"""
    This is an abstract base class. Please use one of it's children.    
    """

    def run(self,
            dt=.5e-7,
            dtMax=1e+20,
            dtMin=.5e-7,
            totalSteps=1e+10,
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
            capacitance=0.3,
            Nx=1000,
            CFL=None,
            dataFile=None,
            totalTime=1e+100,
            narrow_distance=None,
            data_frequency=1,
            NxBase=1000,
            solver_tol=1e-10):
        
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
          - `Nx`: number of grid points in the x-direction
          - `CFL`: CFL number
          - `narrow_distance` : distance front covers before reinitializing
          - `NxBase`: number of grid points used for level set initialization
        """

        Fbar = faradaysConstant / gasConstant / temperature
        self.parameters = locals().copy()
        del self.parameters['self']
        self.parameters['trenchWidth'] = 2 * 0.093 / perimeterRatio
        self.parameters['fieldWidth'] = 2 / perimeterRatio

        mesh = self.getMesh(Nx, featureDepth, perimeterRatio, delta)

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
        self.initializeDistance(distance, featureDepth, perimeterRatio, delta, areaRatio, NxBase)

        extension = fp.CellVariable(mesh=mesh)
            
        theta, interfaceTheta = self.getTheta(mesh, r'$\theta$', distance)

        I0 = (i0 + i1 * interfaceTheta)
        baseCurrent = I0 * (nx.exp(alpha * Fbar * potential) \
                                - nx.exp(-(2 - alpha) * Fbar * potential))
        cbar =  cupric / bulkCupric
        current = cbar * baseCurrent
        currentDerivative = cbar * I0 * (alpha * Fbar *  nx.exp(alpha * Fbar * potential) \
                                             + (2 - alpha) * Fbar * nx.exp(-(2 - alpha) * Fbar * potential))

        upper = fp.CellVariable(mesh=mesh)
        ID = mesh._getNearestCellID(mesh.faceCenters[:,mesh.facesRight.value])
        upper[ID] = kappa / mesh.dx / (deltaRef - delta)

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

        if CFL is not None:
            advectionEq = fp.TransientTerm() + fp.AdvectionTerm(extension)
        
        elapsedTime = 0.
        step = 0
        
        potentialBar = -potential / appliedPotential
        potentialBar.name = r'$\bar{\eta}$'
        cbar.name = r'$\bar{c_{cu}}$'
        suppressorBar = suppressor / bulkSuppressor
        suppressorBar.name = r'$\bar{c_{\theta}}$'

        if view:
            viewer = self.getViewer(interfaceTheta, suppressorBar, cbar, potentialBar, distance)
            if CFL is not None:
                distanceViewer = fp.Viewer(distance, datamax=1e-10, datamin=-1e-10)
                extensionViewer = fp.Viewer(extension)

        monitorPoint = nx.zeros((mesh.dim, 1), 'd')
        monitorPoint[0, 0] = mesh.dx / 2.
        
        potentials = []

        potentialSolver = fp.LinearPCGSolver(tolerance=solver_tol)
        cupricSolver = fp.LinearPCGSolver(tolerance=solver_tol)
        suppressorSolver = fp.LinearPCGSolver(tolerance=solver_tol)
        thetaSolver = fp.LinearPCGSolver(tolerance=solver_tol)

        while (step < totalSteps) and (elapsedTime < totalTime):
            
            if view:
                viewer.axes.set_title(r'$t=%1.2e$' % elapsedTime)
                viewer.plot()

            potential.updateOld()
            cupric.updateOld()
            suppressor.updateOld()
            theta.updateOld()

            if dataFile is not None and step % data_frequency == 0:
                self.writeData(dataFile, elapsedTime, distance, step)
            
            if CFL is not None:
                if narrow_distance is None:
                    narrow_distance = featureDepth / 5.
                LSFrequency = int(narrow_distance / mesh.dx / CFL)

                if step % LSFrequency == 0:
                    self.calcDistanceFunction(distance)
                
                extension[:] = depositionRate

                distance.extendVariable(extension)

                if view:
                    distanceViewer.plot()
                    extensionViewer.plot()

                dt.setValue(min(float(CFL * mesh.dx / max(extension.globalValue)), float(dt) * 1.1))
                dt.setValue(min((float(dt), dtMax)))
                dt.setValue(max((float(dt), dtMin)))

                advectionEq.solve(distance, dt=dt)
            else:
                if step == 0:
                    self.calcDistanceFunction(distance)

            for sweep in range(sweeps):

                potentialRes = potentialEq.sweep(potential, dt=dt, solver=potentialSolver)
                cupricRes = cupricEq.sweep(cupric, dt=dt, solver=cupricSolver)
                suppressorRes = suppressorEq.sweep(suppressor, dt=dt, solver=suppressorSolver)
                thetaRes = thetaEq.sweep(theta, dt=self.getThetaDt(dt), solver=thetaSolver)
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
                print
                print 'theta',theta[0]
                print 'cBar_supp',suppressor[0] / bulkSuppressor
                print 'cBar_cu',cupric[0] / bulkCupric
                print 'potentialBar',-potential[0] / appliedPotential
                print 'min(extension)',min(extension)
                print 'min(depositionRate)',min(depositionRate)
                print 'min(current)',min(current)
                print 'min(cupric)',min(cupric)
                print 'min(baseCurrent)',min(baseCurrent)
                print 'max(interfaceTheta) - 1:',max(interfaceTheta) - 1
                print 'min(interfaceTheta)',min(interfaceTheta)
                print 'min(I0)',min(I0)
                print 'dt',dt
                print 'elapsed time',elapsedTime
                print 'step',step
                print

            elapsedTime += float(dt)

            if CFL is None:
                dt.setValue(float(dt) * 1e+10)
                dt.setValue(min((float(dt), dtMax)))
                dt.setValue(max((float(dt), dtMin)))

            step += 1
                
            potentials.append(-float(potential(monitorPoint)))

        if view:
            viewer.plot()

        self.parameters['potential'] = nx.array(potential)
        self.parameters['cupric'] = nx.array(cupric)
        self.parameters['suppressor'] = nx.array(suppressor)
        self.parameters['theta'] = nx.array(interfaceTheta)
        self.parameters['potentials'] = nx.array(potentials)

        self.parameters['potential0'] = nx.array(potential(monitorPoint))
        self.parameters['cupric0'] = nx.array(cupric(monitorPoint))
        self.parameters['suppressor0'] = nx.array(suppressor(monitorPoint))
        self.parameters['theta0'] = nx.array(interfaceTheta(monitorPoint))

        self.vars1D = self.get1DVars(interfaceTheta, suppressorBar, cbar, potentialBar, distance)

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

    def getMesh(self, Nx, featureDepth, perimeterRatio, delta):
        raise NotImplementedError

    def get1DVars(self, interfaceTheta, suppressorBar, cbar, potentialBar, *args):
        return [interfaceTheta, suppressorBar, cbar, potentialBar]
    
    def getViewer(self, *args):
        return fp.Viewer(self.get1DVars(*args), datamax=1.0, datamin=0.0)

    def getMesh1D(self, Nx, featureDepth, perimeterRatio, delta):
        distanceBelowTrench = self.getDistanceBelowTrench(delta)
        L = delta + featureDepth + distanceBelowTrench
        dx = L / Nx
        return fp.Grid1D(nx=Nx, dx=dx) - [[distanceBelowTrench + featureDepth]] 

    def writeData(self, dataFile, elapsedTime, distance, timeStep):
        h5data = DictTable(dataFile, 'a')
        mesh = distance.mesh
        dataDict = {'elapsedTime' : elapsedTime,
                    'nx' : mesh.nx,
                    'ny' : mesh.ny,
                    'dx' : mesh.dx,
                    'dy' : mesh.dy,
                    'distance' : np.array(distance)}

        h5data[timeStep] = dataDict

    def initializeDistance(self, distance, featureDepth, perimeterRatio, delta, areaRatio, NxBase):
        distance[:] = 1.        
        mesh = distance.mesh
        distance.setValue(-1., where=mesh.x < -featureDepth)
        if hasattr(mesh, 'y'):
            distance.setValue(-1., where=(mesh.x < 0) & (mesh.y > areaRatio / perimeterRatio))

        
if __name__ == '__main__':
    import doctest
    doctest.testmod()
