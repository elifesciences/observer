import csv as csvpy
from datetime import date, datetime
from . import models, utils
from functools import partial

# https://docs.djangoproject.com/en/1.11/howto/outputting-csv/
from django.http import StreamingHttpResponse

class Echo(object):
    "An object that implements just the write method of the file-like interface."

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def streaming_csv_response(filename, rows, writer=None):
    pseudo_buffer = Echo()

    writer = (writer or csvpy.writer)(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    return response

#
#
#

def coerce(val):
    "coerce a value to a csv-friendly value"
    lu = {
        datetime: utils.ymdhms,
        date: utils.ymd,
    }
    if type(val) in lu:
        return lu[type(val)](val)
    return val

def format_dict(row):
    # alphabetical sorting
    return sorted(utils.val_map(coerce, row).items())

def format_list(row, headers):
    if not headers:
        headers = range(1, len(row))
    return zip(headers, map(coerce, row))
    
    lu = {
        datetime: utils.ymd
    }
    return [val if not lu.get(type(val)) else lu[type(val)](val) for val in row]

def format_article(art):
    return format_dict(utils.to_dict(art))

def format_row(row, context):
    "the output of this function must be a list of pairs, [(key, val), (key, val), etc]"
    idx = {
        dict: format_dict,
        models.Article: format_article,
    }
    default = partial(format_list, context.get('headers'))
    return idx.get(type(row), default)(row)

'''
arghj! not getting anywhere with this code.

intent is:

you pass format_report a report
a report contains an 'items' key
'items' is a queryset
each result in queryset is either an object, a dict or a list
each type gets it's own formatter
each of the values emitted needs to go through the coercer
headers can optionally be present
if present, use those. results are limited to the keys specified
if not present, peek into the first row of results and use those keys, ordered alphabetically
if not present and row is a list of values, emit no headers, assume ordering is correct



'''


def format_report(report, context):
    rows = map(partial(format_row, context=context), report['items'])
    filename = report['title'].replace(' ', '-').lower()
    
    peek = next(rows)
    headers = map(utils.first, peek)

    rows = itertools.chain([peek], rows)
    return streaming_csv_response(filename, rows, csvpy.DictWriter)
