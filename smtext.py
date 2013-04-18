#import pylab
#import numpy as npf

import cgi

from sumatra.projects import load_project
from texttable import Texttable
from sumatra.formatting import HTMLFormatter
from sumatra.formatting import fields


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
            else:
                s = str(attr)
            c = cgi.escape(s)
            if field in ('label', 'timestamp', 'repository', 'parameters', 'tags', 'version'):
                c = "<code>" + c + "</code>"
            
            t += (c,)
        
        return "  <tr>\n    <td>" + "</td>\n    <td>".join(t) + "    </td>\n  </tr>"

    def table(self):
        return "<table>\n" + \
               "  <tr>\n    <th>" + "</th>\n    <th>".join(field.title() for field in self.fields) + "    </th>\n  </tr>\n" + \
               "\n".join(self.format_record(record) for record in self.records) + \
               "\n</table>"


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

def getSMTrecords(tags=[], parameters={}):
    project = load_project()
    records_list = []
    for r in project.record_store.list(project.name):
        if set(tags).issubset(set(r.tags)):
            if set(parameters.items()).issubset(set(r.parameters.as_dict().items())):
                records_list.append(r)

    return records_list

if __name__ == '__main__':
    records = getSMTrecords(tags=['serialnumber10'], parameters={'kPlus' : 100.0})
    #print markdown_table(records)
    print CustomHTMLFormatter(records, fields=['label', 'timestamp', 'parameters', 'tags'], parameters=['kPlus']).table()
