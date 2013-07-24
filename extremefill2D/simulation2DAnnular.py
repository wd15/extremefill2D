import fipy as fp
from extremefill2D.simulation2D import Simulation2D
import fipy.tools.numerix as nx
import numpy as np

class Simulation2DAnnular(Simulation2D):
    def getMesh(self, Nx, featureDepth, perimeterRatio, delta):
        r"""
        perimeterRatio = 2 / R, where R is the boundary radius
        perimeterRatio = perimeter / a_s
        perimeter = 2 * pi * R
        area = pi * R**2
        """

        distanceBelowTrench = self.getDistanceBelowTrench(delta)
        L = delta + featureDepth + distanceBelowTrench
        ny = Nx
        dy = L / Nx
        dx = dy
        R = 2. / perimeterRatio
        nx = int(R / dx)
        return fp.CylindricalGrid2D(nx=nx, dx=dx, ny=ny, dy=dy) - [[0], [distanceBelowTrench + featureDepth]]

    def get1DVars(self, interfaceTheta, suppressorBar, cbar, potentialBar, distance):
        mesh2D = interfaceTheta.mesh
        mesh1D = fp.Grid1D(nx=mesh2D.ny, dx=mesh2D.dy) + mesh2D.origin[[1]]
        vars2D = super(Simulation2D, self).get1DVars(interfaceTheta, suppressorBar, cbar, potentialBar)
        listOfVars = [_Interpolate1DVarMax(mesh1D, vars2D[0], distance)]
        return listOfVars + [_Interpolate1DVar(mesh1D, v, distance) for v in vars2D[1:]]

class _Interpolate1DVarBase(fp.CellVariable):
    def __init__(self, mesh, var2D, distance):
        super(_Interpolate1DVarBase, self).__init__(mesh=mesh, name=var2D.name)
        self.var2D = self._requires(var2D)
        self.distance = distance
        
class _Interpolate1DVar(_Interpolate1DVarBase):
    def _calcValue(self):
        value = self.var2D([nx.zeros(self.mesh.nx), self.mesh.x])
        phi = self.distance([nx.zeros(self.mesh.nx), self.mesh.x,])
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
