#import pylab
#import numpy as npf
from sumatra.projects import load_project
from texttable import Texttable
from sumatra.formatting import HTMLFormatter

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

def get_records(tags=[], parameters={}):
    project = load_project()
    records_list = []
    for r in project.record_store.list(project.name):
        if set(tags).issubset(set(r.tags)):
            if set(parameters.items()).issubset(set(r.parameters.as_dict().items())):
                records_list.append(r)

    return records_list


if __name__ == '__main__':
    records = get_records(tags=['serialnumber10'], parameters={'kPlus' : 100.0})
    print markdown_table(records)
    #print HTMLFormatter(records).table()
