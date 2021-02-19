from django.conf import settings
from django.http import HttpResponse
from feedgen.feed import FeedGenerator
import logging
from . import utils, models
import feedgen.ext.base
import feedgen.util

LOG = logging.getLogger(__name__)

def attr_name(elem):
    "the special object attribute name that follows the naming of all other feedgen extensions"
    return "_feedlyelem_%s" % elem

class FeedlyBaseExtension(feedgen.ext.base.BaseExtension):
    _ns = 'http://webfeeds.org/rss/1.0'

    def setup(self):
        for elem, _ in self.elem_list:
            setattr(self, attr_name(elem), None) # => `self._feedlyelem_accentColor = None`

        def setter_template(inst, elem):
            """extending a BaseExtension object means writing a tonne of boilerplate accessors.
            this creates setters for each of the `self.elem_list` list of elements."""
            attr = attr_name(elem)

            def setter(value, replace=True):
                if value is not None:
                    if not isinstance(value, list):
                        value = [value]
                    if replace or not getattr(inst, attr):
                        setattr(inst, attr, [])
                    setattr(self, attr, getattr(self, attr) + value)
                return getattr(self, attr)
            return setter

        for elem, _ in self.elem_list:
            setattr(self, elem, setter_template(self, elem))

    def extend_ns(self):
        return {'webfeeds': self._ns}

    # from: https://github.com/lkiesow/python-feedgen/blob/master/feedgen/ext/dc.py#L47
    def _extend_xml(self, xml_element):
        for elem, attr_list in self.elem_list:
            for val in getattr(self, attr_name(elem)) or []:
                node = feedgen.util.xml_elem('{%s}%s' % (self._ns, elem), xml_element)
                if attr_list:
                    assert isinstance(val, dict), "element %r has attributes that must be set: %s" % (elem, attr_list)
                    for attr in attr_list:
                        node.set(attr, val[attr])
                else:
                    node.text = val

    def extend_atom(self, element):
        self._extend_xml(element)
        return element

    def extend_rss(self, element):
        self._extend_xml(element)
        return element

class Feedly(FeedlyBaseExtension):
    def __init__(self):
        self.elem_list = [
            # (elem, attr-list)
            ('accentColor', []),
            ('analytics', ['id', 'engine']),
            ('cover', ['image']),
            ('wordmark', []),
            ('icon', []),
            ('partial', []),
            ('deprecated', []),
            ('promotion', [])
        ]
        self.setup()

    def extend_rss(self, feed):
        """extends the RSS 'channel' element rather than the 'rss' element"""
        channel = feed[0]
        self._extend_xml(channel)
        return feed

class FeedlyEntry(FeedlyBaseExtension):
    def __init__(self):
        self.elem_list = [
            ('featuredImage', ['url', 'height', 'width', 'type']),
        ]
        self.setup()

#
#
#

def set_obj_attrs(obj, data):
    """given a FeedGen `obj`, insert given `data` into it.
    for each key in given `data` there should be a corresponding 'setter' in the `obj`.
    FeedGen object setters support namespaces as well as lists of values.
    Works for simple values but doesn't support setters with additional attributes (like `link`)."""
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
            setter(val)
    [_set(obj, key, val) for key, val in data.items()]

def mkfeed(report):
    "returns an initialised FeedGen object with channel-level attributes set"
    fg = FeedGenerator()
    fg.load_extension('dc')
    fg.register_extension(**{'namespace': 'webfeeds',
                             'extension_class_feed': Feedly,
                             'extension_class_entry': FeedlyEntry})

    # extract the report bits
    # also serves as a whitelist of allowed elements
    data = utils.subdict(report, ['id', 'title', 'description', 'link', 'lastBuildDate',
                                  'webfeeds:accentColor', 'webfeeds:analytics', 'webfeeds:cover', 'webfeeds:icon', 'webfeeds:wordmark'
                                  ])

    # rename some bits
    # data = utils.rename(data, [('owner', 'author')]) # for example

    # link: "The URL to the HTML website corresponding to the channel" for example "http://www.goupstate.com/"
    # https://www.rssboard.org/rss-specification
    data['link'] = data.get('link') or {'href': 'https://elifesciences.org'}

    # add some defaults
    data['language'] = 'en'
    data['generator'] = 'observer (using python-feedgen)'

    # the setter magic will work for *most* of the attributes *most* of the time,
    # but there are some exceptions.
    # order matters as well, so the below doesn't work if called *after* the setter magic.
    if 'self-link' in report:
        fg.link(href=report['self-link'], rel='self', replace=False)

    default_analytics = {'id': settings.FEEDLY_GA_MEASUREMENT_ID, 'engine': 'GoogleAnalytics'}
    data['webfeeds:analytics'] = data.get('webfeeds:analytics', default_analytics)

    # set the attributes
    # http://lkiesow.github.io/python-feedgen/#create-a-feed
    set_obj_attrs(fg, data)

    return fg

def add_entry(fg, item):
    "adds a single `item` to the given FeedGen object `fg`."
    # default order of insertion changed in 0.6 to 'prepend'
    # https://github.com/lkiesow/python-feedgen/blob/1b301f67adf4e2f0367579a6c41f72ee524b9380/feedgen/feed.py#L999
    entry = fg.add_entry(order='append')
    set_obj_attrs(entry, item)
    return entry

def add_many_entries(fg, item_list):
    """adds each item in `item_list` to the given FeedGen object `fg`.
    Any lazy sequences are realised."""
    # why 250? pagination of (lazy) Django QuerySets should have happened by this point (max 100),
    # but just in case ...
    [add_entry(fg, item) for item in utils.take(250, item_list)]

# articles

def article_to_rss_entry(art):
    "convert a single Article object to a data structure suitable for FeedGen coercion."
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
    item['link'] = {'href': art.get_absolute_url()}
    item['author'] = [{'name': a.name, 'email': art.author_email} for a in art.authors.all()]
    item['category'] = [{'term': subject.name, 'label': subject.label} for subject in art.subjects.all()]
    item['dc:dc_date'] = utils.ymdhms(item['pubDate'])
    return item

def article_list_to_rss_entry_list(queryset):
    "converts many Article objects to a list of data structures suitable for FeedGen coercion."
    queryset = queryset.prefetch_related('subjects', 'authors')
    return map(article_to_rss_entry, queryset) # deliberate use of lazy `map`

# content

def content_to_rss_entry(content):
    "converts a single Content object to a data structure suitable for FeedGen coercion."
    data = utils.to_dict(content)

    item = utils.subdict(data, [
        'id', 'title', 'description',
        'datetime_published', 'datetime_updated'])
    utils.renkeys(item, [
        ('datetime_published', 'pubDate'),
        ('datetime_updated', 'updated'),
    ])
    self_link = content.get_absolute_url()
    item['id'] = self_link
    item['link'] = {'href': self_link}
    item['dc:dc_date'] = utils.ymdhms(item['pubDate'])
    item['category'] = [{'term': cat.name, 'label': cat.label} for cat in content.categories.all()]

    # todo: add content.content_type to 'categories' ...?

    # content has an image available, generate a thumbnail with a max width or height depending on orientation.
    if content.image_uri:
        max_xy = 800
        thumbnail_width, thumbnail_height = utils.thumbnail_dimensions(max_xy, content.image_width, content.image_height)
        iiif_url = utils.iiif_thumbnail_link(content.image_uri, thumbnail_width, thumbnail_height)
        item['webfeeds:featuredImage'] = {'url': iiif_url,
                                          'height': str(thumbnail_height),
                                          'width': str(thumbnail_width),
                                          'type': "image/jpeg"}
    return item

def content_to_rss_entry_list(queryset):
    "converts a QuerySet of Content objects to a list of datastructures suitable for FeedGen coercion"
    return map(content_to_rss_entry, queryset)

def _format_report(report, context):
    "generates an RSS feed from the given `report` and `context` data, returning XML content as a string"
    report.update(context) # yes, this nukes any conflicting keys in the report
    report['title'] = 'eLife: ' + report.get('title', 'untitled')
    feed = mkfeed(report)

    dispatch = {
        models.Article: article_list_to_rss_entry_list,
        models.Content: content_to_rss_entry_list,

        # if we're given a map of data, assume it's already in the shape we want it in
        dict: lambda x: x
    }

    items = report.get('items', [])
    obj_type = dict
    if hasattr(items, 'model'):
        obj_type = items.model
    items = dispatch[obj_type](items)

    add_many_entries(feed, items)
    return feed.rss_str(pretty=True).decode('utf-8')

def format_report(report, context):
    "generates an RSS feed from the given `report` and `context` data, returning an HttpResponse."
    return HttpResponse(_format_report(report, context), content_type='text/xml')
