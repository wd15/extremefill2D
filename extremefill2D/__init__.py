import extremefill2D.pseudo2DSimulation
import extremefill2D.simulation1D
import extremefill2D.simulation2D

## figure ordering from the paper

def test():
    r"""
    Run all the doctests available.
    """
    import doctest
    doctest.testmod(extremefill2D.pseudo2DSimulation)
    doctest.testmod(extremefill2D.simulation1D)
    doctest.testmod(extremefill2D.simulation2D)
       

def _getVersion():
    from pkg_resources import get_distribution, DistributionNotFound

    try:
        version = get_distribution(__name__).version
    except DistributionNotFound:
        version = "unknown, try running `python setup.py egg_info`"
        
    return version
    
__version__ = _getVersion()           

