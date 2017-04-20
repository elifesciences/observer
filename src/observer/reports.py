
def latest_articles():
    return {
        'title': "latest articles",
        'description': "Articles published in eLife",
        'items': [],
    }


def get_report(name):
    return {
        'latest-articles': latest_articles
    }[name]
