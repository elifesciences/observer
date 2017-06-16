from django.http import HttpResponse
from collections import OrderedDict
import itertools
import csv as csvpy
from datetime import date, datetime
from . import models, utils
#from functools import partial

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
        # assumption will fail on reports whose first header in the header row is an integer
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

def format_list(row):
    # returns an OrderedDict mapping of column numbers : column values
    return OrderedDict(zip(range(0, len(row)), map(coerce, row)))

def format_dict(row):
    return utils.val_map(coerce, row)

def format_article(art):
    return format_dict(utils.to_dict(art))

def format_report(report, context):
    # sniff the result types
    items_qs = report['items']
    peek = items_qs.first()
    if not peek:
        # no results
        # we could return a 204, but that's more REST-ful
        # and we're making an effort to avoid cleverness here
        return HttpResponse(status=200)

    formatters = {
        tuple: format_list,
        dict: format_dict,
        models.Article: format_article
    }
    formatterfn = formatters[type(peek)]
    headers = formatterfn(peek).keys()

    rows = map(formatterfn, items_qs) # still lazy
    filename = report['title'].replace(' ', '-').lower()
    return streaming_csv_response(filename, rows, headers)
