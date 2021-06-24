from collections import OrderedDict
import itertools
from . import utils
from django.http import StreamingHttpResponse

def streaming_response(filename, rows):
    body = []
    body.append((utils.json_dumps(row) + "\n") for row in rows)
    response = StreamingHttpResponse(itertools.chain.from_iterable(body), content_type="application/x-ndjson")
    response['Content-Disposition'] = 'attachment; filename="%s.rows.json"' % filename
    return response

def format_report(report, context):
    "returns output as a streaming list of json rows."
    items_qs = report['items']
    peek = items_qs.first()
    if not peek:
        # no results
        return StreamingHttpResponse([], content_type="application/x-ndjson")

    # we might be able to something more-clever later for reports without explicit headers
    #headers = headers or formatterfn(peek).keys()

    headers = report.get('headers')
    row_formatter = context.get('row-formatter')

    def format_row(row):
        if row_formatter:
            row = row_formatter(row)
        return OrderedDict(zip(headers, row))

    rows = map(format_row, items_qs)

    filename = report['title'].replace(' ', '-').lower()
    return streaming_response(filename, rows)
