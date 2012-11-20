from extremefill.dicttable import DictTable
import pylab
import numpy as np

def getNormData():
    basedata = DictTable("cfl0.05.h5", 'r')
    data0 = DictTable("cfl0.1.h5", 'r')
    data1 = DictTable("cfl0.2.h5", 'r')
    norms = []
    times = []
    latestIndex = basedata.getLatestIndex()
    for index in xrange(0, latestIndex, 10):
        print 'index',index
        elapsedTime = basedata[index]['elapsedTime']
        phiBase = basedata[index]['distance']
        norm0 = getNorm(data0, elapsedTime, phiBase)
        norm1 = getNorm(data1, elapsedTime, phiBase)
        norms.append([norm0, norm1])
        times.append(elapsedTime)

    return np.array(times), np.array(norms)
        
def getNorm(data, elapsedTime, phiBase):
    if not hasattr(data, 'previousIndex'):
        index = 1
    else:
        index = data.previousIndex 
    latestIndex = data.getLatestIndex()
    while index <= latestIndex and data[index]['elapsedTime'] < elapsedTime:
        index += 1
    data.previousIndex = index - 1    

    t0 = data[index - 1]['elapsedTime']
    t1 = data[index]['elapsedTime']
    alpha = (elapsedTime - t0) / (t1 - t0)
    phi0 = data[index - 1]['distance']
    phi1 = data[index]['distance']
    phi = phi0 * (1 - alpha) + phi1 * alpha
    dx = data[index]['dx']
    if elapsedTime > 1000.:
        plotContour(data, index)
    diff = abs(phi - phiBase) / dx
    diff[abs(phiBase) > 4 * dx] = 0.

    return max(diff)
    
#     if elapsedTime > 1000:
#         ID = np.argmax(abs(phi - phiBase))
#         diff = abs(phi - phiBase)
#         diff[abs(phiBase) > 2 * dx] = 0.
#         print 'diff max',max(diff) / dx
#         print 'max(abs(phi - phiBase)) / dx',max(abs(phi - phiBase)) / dx
#         print 'elapsedTime',elapsedTime
#         print 't0',t0,'t1',t1
#         print 'phi[ID]',phi[ID]
#         print 'phiBase[ID]',phiBase[ID]
#         print 'phi0[ID]',phi0[ID]
#         print 'phi1[ID]',phi1[ID]
#         print 'dx',dx
#         print "ID",ID
#         raw_input('stopped')
#     return max(abs(phi - phiBase)) / dx
# #    return np.sum((phi - phiBase)**2)

def plotNorms():
    times, normdata = getNormData() 
    for index in xrange(len(normdata[0])):
        pylab.plot(times, normdata[:, index])
    pylab.show()

def plotContour(data, index):
    dx = data[index]['dx']
    dy = data[index]['dy']
    nx = data[index]['nx']
    ny = data[index]['ny']
    import fipy as fp
    mesh = fp.Grid2D(nx=nx, ny=ny, dx=dx, dy=dy)
    shape = (ny, nx)
    x = np.reshape(mesh.x.value, shape)
    y = np.reshape(mesh.y.value, shape)
    phi = np.reshape(data[index]['distance'], shape)
    pylab.contour(x, y, phi, (0.,), colors='black')
    pylab.show()
    
    
    
if __name__ == '__main__':
    ##    from profiler import calibrate_profiler
    ##    from profiler import Profiler
    ##    fudge = calibrate_profiler(10000)
    ##    profile = Profiler('profile', fudge=fudge)
    plotNorms()
    ##    profile.stop()
