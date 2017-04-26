from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import Http404  # , get_object_or_404

from et3.render import render_item
from et3.extract import path as p
from et3.utils import uppercase
from observer import models
from .utils import ensure, isint

from . import reports, rss
import logging

LOG = logging.getLogger(__name__)

def request_args(request, **overrides):
    opts = {'per_page': 28, 'page_num': 1, 'order_direction': 'ASC', 'min_per_page': 1, 'max_per_page': 100}
    opts.update(overrides)

    def ispositiveint(v):
        ensure(isint(v) and int(v) > 0, "expecting positive integer, got: %s" % v)
        return int(v)

    def inrange(minpp, maxpp):
        def fn(v):
            ensure(v >= minpp and v <= maxpp, "value must be between %s and %s" % (minpp, maxpp))
            return v
        return fn

    def isin(lst):
        def fn(val):
            ensure(val in lst, "value %r is not in %r" % (val, lst))
            return val
        return fn

    desc = {
        'page': [p('page', opts['page_num']), ispositiveint],
        'per_page': [p('per-page', opts['per_page']), ispositiveint, inrange(opts['min_per_page'], opts['max_per_page'])],
        'order': [p('order', opts['order_direction']), uppercase, isin(['ASC', 'DESC'])],
    }
    return render_item(desc, request.GET)

def chop(q, page, per_page, order):
    """orders and chops a query into pages, returning the total of the original query and a query object"""
    total = q.count()

    order_by_idx = {
        models.Article: 'datetime_version_published',
        models.ArticleJSON: 'msid',
    }
    order_by = order_by_idx[q.model]

    # switch directions if descending (default ASC)
    if order == 'DESC':
        order_by = '-' + order_by

    q = q.order_by(order_by)

    # a per-page = 0 means 'all results'
    if per_page > 0:
        start = (page - 1) * per_page
        end = start + per_page
        q = q[start:end]

    return total, q


def paginate_report_results(report, page, per_page, order):
    report = report()
    report['count'], report['items'] = chop(report['items'], page, per_page, order)
    return report

def format_report(report, format, context):
    known_formats = {
        'rss': rss.format_report,
    }
    return known_formats[format](report, context)


#
# views
#

def report(request, name, format='rss'):
    try:
        report = reports.get_report(name)
    except KeyError:
        raise Http404("report not found")
    try:
        kwargs = request_args(request)
        report_paginated = paginate_report_results(report, **kwargs)
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
