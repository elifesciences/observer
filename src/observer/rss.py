from feedgen.feed import FeedGenerator
import utils

def set_obj_attrs(obj, data):
    def set(key, val):
        getattr(obj, key)(val)
    [set(key, val) for key, val in data.items()]

def mkfeed(report):
    fg = FeedGenerator()

    # extract the report bits
    data = utils.subdict(report, ['id', 'title', 'description', 'link'])

    # rename some bits
    # data = utils.rename(data, [('owner', 'author')]) # for example

    # wrangle some more bits
    data['link'] = {'href': data['link'], 'rel': 'self'}
    
    # add some defaults
    data['language'] = 'en'
    
    # set the attributes
    # http://lkiesow.github.io/python-feedgen/#create-a-feed
    set_obj_attrs(fg, data)

    return fg

def add_entry(fg, item):
    entry = fg.add_entry()

    # extract the entry bits
    data = utils.subdict(item, ['id', 'link', 'title', 'description', 'author', 'category', 'guid', 'pubdate'])

    # rename some bits
    # ...

    # wrangle
    # data['dc:date'] = ...
    data['link'] = {'href': data['link']}

    set_obj_attrs(entry, data)

def add_many_entries(fg, item_list):
    [add_entry(fg, item) for item in item_list]
    
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
