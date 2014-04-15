import numpy as np


from fipy.meshes.cylindricalNonUniformGrid2D import CylindricalNonUniformGrid2D


class ExtremeFill2DMesh(CylindricalNonUniformGrid2D):
    def __init__(self, params):
        dy = params.featureDepth / params.Nx
        dx = dy
        distanceBelowTrench = 10 * dx
        padding = 3 * dx

        dx_nonuniform = self.get_nonuniform_dx(dx, params.rinner,
                                               params.router,
                                               params.rboundary, padding,
                                               params.spacing_ratio)
        
        dy_nonuniform = self.get_nonuniform_dx(dy, distanceBelowTrench,
                                               distanceBelowTrench + params.featureDepth,
                                               distanceBelowTrench + params.featureDepth + params.delta,
                                               padding,
                                               params.spacing_ratio)

        origin = -np.array([[-dx / 100.], [distanceBelowTrench + params.featureDepth]])
        super(ExtremeFill2DMesh, self).__init__(dx=dx_nonuniform, dy=dy_nonuniform, origin=origin)
        #self = self - [[-dx / 100.], [distanceBelowTrench + params.featureDepth]]
        self.nominal_dx = dx

    def get_nonuniform_dx(self, dx, x0, x1, x2, padding, spacing_ratio=1.1):
        """

        Calculate the geometric grid spacing for a grid with an fine grid
        between `r0` and `r1` and a coarse grid elsewhere.

        """
        assert (x2 - x1) > padding

        inner_padding = min(padding, x0)
        dx0 = self.geometric_spacing(dx, x0 - inner_padding, spacing_ratio)[::-1]

        Lx = x1 - x0 + padding + inner_padding
        nx = int(Lx / dx)
        dx1 = (Lx / nx) * np.ones(nx)

        dx2 = self.geometric_spacing(dx, x2 - (x1 + padding), spacing_ratio)

        return np.concatenate((dx0, dx1, dx2))

    def geometric_spacing(self, initial_spacing, domain_size, spacing_ratio=1.1):
        """

        Caculate grid spacing in one dimension using the inital grid cell
        size given by `initial_spacing`. The grid cells are scaled up by
        `spacing_ratio` and `spacing ratio` must be greater than 1.

        """
        assert spacing_ratio > 1.
        r = spacing_ratio
        L = domain_size
        dx = initial_spacing
        nx = int(np.log(1 - L * (1 - r) / dx) / np.log(r))
        Lestimate = dx * (1 - r**nx) / (1 - r)
        spacing = initial_spacing * spacing_ratio**np.arange(nx)
        if len(spacing) > 0:
            spacing[-1] = spacing[-1] + (L - Lestimate)
        return spacing
