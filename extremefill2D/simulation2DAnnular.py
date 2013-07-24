import fipy as fp
from extremefill2D.simulation2D import Simulation2D
import fipy.tools.numerix as numerix
import numpy as np

class Simulation2DAnnular(Simulation2D):
    def run(self, router=None, rinner=None, rboundary=None, **kwargs):
        self.rboundary = rboundary
        self.rinner = rinner
        self.router = router
        super(Simulation2DAnnular, self).run(**kwargs)

    def getMesh(self, Nx, featureDepth, perimeterRatio, delta):
        distanceBelowTrench = self.getDistanceBelowTrench(delta)
        L = delta + featureDepth + distanceBelowTrench
        ny = Nx
        dy = L / Nx
        dx = dy
        nx = int(self.rboundary / dx)
        mesh = fp.CylindricalGrid2D(nx=nx, dx=dx, ny=ny, dy=dy) - [[-dx / 100.], [distanceBelowTrench + featureDepth]]
        mesh.bulkBoundaryFaces = mesh.facesTop
        return mesh

    def get1DVars(self, interfaceTheta, suppressorBar, cbar, potentialBar, distance):
        mesh2D = interfaceTheta.mesh
        mesh1D = fp.Grid1D(nx=mesh2D.ny, dx=mesh2D.dy) + mesh2D.origin[[1]]
        vars2D = super(Simulation2D, self).get1DVars(interfaceTheta, suppressorBar, cbar, potentialBar)
        listOfVars = [_Interpolate1DVarMax(mesh1D, vars2D[0], distance)]
        return listOfVars + [_Interpolate1DVar(mesh1D, v, distance) for v in vars2D[1:]]

    def initializeDistance(self, distance, featureDepth, perimeterRatio, delta, areaRatio, NxBase):
        baseMesh = self.getMesh(NxBase, featureDepth, perimeterRatio, delta)
        baseDistance = fp.DistanceVariable(mesh=baseMesh)
        self._initializeDistance(baseDistance, featureDepth, perimeterRatio, delta, areaRatio, NxBase)
        baseDistance.calcDistanceFunction()
        value = np.array(baseDistance(distance.mesh.cellCenters, order=1))
        distance.setValue(value)

    def _initializeDistance(self, distance, featureDepth, perimeterRatio, delta, areaRatio, NxBase):
        distance[:] = 1.        
        mesh = distance.mesh
        distance.setValue(-1., where=mesh.y < -featureDepth)
        distance.setValue(-1., where=(mesh.y < 0) & (mesh.x < self.rinner))        
        distance.setValue(-1., where=(mesh.y < 0) & (mesh.x > self.router))

class _Interpolate1DVarBase(fp.CellVariable):
    def __init__(self, mesh, var2D, distance):
        super(_Interpolate1DVarBase, self).__init__(mesh=mesh, name=var2D.name)
        self.var2D = self._requires(var2D)
        self.distance = distance
        
class _Interpolate1DVar(_Interpolate1DVarBase):
    def _calcValue(self):
        value = self.var2D([numerix.zeros(self.mesh.nx), self.mesh.x])
        phi = self.distance([numerix.zeros(self.mesh.nx), self.mesh.x,])
        value[phi < 0] = 0.
        return value

class _Interpolate1DVarMax(_Interpolate1DVarBase):
    def _calcValue(self):
        value = np.zeros(self.mesh.nx, 'd')
        intx = self.var2D.mesh.x[:self.var2D.mesh.nx]
        onesx = np.ones(self.var2D.mesh.nx, 'd')
        for i, y in enumerate(self.mesh.x):
            value[i] = np.max(self.var2D([intx, y * onesx]))
        return value
