import numpy as np


from fipy.meshes.cylindricalNonUniformGrid2D import CylindricalNonUniformGrid2D


class ExtremeFill2DMesh(CylindricalNonUniformGrid2D):
    """Mesh class for via or annular meshes

    A cylindrical grid which is fine in the region close to the
    feature and coarsens away for the the feature

    The grid is coarsened away from the feature using a geometric
    ratio.
    
    Attributes:
        `nominal_dx`: The ideal value for `dx`. Not the actual value of `dx`
        
    """
    def __init__(self, params):
        """Init for `ExtremeFill2DMesh`.

        Args: 
            params: a class with `Nx`, `rinner`, `router`, `rboundary`,
                `spacing_ratio`, `featureDepth` and `delta` attributes.

        """

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
        """Calculates mesh spacing for a triple layered domain.

        Calculates the spacing for a triple layer domain where the
        central region is fine and the outer regions are coarsened
        geometrically. The domain starts at 0 and extends out

        Args:
            `dx`: the ideal spacing in the fine region
            `x0`: the inner position of the fine region
            `x1`: the outer position of the fine region
            `x2`: the outer extent of the domain
            `padding`: the width of padding where the spacing in fine around the nominal fine region
            `spacing_ratio`: the geometric ration to use when coarsening the mesh
            
        Returns:
            an array of the spacing

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
        """Calculate geometric spacing.

        Calculate grid spacing in one dimension starting with an
        initial spacing and coarsening from right to left
        geometrically.

        Args:
            `initial_spacing`: the left hand fine grid spacing
            `domain_size`: the size of the domain
            `spacing_ration`: the geometric ratio to use for coarsening the mesh

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
