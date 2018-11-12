from collections import OrderedDict
import itertools
from . import utils
from django.http import StreamingHttpResponse

def streaming_response(filename, rows):
    body = []
    body.append((utils.json_dumps(row) + "\n") for row in rows)
    response = StreamingHttpResponse(itertools.chain.from_iterable(body), content_type="application/json")
    response['Content-Disposition'] = 'attachment; filename="%s.rows.json"' % filename
    return response

def format_report(report, context):
    "returns output as a streaming list of json rows."
    items_qs = report['items']
    peek = items_qs.first()
    if not peek:
        # no results
        return StreamingHttpResponse([], content_type="application/json")

    # we might be able to something more-clever later for reports without explicit headers
    #headers = headers or formatterfn(peek).keys()

    headers = report.get('headers')
    rows = map(lambda row: OrderedDict(zip(headers, row)), items_qs)

    filename = report['title'].replace(' ', '-').lower()
    return streaming_response(filename, rows)
