from io import StringIO
from observer import models, utils
from django.http import HttpResponse  # , StreamingHttpResponse

xml_doc_header = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n"""

xml_doc_footer = """</urlset>"""

def url_elem(loc_str, mod_str):
    "returns a snippet of xml with the given `loc_str` as the `loc` element and `mod_str` as `lastmod` element."
    return "  <url>\n    <loc>" + loc_str + "</loc>\n    <lastmod>" + mod_str + "</lastmod>\n  </url>\n"

def render(data_pair_list):
    "returns a generator function that first yields the header, then each body item in `data_pair_list`, then the footer"
    yield xml_doc_header
    for loc_str, mod_str in data_pair_list:
        yield url_elem(loc_str, mod_str)
    yield xml_doc_footer

def coerce(item):
    "attempts to convert given `item` into a simple pair of (url, datetime string) suitable for `url_elem`"
    if isinstance(item, tuple):
        return item # passed through without modification
    if isinstance(item, dict):
        return (item['url'], utils.ymdhms(item['last-modified']))
    if isinstance(item, models.Article):
        return (item.get_absolute_url(), utils.ymdhms(item.datetime_version_published))
    if isinstance(item, models.PressPackage):
        return (item.get_absolute_url(), utils.ymdhms(item.updated or item.published))
    if isinstance(item, models.Content):
        return (item.get_absolute_url(), utils.ymdhms(item.datetime_updated or item.datetime_published))
    raise ValueError("item %r cannot be coerced to a pair of (url, last-modified) values" % (item,))

def _format_report(report, context):
    "generates a `sitemap.xml` document from the given `report` and its `context` data, returning a generator."
    data_pair_list = map(coerce, report['items'])
    return render(data_pair_list)

def realise(formatted_report, fn):
    "consumes `formatted_report`, calling `fn` on each item until it is empty"
    all(fn(x) for x in formatted_report)

def realise_as_string(formatted_report):
    "consumes `formatted_report` returning a simple newline delimited string"
    with StringIO() as buffer:
        realise(formatted_report, buffer.write)
        return buffer.getvalue()

def format_report(report, context):
    "generates a `sitemap.xml` from the given `report` and `context` data, returning an HttpResponse."
    # streaming responses affect cache headers
    # return StreamingHttpResponse(_format_report(report, context), content_type='text/xml')
    return HttpResponse(_format_report(report, context), content_type='text/xml')
