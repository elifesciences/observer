from django.http import HttpResponse
from django.db import models
from feedgen.feed import FeedGenerator
import logging
from . import utils

LOG = logging.getLogger(__name__)

def set_obj_attrs(obj, data):
    """given a FeedGen `obj`, insert given `data` into it.
    for each key in given `data` there should be a corresponding 'setter' in the `obj`.
    FeedGen object setters support namespaces as well as lists of values."""
    def _set(obj, key, val):
        if ':' in key:
            # namespaced setter, assumes ns has been loaded
            ns, key = key.split(':', 1)
            obj = getattr(obj, ns)
        setter = getattr(obj, key)
        if isinstance(val, list):
            for row in val:
                setter(row)
        else:
            getattr(obj, key)(val)
    [_set(obj, key, val) for key, val in data.items()]

def mkfeed(report):
    fg = FeedGenerator()
    fg.load_extension('dc')
    #fg.load_extension('webfeeds')

    # extract the report bits
    data = utils.subdict(report, ['id', 'title', 'description', 'link', 'lastBuildDate'])

    # rename some bits
    # data = utils.rename(data, [('owner', 'author')]) # for example

    # link: "The URL to the HTML website corresponding to the channel" for example "http://www.goupstate.com/"
    # https://www.rssboard.org/rss-specification
    data['link'] = data.get('link') or {'href': 'https://elifesciences.org'} #, 'rel': 'self'}

    # add some defaults
    data['language'] = 'en'
    data['generator'] = 'observer (using python-feedgen)'

    # set the attributes
    # http://lkiesow.github.io/python-feedgen/#create-a-feed
    set_obj_attrs(fg, data)

    return fg

def add_entry(fg, item):
    # default order of insertion changed in 0.6 to 'prepend'
    # https://github.com/lkiesow/python-feedgen/blob/1b301f67adf4e2f0367579a6c41f72ee524b9380/feedgen/feed.py#L999
    entry = fg.add_entry(order='append')
    set_obj_attrs(entry, item)
    return entry

def add_many_entries(fg, item_list):
    # note: what is the point of the laziness if this list construction realises it?
    # was it a py2 -> py3 conversion error?
    [add_entry(fg, item) for item in utils.take(250, item_list)]


#
#
#

def article_to_rss_entry(art):
    "serialise a models.Article object to an rss item entry"
    item = utils.to_dict(art)

    # extract the entry bits
    item = utils.subdict(item, ['id', 'doi', 'title', 'abstract', 'datetime_published'])  # , 'description', 'author', 'category', 'guid', 'pubdate'])

    # rename some bits
    utils.renkeys(item, [
        ('doi', 'link'),
        ('abstract', 'description'),
        ('datetime_published', 'pubDate'),
    ])

    # wrangle
    item['id'] = "https://dx.doi.org/" + item['link']
    item['link'] = {'href': "https://elifesciences.org/articles/" + utils.pad_msid(art.msid)}
    item['author'] = [{'name': a.name, 'email': art.author_email} for a in art.authors.all()]
    item['category'] = [{'term': c.name, 'label': c.label} for c in art.subjects.all()]
    item['dc:dc_date'] = utils.ymdhms(item['pubDate'])
    return item

def _format_report(report, context):
    "formats given report as RSS xml"
    report.update(context) # yes, this nukes any conflicting keys in the report
    report['title'] = 'eLife: ' + report.get('title', 'untitled')
    feed = mkfeed(report)
    items = report.get('items', [])

    if isinstance(items, models.QuerySet):
        query = items # this is a `models.SomeModel.objects.foo` queryset
        query = query.prefetch_related('subjects', 'authors')
        items = map(article_to_rss_entry, query) # deliberate use of lazy `map`

    add_many_entries(feed, items)
    return feed.rss_str(pretty=True).decode('utf-8')

def format_report(report, context):
    return HttpResponse(_format_report(report, context), content_type='text/xml')
