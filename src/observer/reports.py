from . import models
from functools import wraps

# utils

KNOWN_SERIALISATIONS = JSON, CSV, RSS = 'JSON', 'CSV', 'RSS'

SERIALISATIONS = 'serialisations'
ORDER, ORDER_BY = 'order', 'order_by'
PER_PAGE = 'per_page'
NO_PAGINATION = 0
DESC, ASC = 'DESC', 'ASC'

def report(meta):
    "attaches metadata to a report. metadata is returned as the results including 'items' key"
    def wrap1(fn):
        @wraps(fn)
        def wrap2(*args, **kwargs):
            meta['items'] = fn(*args, **kwargs)
            return meta
        setattr(wrap2, 'meta', meta) # ll report.meta.title, report.meta.per_page
        return wrap2
    return wrap1

def article_meta(**kwargs):
    "returns standard metadata most reports returning models.Article objects will need"
    meta = {
        SERIALISATIONS: [RSS, CSV],
        ORDER_BY: 'datetime_version_published',
        ORDER: DESC,
        PER_PAGE: 28,
    }
    meta.update(kwargs)
    return meta

#
# reports
#

@report(article_meta(
    title="latest articles",
    description="Articles published in eLife",
))
def latest_articles():
    """
    the latest articles report:
    * returns -all- articles
    * ordered by the date the first version was published, most recent to least recent
    """
    return models.Article.objects.all().order_by('-datetime_published')


@report(article_meta(
    title='upcoming articles',
    description='eLife PAP articles',
))
def upcoming_articles():
    """
    the upcoming articles report:
    * returns -all- POA articles
    * ordered by the date the first version was published, most recent to least recent
    """
    return models.Article.objects \
        .filter(status=models.POA) \
        .order_by('-datetime_published')

@report({
    'title': 'published research article index',
    'description': 'the POA and VOR dates for all published research articles',
    SERIALISATIONS: [CSV],
    PER_PAGE: NO_PAGINATION,
    ORDER_BY: 'msid',
    ORDER: ASC,

    #'headers': ['msid', 'poa', 'vor'] # published.csv on lax has no headers, but this could be specified here?
})
def published_research_article_index():
    """
    the published research article index report:
    * returns all articles EXCEPT commentaries, editorials, book reviews, discussions and corrections
    * ordered by the manuscript id, smallest to largest (ASC)
    * has just three values per row: msid, date first poa published, date first vor published
    """
    return models.Article.objects \
        .exclude(type__in=['article-commentary', 'editorial', 'book-review', 'discussion', 'correction']) \
        .order_by('msid') \
        .values('msid', 'datetime_poa_published', 'datetime_vor_published')

#
#
#

# replace these with some fancy introspection of the reports module

def known_report_idx():
    return {
        'latest-articles': latest_articles,
        'upcoming-articles': upcoming_articles,
        'published-research-article-index': published_research_article_index,
    }

def get_report(name):
    return known_report_idx()[name]
