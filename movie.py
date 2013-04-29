import os.path
import sys


import tables
from contourViewer import ContourViewer

def update_progress(progress):
    progress = int(progress * 100)
    dec = progress / 10
    sys.stdout.write('\r[{0}] {1}%'.format('#' * dec + '-' * (10  - dec), progress))
    sys.stdout.flush()

if __name__ == '__main__':
    viewer = ContourViewer(tags=['serialnumber17'], parameters={'Nx' : 600})
    latestIndex = viewer.data.getLatestIndex()
    index = 0
    dataPath = os.path.join('Data', viewer.record.label)
    print 'dataPath',dataPath
    while index <= latestIndex:
        filename = os.path.join(dataPath, 'step%s.png' % str(index).rjust(6, '0'))
        viewer.plot(indices=index, filename=filename)
        index += 10
        update_progress(float(index) / latestIndex)
    print 'finished'
                     

