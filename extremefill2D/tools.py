import os.path
import cgi
from math import modf
import shutil
import json
import datetime


import tables
from sumatra.projects import load_project
from sumatra.formatting import HTMLFormatter
from sumatra.formatting import fields
from IPython.core.display import HTML
import numpy as np
from dicttable import DictTable
import fipy as fp


def _quotient_remainder(dividend, divisor):
    q = dividend // divisor
    r = dividend - q * divisor
    return (q, r)


def human_readable_duration(seconds):
    """
    Coverts seconds to human readable unit

    >>> human_readable_duration(((6 * 60 + 32) * 60 + 12))
    '6h 32m 12.00s'
    >>> human_readable_duration((((8 * 24 + 7) * 60 + 6) * 60 + 5))
    '8d 7h 6m 5.00s'
    >>> human_readable_duration((((8 * 24 + 7) * 60 + 6) * 60))
    '8d 7h 6m'
    >>> human_readable_duration((((8 * 24 + 7) * 60) * 60))
    '8d 7h'
    >>> human_readable_duration((((8 * 24) * 60) * 60))
    '8d'
    >>> human_readable_duration((((8 * 24) * 60) * 60) + 0.12)
    '8d 0.12s'

    """
    (fractional_part, integer_part) = modf(seconds)
    (d, rem) = _quotient_remainder(int(integer_part), 60 * 60 * 24)
    (h, rem) = _quotient_remainder(rem, 60 * 60)
    (m, rem) = _quotient_remainder(rem, 60)
    s = rem + fractional_part
    
    return ' '.join(
        templ.format(val)
        for (val, templ) in [
            (d, '{0}d'),
            (h, '{0}h'),
            (m, '{0}m'),
            (s, '{0:.2f}s'),
            ]
        if val != 0
        )

class CustomHTMLFormatter(HTMLFormatter):
    def __init__(self, records, fields=fields, parameters=None):
        self.fields = fields
        self.parameters = parameters
        super(CustomHTMLFormatter, self).__init__(records)
        
    def long(self):
        def format_record(record):
            output = "  <dt>%s</dt>\n  <dd>\n    <dl>\n" % record.label
            for field in self.fields:
                output += "      <dt>%s</dt><dd>%s</dd>\n" % (field, cgi.escape(str(getattr(record, field))))
            output += "    </dl>\n  </dd>"
            return output
        return "<dl>\n" + "\n".join(format_record(record) for record in self.records) + "\n</dl>"

    def format_record(self, record):
        t = ()
        for field in self.fields:
            attr = getattr(record, field)
            if field == 'timestamp':
                s = attr.strftime('%Y-%m-%d %H:%M')
            elif field == 'repository':
                s = '{0} ({1})'.format(attr.url, attr.upstream)
            elif field == 'parameters' and self.parameters:
                s = ''
                d = attr.as_dict()
                for p in self.parameters:
                    s += ' {0}: {1},'.format(p, d[p])
                s = s[1:-1]
            elif field == 'tags':
                s = ''
                for tag in attr:
                    s += ' {0},'.format(tag)
                s = s[1:-1]
            elif field == 'version':
                s = attr[:12]
            elif field == 'duration':
                s = human_readable_duration(attr)
            else:
                s = str(attr)
            c = cgi.escape(s)
            # if field in ('label', 'timestamp', 'repository', 'parameters', 'tags', 'version', 'duration'):
            # #    c = "<code>" + c + "</code>"

            if field in ('label', 'repository', 'version', 'parameters'):
                c = "<code>" + c + "</code>"
            
            t += (c,)
        
        return "  <tr>\n    <td>" + "</td>\n    <td>".join(t) + "    </td>\n  </tr>"

    def style(self, table_out):
        replacements = {'<table>' : '<table style="border:2px solid black;border-collapse:collapse; font-size:10px;">',
                        '<th>'    : '<th style="border:2px solid black;background:#b5cfd2">',
                        '<td>'    : '<td style="border:2px solid black;">',
                        '<code>'  : '<code style="font-size:10px;">'}
        
        for k, v in replacements.iteritems():
            table_out = table_out.replace(k, v)

        return table_out

    def table(self):
        table_out = "<table>\n" + \
            "  <tr>\n    <th>" + "</th>\n    <th>".join(field.title() for field in self.fields) + "    </th>\n  </tr>\n" + \
            "\n".join(self.format_record(record) for record in self.records) + \
            "\n</table>" + \
            "\n<br>"
        
        return self.style(table_out)

    def ipython_table(self):
        return HTML(self.table())
        


def markdown_table(records):
    from texttable import Texttable
    fields = ['label', 'timestamp', 'reason', 'duration']
    table = Texttable()
    table.set_cols_dtype(['t'] * len(fields))
    rows = [fields]
    for record in records:
        rows.append([str(getattr(record, field)) for field in fields])
    table.add_rows(rows)
    out = table.draw().replace('=', '-')
    out = out.replace('\n+-', '\n|-')
    out = '|' + out[1:-1] + '|'
    return out

def getSMTRecords(records=None, tags=[], parameters={}, atol=1e-10, rtol=1e-10, path='./'):
    if not records:
        project = load_project(path)
        records = project.record_store.list(project.name, tags=tags)
    records_out = []
    for r in records:
        if set(tags).issubset(set(r.tags)):
            allclose = []
            for k, v in parameters.items():
                if np.allclose(v, r.parameters.as_dict()[k], atol=atol, rtol=rtol):
                    allclose.append(True)
                else:
                    allclose.append(False)
            if np.all(allclose):
                records_out.append(r)
            # if set(parameters.items()).issubset(set(r.parameters.as_dict().items())):
            #     records_out.append(r)

    return records_out

def getRecord(records=None, **args):
    records = getSMTRecords(records=records, parameters=args)
    if len(records) == 0:
        return None
    else:
        return records[0]
    
def getData(tags, parameters):
    records = getSMTRecords(tags, parameters)
    record = records[0]
    return os.path.join(record.datastore.root, record.output_data[0].path)

def smt_ipy_table(records, fields, parameters=[]):
    from ipy_table import make_table
    import ipy_table
    table = [[field.title() for field in fields]]
    for record in records:
        record_list = []
        for field in fields:
            attr = getattr(record, field)
            if field == 'timestamp':
                s = attr.strftime('%Y-%m-%d %H:%M')
            elif field == 'repository':
                s = '{0}'.format(attr.upstream)
            elif field == 'parameters' and parameters:
                s = ''
                d = attr.as_dict()
                for p in parameters:
                    s += ' {0}: {1},'.format(p, d[p])
                s = s[1:-1]
            elif field == 'tags':
                s = ''
                for tag in attr:
                    s += ' {0},'.format(tag)
                s = s[1:-1]
            elif field == 'version':
                s = attr[:12]
            elif field == 'duration':
                s = human_readable_duration(attr)
            elif field == 'label':
                s = attr[:8]
            else:
                s = str(attr)
            c = cgi.escape(s)
            # if field in ('label', 'timestamp', 'repository', 'parameters', 'tags', 'version', 'duration'):
            # #    c = "<code>" + c + "</code>"

            if field in ('label', 'repository', 'version', 'parameters'):
                c = "<code>" + c + "</code>"
            
            record_list.append(c)

        table.append(record_list)
    t = make_table(table)
    ipy_table.apply_theme('basic')
    ipy_table.set_global_style(wrap=True)
    return HTML(t._repr_html_())


def batch_launch(reason='', tags=[], **kwargs):
    cmd = 'qsub -cwd -o {0} -e {0} launcher'.format('.qsub')
    for k, v in kwargs.iteritems():
        cmd += ' {0}={1}'.format(k, v)
    cmd += ' --reason="{0}"'.format(reason)
    for t in tags:
        cmd += ' --tag={0}'.format(t)
    os.system(cmd)

def delete_defunct_smt_directories():
    data_dir = 'Data'
    directories = os.listdir(data_dir)
    records = getSMTRecords()
    labels = [r.label for r in records]
    for directory in directories:
        tail = os.path.split(directory)[1]
        if tail in labels:
            pass
        else:
            path = os.path.join(data_dir, directory)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

def getDepositionRates(record):
    datafile = os.path.join(record.datastore.root, record.output_data[0].path)
    data = DictTable(datafile, 'r')
    latestIndex = data.getLatestIndex()
    indexJump = record.parameters['data_frequency']
    index = 0
    elapsedTimes = []
    depositionRates = []
    while index <= latestIndex:
        d = data[index]
        elapsedTimes.append(d['elapsedTime'])
        depositionRates.append(d['extensionGlobalValue'])
        index += indexJump
    return elapsedTimes, depositionRates

def switch_smt_database(db_name):
    fname = '.smt/project'
    shutil.copy(fname, fname + '.bkup')
    f = open(fname, 'r')
    d = json.load(f)
    f.close()
    old_db_name = d['name']
    d['name'] = db_name
    f = open(fname, 'w')
    json.dump(d, f, indent=2)
    f.close()
    return old_db_name

def find_all_zeros(f, x0, x1, N=1000):
    x = np.linspace(x0, x1, N)
    y = f(x)
    sign = y[1:] * y[:-1]
    mask = sign < 0
    IDs = np.array(np.nonzero(mask)).flatten()
    from scipy.optimize import brentq
    return np.array([brentq(f, x[ID], x[ID + 1]) for ID in IDs])

class FeatureProperty(object):
    def __init__(self, record):
        self.record = record

    def getVoidSize(self, record):
        from scipy.interpolate import interp1d

        datafile = os.path.join(record.datastore.root, record.output_data[0].path)
        h5file = tables.openFile(datafile, mode='r')
        index = h5file.root._v_attrs.latestIndex
        data = h5file.getNode('/ID' + str(int(index)))

        mindx = min(data.dx.read())
        featureDepth = record.parameters['featureDepth']
        distanceBelowTrench = 10 * mindx

        if not hasattr(self, 'mesh'):
            self.mesh = fp.Grid2D(nx=data.nx.read(), ny=data.ny.read(), dx=data.dx.read(), dy=data.dy.read()) - [[-mindx / 100.], [distanceBelowTrench + featureDepth]]
        phi = fp.CellVariable(mesh=self.mesh, value=data.distance.read())

        N = 1000
        rinner = record.parameters['rinner']
        router = record.parameters['router']
        X = (rinner + router) / 2. * np.ones(N)
        Y = np.linspace(-featureDepth, 10e-6, 1000)
        points = (X, Y)
        if not hasattr(self, 'nearestCellIDs'):
            self.nearestCellIDs = self.mesh._getNearestCellID(points)
        phiInterpolated = phi(points, order=1, nearestCellIDs=self.nearestCellIDs)

        f = interp1d(Y, phiInterpolated)
        zeros = find_all_zeros(f, Y[0], Y[-1])

        if len(zeros) < 2:
            void_size = 0.
        else:
            void_size = max((zeros[1:] - zeros[:-1])[::2]) / featureDepth

        if len(zeros) % 2 == 0:
            height = 1.
        else:
            height = (featureDepth + zeros[-1]) / featureDepth 
            height = min(height, 1.)

        h5file.close()

        return void_size, height

def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y



def refine_contour_plot(points, values):
    """

    Take a set of `points` and `values` used to plot a contour plot and returns new points to calculate in order of how the value difference between connecting points is reduced.

    >>> refine_contour_plot([[0, 0], [1, 0], [0, 1]], [0., 1., 10.])
    [[0., 0.5], [0.5, 0.5], [0.5, 0.]]

    :Parameters:
      - `points`: Set of (x, y) points.
      - `values`: Values at the points

    :Returns:

      - `new_points`: set of points to recalculate and improve the contour plot

    """
    from scipy.spatial import Delaunay
    tri = Delaunay(points)  
    indices, indptr = tri.vertex_neighbor_vertices
    edges = []
    for i in xrange(len(points)):
        for j in indptr[indices[i]:indices[i + 1]]:
            if j > i:
                edges.append([i, j])
    edges = np.array(edges)
    vertexValues = np.array(values)[edges]
    edgeValue = abs(vertexValues[:,0] - vertexValues[:,1])
    
    return ((tri.points[edges[:,0],:] + tri.points[edges[:,1],:]) / 2)[np.argsort(edgeValue)][::-1]


class DataWriter(object):
    def __init__(self, datafile):
        self.datafile = datafile

    def write(self, elapsedTime, timeStep, variables, **kwargs):
        h5data = DictTable(self.datafile, 'a')
        mesh = variables.distance.mesh
        dataDict = {'elapsedTime' : elapsedTime,
                    'nx' : mesh.nx,
                    'ny' : mesh.ny,
                    'dx' : mesh.dx,
                    'dy' : mesh.dy,
                    'distance' : np.array(variables.distance)}

        h5data[timeStep] = dict(dataDict.items() + kwargs.items())


class WriteCupricData(DataWriter):
    def write(self, elapsedTime, timeStep, variables, **kwargs):
        kwargs['cupric'] = np.array(variables.cupric)
        super(WriteCupricData, self).write(elapsedTime, timeStep, variables, **kwargs)
