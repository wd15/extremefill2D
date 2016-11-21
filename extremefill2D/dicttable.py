import tables
import os
##import hashlib

class DictTable:
    """
    Designed to save a dictionary of arrays at each timestep in a simulation.
    """
    IDprefix = 'ID'
    def __init__(self, h5filename, mode='a'):
        if mode == 'w' and os.path.exists(h5filename):
            print('removing %s ' %  h5filename)
            os.remove(h5filename)

        self.h5filename = h5filename

    def haskey(self, index):
        h5file = tables.openFile(self.h5filename, mode='a')
        groupName = self.IDprefix + str(index)
        _haskey =  hasattr(h5file.root, groupName)
        h5file.close()
        return _haskey

    def __setitem__(self, index, values):
        h5file = tables.open_file(self.h5filename, mode='a')
        h5file.root._v_attrs.latestIndex = index

        groupName = self.IDprefix + str(index)

        if hasattr(h5file.root, groupName):
            group = h5file.root._f_getChild(groupName)
            group._f_remove(recursive=True)

        group = h5file.create_group(h5file.root, groupName)

        for k in values.keys():
            h5file.create_array(group, k, values[k])

        h5file.close()

    def openread(self):
        if not hasattr(self, 'h5fileread'):
            self.h5fileread = tables.open_file(self.h5filename, mode='r')
        return self.h5fileread

    def __getitem__(self, index):
        h5file = self.openread()

        if type(index) is int:
            index = [index]

        s = '/' + self.IDprefix + str(index[0])

        if len(index) == 1:
            d = {}
            for array in h5file.listNodes(s, classname='Array'):
                d[array.name] = array.read()
        else:
            for t in index[1:]:
                s += '/' + str(t)

            d = h5file.getNode(s, classname='Array').read()

        return d

    def getLatestIndex(self):
        h5file = self.openread()
        latestIndex = h5file.root._v_attrs.latestIndex
        return latestIndex

    def __del__(self):
        if hasattr(self, 'h5fileread'):
            self.h5fileread.close()
            del self.h5fileread
