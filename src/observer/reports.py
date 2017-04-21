from . import models

def latest_articles():
    """
    the latest articles report:
    * returns -all- articles
    * ordered by the date the first version was published, most recent to least recent
    """
    results = models.Article.objects.all().order_by('-datetime_published')

    return {
        'title': "latest articles",
        'description': "Articles published in eLife",
        'items': results,
    }

def upcoming_articles():
    """
    the upcoming articles report:
    * returns -all- POA articles
    * ordered by the date the first version was published, most recent to least recent
    """
    results = models.Article.objects \
        .filter(status=models.POA) \
        .order_by('-datetime_published')

    return {
        'title': 'upcoming articles',
        'description': 'eLife PAP articles',
        'items': results,
    }

#
#
#

def get_report(name):
    return {
        'latest-articles': latest_articles,
        'upcoming-articles': upcoming_articles,
    }[name]
