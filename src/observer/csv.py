import csv as csvpy
from datetime import datetime
from . import utils

# https://docs.djangoproject.com/en/1.11/howto/outputting-csv/
from django.http import StreamingHttpResponse

class Echo(object):
    "An object that implements just the write method of the file-like interface."

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def streaming_csv_response(filename, rows):
    pseudo_buffer = Echo()
    writer = csvpy.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    return response

#
#
#

def format_row(row):
    lu = {
        datetime: utils.ymd
    }
    return [val if not lu.get(type(val)) else lu[type(val)](val) for val in row]

def format_report(report, context):
    rows = map(format_row, report['items'])
    filename = report['title'].replace(' ', '-').lower()
    return streaming_csv_response(filename, rows)
