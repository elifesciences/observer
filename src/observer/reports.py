
def latest_articles():
    return {
        'title': "latest articles",
        'description': "Articles published in eLife",
        'items': [],
    }

def upcoming_articles():
    return {
        'title': 'upcoming articles',
        'description': 'eLife PAP articles',
        'items': [],
    }

#
#
#

def get_report(name):
    return {
        'latest-articles': latest_articles,
        'upcoming-articles': upcoming_articles,
    }[name]
