import fipy as fp
from extremefill2D.simulation2D import Simulation2D

class Simulation2DNoSymmetry(Simulation2D):

    def getMesh(self, Nx, featureDepth, perimeterRatio, delta):
        distanceBelowTrench = self.getDistanceBelowTrench(delta)
        L = delta + featureDepth + distanceBelowTrench
        dx = L / Nx
        Ny = int(1 / perimeterRatio / dx) * 2
        return fp.Grid2D(nx=Nx, dx=dx, ny=Ny, dy=dx) - [[distanceBelowTrench + featureDepth], [Ny * dx / 2]]


