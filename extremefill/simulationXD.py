from extremefill.simulation import Simulation
import fipy as fp
import numpy as np
from fipy.variables.surfactantVariable import _InterfaceSurfactantVariable

class _InterfaceVar(_InterfaceSurfactantVariable):
    def _calcValue(self):
        return np.minimum(1, super(_InterfaceVar, self)._calcValue())


class SimulationXD(Simulation):
    def getDistanceBelowTrench(self, delta):
        return delta * 0.1

    def getTheta(self, mesh, name, distance):   
        theta = fp.SurfactantVariable(distanceVar=distance, hasOld=True, name=r'$\theta$', value=0.)
        return theta, _InterfaceVar(theta)

    def getCoeffs(self, distance, perimeterRatio, areaRatio, featureDepth):
        return distance.cellInterfaceAreas / distance.mesh.cellVolumes, 1., (distance >= 0).harmonicFaceValue

    def getThetaEq(self, depositionRate, dt, kPlus, suppressor, distance, surface, kMinus, theta):
        adsorptionCoeff = dt * suppressor * kPlus
        thetaEq = fp.TransientTerm() == fp.ExplicitUpwindConvectionTerm(fp.SurfactantConvectionVariable(distance)) \
          + adsorptionCoeff * surface \
          - fp.ImplicitSourceTerm(adsorptionCoeff * distance._cellInterfaceFlag) \
          - fp.ImplicitSourceTerm(kMinus * depositionRate * dt)
          ##        theta.constrain(0, distance.mesh.exteriorFaces)

        return thetaEq

    def getThetaDt(self, dt):
        return 1.

    def calcDistanceFunction(self, distance):
        distance.calcDistanceFunction()
