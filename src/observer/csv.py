from collections import OrderedDict
import itertools
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

def streaming_csv_response(filename, rows, headers):
    pseudo_buffer = Echo()
    writer = csvpy.DictWriter(pseudo_buffer, fieldnames=headers)
    header = OrderedDict(zip(headers, headers))
    body = []
    if not utils.isint(list(headers)[0]):
        # bit of a kludge.
        # assumption fails when first header in header row is an int
        body.append((writer.writerow(row) for row in [header]))
    body.append((writer.writerow(row) for row in rows))
    response = StreamingHttpResponse(itertools.chain.from_iterable(body), content_type="text/csv")
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

def format_list(row, headers=None):
    if headers:
        return OrderedDict(zip(headers, row))
    # returns an OrderedDict mapping of column numbers : column values
    return OrderedDict(zip(range(0, len(row)), map(coerce, row)))

def format_dict(row, headers=None):
    # todo: check given header matches keys in row
    # or wait until csv.DictWriter complains?
    return utils.val_map(coerce, row)

def format_article(art, headers=None):
    return format_dict(utils.to_dict(art))

def format_report(report, context):
    # sniff the result types
    items_qs = report['items']
    peek = items_qs.first()
    if not peek:
        # no results
        # we could return a 204, but that's more REST-ful
        # and we're making an effort to avoid cleverness here
        return StreamingHttpResponse([], content_type="text/csv")

    headers = report.get('headers')

    # these always return a dictionary version of the row
    formatters = {
        tuple: format_list,
        dict: format_dict,
        models.Article: format_article,
    }
    formatterfn = partial(formatters[type(peek)], headers=headers)

    report_formatterfn = report.get('row_formatters', {}).get('CSV')

    if report_formatterfn:
        formatterfn = lambda row: format_list(report_formatterfn(row), headers=headers)

    rows = map(formatterfn, items_qs) # still lazy
    headers = headers or formatterfn(peek).keys()
    filename = report['title'].replace(' ', '-').lower()
    return streaming_csv_response(filename, rows, headers)
