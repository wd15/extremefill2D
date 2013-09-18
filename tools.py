import os.path
import cgi
from math import modf
import shutil
import json


from sumatra.projects import load_project
from texttable import Texttable
from sumatra.formatting import HTMLFormatter
from sumatra.formatting import fields
from IPython.core.display import HTML
import numpy as np
from dicttable import DictTable
import fipy as fp
from ipy_table import make_table

from scipy.interpolate import interp1d
import tables


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

def getSMTRecords(records=None, tags=[], parameters={}, atol=1e-10, rtol=1e-10):
    if records is None:
        project = load_project()
        records = project.record_store.list(project.name)
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
    t.apply_theme('basic')
    t.set_global_style(wrap=True)
    return HTML(t._repr_html_())


def batch_launch(reason='', tags=[], **kwargs):
    cmd = 'qsub -cwd -o {0} -e {0} launcher'.format('.qsub')
    for k, v in kwargs.iteritems():
        cmd += ' {0}={1}'.format(k, v)
    cmd += ' --reason="{0}"'.format(reason)
    for t in tags:
        cmd += ' --tag={0}'.format(t)
    os.system(cmd)


def write_data(dataFile, elapsedTime, distance, timeStep, **otherFields):
    h5data = DictTable(dataFile, 'a')
    mesh = distance.mesh
    dataDict = {'elapsedTime' : elapsedTime,
                'nx' : mesh.nx,
                'ny' : mesh.ny,
                'dx' : mesh.dx,
                'dy' : mesh.dy,
                'distance' : np.array(distance)}
    for k, v in otherFields.iteritems():
        dataDict[k] = np.array(v)

    h5data[timeStep] = dataDict

def geometric_spacing(initial_spacing, domain_size, spacing_ratio=1.1):
    """
    
    Caculate grid spacing in one dimension using the inital grid cell
    size given by `initial_spacing`. The grid cells are scaled up by
    `spacing_ratio` and `spacing ratio` must be greater than 1.

    >>> geometric_spacing(1., 10., 1.1)
    array([ 1.     ,  1.1    ,  1.21   ,  1.331  ,  1.4641 ,  1.61051,  2.28439])
    >>> np.sum(geometric_spacing(1., 10., 1.1))
    10.0

    """
    if spacing_ratio <= 1.:
        raise Exception, 'spacing_ratio must be greater than 1'
    r = spacing_ratio
    L = domain_size
    dx = initial_spacing
    nx = int(np.log(1 - L * (1 - r) / dx) / np.log(r))
    Lestimate = dx * (1 - r**nx) / (1 - r)
    spacing = initial_spacing * spacing_ratio**np.arange(nx)
    spacing[-1] = spacing[-1] + (L - Lestimate)
    return spacing


def get_nonuniform_dx(dx, x0, x1, x2, padding, spacing_ratio=1.1):
    """
    
    Calculate the geometric grid spacing for a grid with an fine grid
    between `r0` and `r1` and a coarse grid elsewhere.

    >>> np.sum(get_nonuniform_dx(0.1, 3., 4., 10, 0.3, 2.)[:7])
    3.0
    >>> get_nonuniform_dx(0.1, 3., 4., 10, 0.3, 2.)
    array([ 2. ,  0.4,  0.2,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,
        0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.1,  0.2,
        0.4,  0.8,  4.2])

    """

    if x0 <= padding or x2 - x1 <= padding:
        raise Exception, 'padding is too large'
    
    dx0 = geometric_spacing(dx, x0 - padding, spacing_ratio)[::-1]

    Lx = x1 - x0 + 2 * padding
    nx = int(Lx / dx)
    dx1 = (Lx / nx) * np.ones(nx)
    
    dx2 = geometric_spacing(dx, x2 - (x1 + padding), spacing_ratio)

    return np.concatenate((dx0, dx1, dx2))

class DistanceVariableNonUniform(fp.DistanceVariable):
    def getLSMshape(self):
        mesh = self.mesh

        min_dx = lambda x: fp.numerix.amin(x) if len(fp.numerix.shape(x)) > 0 else x
        
        if hasattr(mesh, 'nz'):
            raise Exception, "3D meshes not yet implemented"
        elif hasattr(mesh, 'ny'):
            dx = (min_dx(mesh.dy), min_dx(mesh.dx))
            shape = (mesh.ny, mesh.nx)
        elif hasattr(mesh, 'nx'):
            dx = (min_dx(mesh.dx),)
            shape = mesh.shape
        else:
            raise Exception, "Non grid meshes can not be used for solving the FMM."

        return dx, shape

    def deleteIslands(self):
        from fipy.tools import numerix
        from fipy.tools.numerix import MA

        cellToCellIDs = self.mesh._getCellToCellIDs()
        adjVals = numerix.take(self.value, cellToCellIDs)
        adjInterfaceValues = MA.masked_array(adjVals, mask = (adjVals * self.value) > 0)
        masksum = numerix.sum(numerix.logical_not(MA.getmask(adjInterfaceValues)), 0)
        tmp = MA.logical_and(masksum == 4, self.value > 0)
        self.value = numerix.array(MA.where(tmp, -1, self.value))

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
    indexJump = 10
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

class VoidSizeFinder(object):

    def find_void_size(self, record):
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
