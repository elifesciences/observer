from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import Http404  # , get_object_or_404

from . import reports, rss
import logging

LOG = logging.getLogger(__name__)

def paginate_report_results(report, page=1, per_page=10):
    report = report()

    # carve it up here

    return report

def format_report(report, format, context):
    known_formats = {
        'rss': rss.format_report,
    }
    return known_formats[format](report, context)

def report(request, name, format='rss'):
    try:
        report = reports.get_report(name)
    except KeyError:
        raise Http404("report not found")
    try:
        report_paginated = paginate_report_results(report)
        # additional things to pass to whatever is rendering the report
        # keys here will override any found in the report
        context = {
            'link': "https://data.elifesciences.org" + reverse('report', kwargs={'name': name}),
        }
        report_formatted = format_report(report_paginated, format, context)
        return HttpResponse(report_formatted, content_type='text/xml')
    except BaseException:
        LOG.exception("unhandled exception")
        return HttpResponse("server error attempting to handle your request", status=500)
