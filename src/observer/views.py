from rest_framework.response import Response
from django.shortcuts import Http404 #, get_object_or_404

from . import reports
import logging

LOG = logging.getLogger(__name__)

def paginate_report_results(report, page=1, per_page=10):
    return report

def format_report(report, format):
    return report

def report(request, name, format='rss'):
    try:
        report = getattr(reports, name)
        if not report:
            raise Http404("report not found")
        report_paginated = paginate_report_results(report)
        report_formatted = format_report(report_paginated, format)
        return Response(report_formatted, content_type='text/xml')
    except Exception:
        LOG.exception("unhandled exception")
        raise Response("server error attempting to handle your request", state=500)
