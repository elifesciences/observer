#from . import models
from feedgen.feed import FeedGenerator
import logging

LOG = logging.getLogger(__name__)

try:
    import utils
except ImportError:
    from . import utils

def set_obj_attrs(obj, data):
    def set(key, val):
        setter = getattr(obj, key)
        if isinstance(val, list):
            for row in val:
                setter(row)
        else:
            getattr(obj, key)(val)
    [set(key, val) for key, val in data.items()]

def mkfeed(report):
    fg = FeedGenerator()

    # extract the report bits
    data = utils.subdict(report, ['id', 'title', 'description', 'link'])

    # rename some bits
    # data = utils.rename(data, [('owner', 'author')]) # for example

    # wrangle some more bits
    data['link'] = {'href': 'https://elifesciences.org', 'rel': 'self'}

    # add some defaults
    data['language'] = 'en'

    # set the attributes
    # http://lkiesow.github.io/python-feedgen/#create-a-feed
    set_obj_attrs(fg, data)

    return fg

def add_entry(fg, item):
    entry = fg.add_entry()
    set_obj_attrs(entry, item)

def add_many_entries(fg, item_list):
    [add_entry(fg, item) for item in utils.take(250, item_list)]


#
#
#

def article_to_rss_entry(art):
    "coerce a models.Article object to something suitable for the feedgen entry model"
    item = utils.to_dict(art)

    # extract the entry bits
    item = utils.subdict(item, ['id', 'doi', 'title', 'abstract', 'datetime_published'])  # , 'description', 'author', 'category', 'guid', 'pubdate'])

    # rename some bits
    utils.renkeys(item, [
        ('doi', 'link'),
        ('abstract', 'description'),
        ('datetime_published', 'pubdate'),
    ])

    # wrangle
    item['id'] = "https://dx.doi.org/" + item['link']
    item['link'] = {'href': "https://beta.elifesciences.org/articles/" + utils.pad_msid(art.msid)}
    
    item['author'] = {'name': art.author_name, 'email': art.author_email}
    '''
    email = art.author_email
    item['author'] = [
        {'name': 'Alicia N McMurchy', 'email': email},
        {'name': 'Przemyslaw Stempor', 'email': email},
        {'name': 'Tessa Gaarenstroom'},
    ]
    '''
    return item

def format_report(report, context):
    try:
        report.update(context) # yes, this nukes any conflicting keys in the report
        report['title'] = 'eLife: ' + report['title']
        feed = mkfeed(report)
        add_many_entries(feed, map(article_to_rss_entry, report['items'])) # deliberate use of lazy map
        return feed.rss_str(pretty=True).decode('utf-8')
    except BaseException as e:
        LOG.exception("unhandled exception formatting report %r", report)
        raise

#
#
#

if __name__ == '__main__':
    demo_report = {
        'title': 'a demonstration',
        'id': 'data.elifesciences.org/latest.rss',
        'link': 'example.org',
        'description': 'this is a simple asdf'
    }
    feed = mkfeed(demo_report)
    add_entry(feed, {'title': 'item title', 'link': 'some id'})
    print(feed.rss_str(pretty=True).decode('utf8'))
