import copy
from . import models, rss, csv, logic, json_lines
from .utils import ensure, subdict
from functools import wraps
from collections import OrderedDict
from et3.utils import do_all_if_tuple as mapfn
from .logic import verified_subjects
from slugify import slugify
from django.db.models import Count
from django.db.models.functions import TruncDay
from datetime import datetime

# utils

KNOWN_SERIALISATIONS = JSON, CSV, RSS = 'JSON', 'CSV', 'RSS'
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
        'serialisations': [RSS, CSV],
        # 2018-06-27: changed from 'datetime_version_published' to 'datetime_published'
        # there was a bug where the field 'datetime_version_published' was being set to the 'datetime_published' value
        # this change preserves the behaviour that has been in service for ~12 months now
        'order_by': 'datetime_published',
        'order': DESC,
        'per_page': 28,
        'params': None
    }
    meta.update(kwargs)
    return meta

#
# reports
#

@report(article_meta(
    title="latest articles",
    description="All of the latest articles published at eLife, including in-progress POA (publish-on-accept) articles.",
))
def latest_articles():
    """
    the latest articles report:
    * returns all articles
    * ordered by the date the first version was published, most recent to least recent
    """
    return models.Article.objects.all().order_by('-datetime_published')

@report(article_meta(
    title="latest articles by subject",
    description="Articles published by eLife, filtered by given subjects",
    params={
        'subjects': [lambda req: req.getlist('subject'), tuple, mapfn(slugify), verified_subjects, list],
    }
))
def latest_articles_by_subject(subjects=None):
    """
    the latest articles (by subject) report:
    * returns all articles in the given subject field
    * ordered by the date the first version was published, most recent to least recent
    """
    valid_subjects = models.Subject.objects.values_list('name', flat=True) # not executed until realised
    ensure(subjects, "at least one valid subject must be provided. valid subjects: %s" % ', '.join(valid_subjects))
    return models.Article.objects.all().filter(subjects__name__in=subjects).order_by('-datetime_published')

@report(article_meta(
    title='upcoming articles',
    description="The latest eLife POA (publish-on-accept) articles. These articles are in-progress and their final VOR (version-of-record) is still being produced.",
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

# note: 'article_meta' here works because of similar field names
@report(article_meta(
    title='digests',
    description='The latest eLife digests.',
    serialisations=[RSS],
))
def digests():
    return models.Digest.objects \
        .order_by('-datetime_published')

# note: 'article_meta' here works because of similar field names
@report(article_meta(
    title='labs-posts',
    description='The latest eLife labs-posts.',
    serialisations=[RSS],
))
def labs_posts():
    return models.LabsPost.objects \
        .order_by('-datetime_published')


#
#
#

@report(article_meta(
    title='published research article index',
    description='The dates and times of publication for all _research_ articles published at eLife. If an article had a POA version, the date and time of the POA version is included.',
    serialisations=[CSV, JSON],
    per_page=NO_PAGINATION,
    order_by='msid',
    order=ASC,
    headers=['manuscript_id', 'poa_published_date', 'vor_published_date'],
))
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
        .values_list('msid', 'datetime_poa_published', 'datetime_vor_published')

@report(article_meta(
    title='published article index',
    description='The dates and times of publication for all articles published at eLife. If an article had a POA version, the date and time of the POA version is included.',
    serialisations=[CSV, JSON],
    per_page=NO_PAGINATION,
    order_by='msid',
    order=ASC,
    headers=['manuscript_id', 'poa_published_date', 'vor_published_date'],
))
def published_article_index():
    """
    the published article index report:
    * returns all articles
    * ordered by the manuscript id, smallest to largest (ASC)
    * has just three values per row: msid, date first poa published, date first vor published
    """
    return models.Article.objects \
        .order_by('msid') \
        .values_list('msid', 'datetime_poa_published', 'datetime_vor_published')

@report(article_meta(
    title="daily profile counts",
    description="Daily record of the total number of profiles",
    serialisations=[CSV],
    per_page=NO_PAGINATION,
    order_by='day',
    order=DESC
))
def profile_count():
    """
    the latest profiles count report:
    * returns a daily count of profiles
    * ordered by the day it was captured, most recent to least recent
    """
    return models.Profile.objects \
        .annotate(day=TruncDay('datetime_record_created')) \
        .values('day') \
        .annotate(count=Count('id')) \
        .order_by('-day')

#
# exeter reports
#

def exeter_new_poa_articles_json_row_formatter(row):
    "per-row value formatting for the `exeter_new_poa_articles` report"
    row = list(row)
    row[1] = datetime.date(row[1])
    return row

@report(article_meta(
    title="Exeter, new POA articles",
    description="All POA articles ordered by the date and time they were first published, most recent POA articles to least recent.",
    serialisations=[JSON],
    row_formatters={JSON: exeter_new_poa_articles_json_row_formatter},
    order_by='datetime_poa_published',
    order=DESC,
    headers=['doi', 'first-published-date', 'article-title', 'article-type'],
))
def exeter_new_poa_articles():
    """
    the new POA articles for Exeter report:
    * returns articles that have a POA version
    * ordered by the date and time the first POA version was published, most recent to least recent
    """
    return models.Article.objects \
        .filter(num_poa_versions__gte=1) \
        .order_by('-datetime_poa_published') \
        .values_list('doi', 'datetime_poa_published', 'title', 'type')

def exeter_new_and_updated_vor_articles_json_row_formatter(row):
    "per-row value formatting for the `exeter_new_and_updated_vor_articles` report"
    row = list(row)
    row[1] = datetime.date(row[1])
    row[2] = datetime.date(row[2])
    row[3] = datetime.date(row[3])
    return row

@report(article_meta(
    title="Exeter, new and updated VOR articles",
    description="All new and updated VOR articles ordered by their updated date, most recent VOR articles to least recent.",
    serialisations=[JSON],
    row_formatters={JSON: exeter_new_and_updated_vor_articles_json_row_formatter},
    order_by='datetime_version_published',
    order=DESC,
    headers=['doi',
             'first-published-date', 'latest-published-date', 'first-vor-published-date',
             'article-title', 'article-type'],
))
def exeter_new_and_updated_vor_articles():
    """
    the new and updated VOR articles for Exeter report:
    * returns articles that have at least one VOR version
    * ordered by the date and time of the latest version published, most recent to least recent
    """
    return models.Article.objects \
        .filter(num_vor_versions__gte=1) \
        .order_by('-datetime_version_published') \
        .values_list('doi',
                     'datetime_published', 'datetime_version_published', 'datetime_vor_published',
                     'title', 'type')

#
#
#

def format_report(report_data, serialisation, context):
    # the report has been executed at this point
    known_formats = {
        JSON: json_lines.format_report,
        RSS: rss.format_report,
        CSV: csv.format_report,
    }
    ensure(serialisation in report_data['serialisations'], "unsupported format %r for report %s" % (format, report_data['title']))
    report_data = copy.deepcopy(report_data)
    return known_formats[serialisation](report_data, context)

def known_report_idx():
    return OrderedDict([
        ('latest-articles', latest_articles),
        ('latest-articles-by-subject', latest_articles_by_subject),
        ('upcoming-articles', upcoming_articles),
        ('digests', digests),
        ('labs-posts', labs_posts),
        ('published-article-index', published_article_index),
        ('published-research-article-index', published_research_article_index),
        ('profile-count', profile_count),
        ('exeter-new-poa-articles', exeter_new_poa_articles),
        ('exeter-new-and-updated-vor-articles', exeter_new_and_updated_vor_articles),
    ])

def _report_meta(reportfn):
    labels = {
        'datetime_published': 'date and time this article was _first_ published',
        # poa published will always be the same as first published
        'datetime_poa_published': 'date and time this article was _first_ published',
        'datetime_version_published': 'date and time this _version_ of the article was published',
        'msid': 'eLife manuscript ID',
        'day': 'year, month and day',
        DESC: '_most_ recent to least recent',
        ASC: '_least_ recent to most recent'
    }
    url_to_kwarg_params = {
        'subjects': ('subject', ', '.join(logic.simple_subjects()))
    }
    meta = copy.deepcopy(reportfn.meta)
    meta['params'] = list((meta.get('params') or {})) # remove the param wrangling description
    meta['http_params'] = list(subdict(url_to_kwarg_params, meta['params']).values())
    meta['order_by_label'] = labels[meta['order_by']]
    meta['order_label'] = labels[meta['order']]
    return meta

def report_meta():
    return OrderedDict([(name, _report_meta(fn)) for name, fn in known_report_idx().items()])

def get_report(name):
    return known_report_idx()[name]
