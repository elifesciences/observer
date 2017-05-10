from os.path import join
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import Http404  # , get_object_or_404
from django.conf import settings
from et3.render import render_item
from et3.extract import path as p
from et3.utils import uppercase
from annoying.decorators import render_to
from .utils import ensure, isint
from . import reports, rss, csv
import logging

from .reports import PER_PAGE, ORDER, SERIALISATIONS, NO_PAGINATION, ORDER_BY, RSS, CSV

LOG = logging.getLogger(__name__)

def request_args(request, report_meta, **overrides):
    opts = {
        'per_page': report_meta[PER_PAGE],
        'page_num': 1,
        'order': report_meta[ORDER], # ll: 'ASC'
        'min_per_page': 1,
        'max_per_page': 100, # ignored if report disables pagination
        'format': report_meta[SERIALISATIONS][0] # default format is the first
    }
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
            ensure(val in lst, "%r not found in list: [%s]" % (val, ', '.join(lst)))
            return val
        return fn

    desc = {
        'page': [p('page', opts['page_num']), ispositiveint],
        'per_page': [p('per-page', opts['per_page']), ispositiveint, inrange(opts['min_per_page'], opts['max_per_page'])],
        'order': [p('order', opts['order']), uppercase, isin(['ASC', 'DESC'])],
        'format': [p('format', opts['format']), uppercase, isin(report_meta[SERIALISATIONS])]
    }
    if opts[PER_PAGE] == NO_PAGINATION:
        # if no user per-page has been specified + report explicitly defaults to no pagination, return all results
        desc['per_page'] = [NO_PAGINATION]
    return render_item(desc, request.GET)

def chop(q, page, per_page, order, order_by):
    """orders and chops a query into pages, returning the total of the original query and a query object"""
    total = q.count()

    # switch directions if descending (default ASC)
    if order == 'DESC':
        order_by = '-' + order_by

    q = q.order_by(order_by)

    # a per-page = 0 means 'all results'
    if per_page > NO_PAGINATION:
        start = (page - 1) * per_page
        end = start + per_page
        q = q[start:end]

    return total, q

def paginate_report_results(report, rargs):
    # TODO: shift this into request_args one day
    order_by = report.meta[ORDER_BY]

    report = report() # results will stay lazy until realised
    # this gives us an opportunity to chop them up and enforce any ordering

    def vals(d, ks):
        return [d[k] for k in ks]

    report['count'], report['items'] = chop(report['items'], *vals(rargs, ['page', 'per_page', 'order']), order_by)

    # update the report with any user overrides
    report.update(rargs)

    return report

def format_report(report, rargs, context):
    # the report has been executed at this point
    known_formats = {
        RSS: rss.format_report,
        CSV: csv.format_report,
    }
    return known_formats[report['format']](report, context)


#
# views
#

@render_to("landing.html")
def landing(request):
    return {
        'html_title': 'Observer - article reports',
        'readme': open(join(settings.PROJECT_DIR, 'README.md')).read()
    }

def report(request, name, format_hint=None):
    try:
        report = reports.get_report(name)
    except KeyError:
        raise Http404("report not found")
    try:
        # extract and validate any params user has given us
        overrides = {}
        if format_hint:
            overrides['format'] = format_hint
        rargs = request_args(request, report.meta, **overrides)

    except AssertionError as err:
        LOG.exception("bad user request")
        return HttpResponse("bad request: %s" % err, status=400)

    try:
        # truncate report results, enforce any user ordering
        report_paginated = paginate_report_results(report, rargs)

        # additional things to pass to whatever is rendering the report
        # keys here will override any found in the report
        context = {
            'link': "https://observer.elifesciences.org" + reverse('report', kwargs={'name': name}),
        }
        return format_report(report_paginated, rargs, context)

    except BaseException:
        LOG.exception("unhandled exception")
        return HttpResponse("server error attempting to handle your request", status=500)
