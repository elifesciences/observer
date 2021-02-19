import cProfile, pstats
from datetime import date
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import Http404  # , get_object_or_404
from et3.render import render_item
from et3.extract import path as p
from et3.utils import uppercase
from annoying.decorators import render_to
from .utils import ensure, isint, subdict
from . import reports
import logging

from .reports import NO_PAGINATION, NO_ORDERING, ASC, DESC

LOG = logging.getLogger(__name__)

PROFILING = False

def profile(fn):
    if not PROFILING:
        return fn

    def wrapper(*args, **kwargs):
        pr = cProfile.Profile(timeunit=0.001)
        pr.enable()
        result = fn(*args, **kwargs)
        pr.disable()

        sortby = "cumulative"
        ps = pstats.Stats(pr).sort_stats(sortby)
        ps.print_stats(.01)
        fname = "/tmp/output-%s.prof" % fn.__name__
        ps.dump_stats(fname)
        print("wrote", fname)

        return result

    return wrapper

#

def request_args(request, report_meta, **overrides):
    opts = {
        'per_page': report_meta['per_page'],
        'page_num': 1,
        'order': report_meta['order'], # "ASC" or "DESC" or None
        # reports can override these values but so far none do.
        # what has happened is that the default of 100 is good enough or pagination is turned off entirely.
        'min_per_page': 1,
        'max_per_page': 100, # ignored if report disables pagination
        'format': report_meta['serialisations'][0] # default format is the first
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
            ensure(val in lst, "value not found in list %s" % (', '.join(lst),))
            return val
        return fn

    # these affect the result of calling the report function
    desc = {
        'page': [p('page', opts['page_num']), ispositiveint],
        'per_page': [p('per-page', opts['per_page']), ispositiveint, inrange(opts['min_per_page'], opts['max_per_page'])],
        'order': [p('order', opts['order']), uppercase, isin([NO_ORDERING, ASC, DESC])],
        'format': [p('format', opts['format']), uppercase, isin(report_meta['serialisations'])]
    }
    if opts['per_page'] == NO_PAGINATION:
        # if no user per-page has been specified + report explicitly defaults to no pagination, return all results
        desc['per_page'] = [NO_PAGINATION]

    # 'params' can be specified in the article metadata.
    # these are given to the report function as keyword parameters
    desc['kwargs'] = report_meta.get('params') or {}

    return render_item(desc, request.GET)

def chop(q, page, per_page, order, order_by):
    """orders and chops a query into pages, returning the total of the original query and a query object"""
    total = q.count()

    # `order` only supported if `order_by` is supported
    # put `order_by=None` in your report to ignore user preferred ordering
    if order_by:
        # switch directions if descending (default ASC)
        if order == DESC:
            order_by = '-' + order_by

        q = q.order_by(order_by)

    # a per-page = 0 means 'all results'
    if per_page > NO_PAGINATION:
        start = (page - 1) * per_page
        end = start + per_page
        q = q[start:end]

    return total, q

def paginate_report_results(reportfn, rargs):
    # TODO: shift this into request_args
    order_by = reportfn.meta.get('order_by')

    report_data = reportfn(**rargs['kwargs']) # results will stay lazy until realised

    # this gives us an opportunity to chop them up and enforce any ordering

    items = report_data['items']
    kwargs = subdict(rargs, ['page', 'per_page', 'order'])
    kwargs['order_by'] = order_by

    if reportfn.meta.get('per_page') == NO_PAGINATION:
        report_data['count'] = None
        report_data['items'] = items
    else:
        report_data['count'], report_data['items'] = chop(items, **kwargs)

    # update the report with any user overrides
    report_data.update(rargs)

    return report_data

def readme_markdown():
    context = {
        'reports': reports.report_meta(),
        'copyright_year': date.today().year,
    }
    return render_to_string('README.md.template', context)

#
# views
#

@render_to("landing.html")
def landing(request):
    return {
        'html_title': 'Observer - article reports',
        'readme': readme_markdown()
    }

def ping(request):
    "returns a test response for monitoring, *never* to be cached"
    resp = HttpResponse('pong', content_type='text/plain; charset=UTF-8')
    resp['Cache-Control'] = 'must-revalidate, no-cache, no-store, private'
    return resp

@profile
def report(request, name, format_hint=None):
    try:
        reportfn = reports.get_report(name)
    except KeyError:
        raise Http404("report not found")
    try:
        # extract and validate any params user has given us.
        overrides = {}
        if format_hint:
            overrides['format'] = format_hint
        rargs = request_args(request, reportfn.meta, **overrides)

        # truncate report results, enforce any user ordering
        report_paginated = paginate_report_results(reportfn, rargs)

        # additional things to pass to whatever is rendering the report.
        # keys here will override any found in the report.
        context = {
            # previously just 'link'
            # in rss there are two 'link' type attributes: a link to the feed itself (rel=self) and a
            # link to the webpage the feed belongs to.
            'self-link': "https://observer.elifesciences.org" + reverse('report', kwargs={'name': name}),

            # per-row value formatter for the requested report format (if any)
            'row-formatter': reportfn.meta.get('row_formatters', {}).get(rargs['format'])
        }
        return reports.format_report(report_paginated, rargs['format'], context)

    except AssertionError as err:
        return HttpResponse("bad request: %s" % err, status=400)

    except BaseException:
        LOG.exception("unhandled exception")
        return HttpResponse("server error attempting to handle your request", status=500)
