import os
import tables
import numpy as np


def test_annular():
    datafile = 'annular.h5'
    h5file = tables.openFile(datafile, mode='r')
    index = h5file.root._v_attrs.latestIndex
    data = h5file.getNode('/ID' + str(int(index)))

    rmdatafile = os.path.join('Data', 'data.h5')
    if os.path.exists(rmdatafile):
        os.remove(rmdatafile)

    import annular

    for attr in ['distance', 'potential', 'theta', 'suppressor', 'cupric']:
        test_value = getattr(data, attr).read()
        value = getattr(annular.variables, attr)
        assert np.allclose(test_value, value)

    h5file.close()
