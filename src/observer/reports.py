import itertools
import copy
from . import models, rss, sitemap, csv, logic, json_lines
from .utils import ensure, subdict, utcnow
from functools import wraps
from collections import OrderedDict
from et3.utils import do_all_if_tuple as mapfn
from .logic import verified_subjects
from slugify import slugify
from django.db.models import Count
from django.db.models.functions import TruncDay
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connection

# utils

# todo: separate 'known serialisations' from 'serialisation extension'.
# I'm conflating the two and it's going to bite me soon.
KNOWN_SERIALISATIONS = JSON, CSV, RSS, SITEMAP = 'JSON', 'CSV', 'RSS', 'XML'

# mapping of known serialisations to their filename extensions.
# used in report format hinting
# SERIALISATION_EXT = {
#    JSON: "json",
#    CSV: "csv",
#    RSS: "rss", # '.xml' works as well. should this be a list?
#    SITEMAP: "xml"
# }

NO_PAGINATION = 0
NO_ORDERING = "NONE"
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
    "returns report metadata suitable for most `models.Article` reports"
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

def content_meta(**kwargs):
    "returns report metadata suitable for most `models.Content` reports"
    meta = {
        'serialisations': [RSS],
        'per_page': 28,
        'params': None,
        'order': NO_ORDERING,

        # content reports use their own, sometimes complex, ordering
        # don't allow user defined ordering and if anything asks, it's just 'datetime_published'
        'order_label_key': DESC,
        'order_by_label_key': 'datetime_published',
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

@report(content_meta(
    title='digests',
    description='The latest eLife digests.',
))
def digests():
    return models.Content.objects \
        .filter(content_type=models.DIGEST) \
        .order_by('-datetime_published')

@report(content_meta(
    title='labs-posts',
    description='The latest eLife labs-posts.',
))
def labs_posts():
    return models.Content.objects \
        .filter(content_type=models.LABS_POST) \
        .order_by('-datetime_published')

@report(content_meta(
    title='community',
    description='The latest eLife community content.',
))
def community():
    return models.Content.objects \
        .filter(content_type__in=models.COMMUNITY_CONTENT_TYPE_LIST) \
        .order_by('-datetime_published', 'title')

@report(content_meta(
    title='interviews',
    description='The latest eLife interviews.',
))
def interviews():
    return models.Content.objects \
        .filter(content_type=models.INTERVIEW) \
        .order_by('-datetime_published')

@report(content_meta(
    title='collections',
    description='The latest eLife collections.',
))
def collections():
    return models.Content.objects \
        .filter(content_type=models.COLLECTION) \
        .order_by('-datetime_published')

@report(content_meta(
    title='blog-articles',
    description='The latest eLife blog articles.',
))
def blog_articles():
    return models.Content.objects \
        .filter(content_type=models.BLOG_ARTICLE) \
        .order_by('-datetime_published')

@report(content_meta(
    title='features',
    description='The latest eLife featured articles.',
))
def features():
    return models.Content.objects \
        .filter(content_type=models.FEATURE) \
        .order_by('-datetime_published')

@report(content_meta(
    title='podcasts',
    description='The latest eLife podcast episodes.',
))
def podcasts():
    return models.Content.objects \
        .filter(content_type=models.PODCAST) \
        .order_by('-datetime_published')

@report(content_meta(
    title='magazine',
    description='The latest eLife magazine content',
))
def magazine():
    return models.Content.objects \
        .filter(content_type__in=models.MAGAZINE_CONTENT_TYPE_LIST) \
        .order_by('-datetime_published', 'title')

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

def sitemap__article_data():
    "returns a list of pre-formatted article data designed for the sitemap."
    psql_sql = r"""SELECT
'https://elifesciences.org/articles/' || LPAD(msid::text, 5, '0'),
to_char(datetime_version_published, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
FROM
articles
ORDER BY
msid DESC"""
    # 'substr' here is used to zero-pad the msid
    sqlite_sql = r"""SELECT
'https://elifesciences.org/articles/' || substr('00000'||msid,-5),
strftime('%Y-%m-%d\T%H:%M:%S\Z', datetime_version_published)
FROM
articles
ORDER BY
msid DESC"""
    db = settings.DATABASES['default']['ENGINE']
    sql = sqlite_sql if db == "django.db.backends.sqlite3" else psql_sql
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()

@report(meta={
    'title': 'sitemap',
    'description': 'generates a complete listing of journal content as a sitemap.xml file',
    'serialisations': [SITEMAP],
    'per_page': NO_PAGINATION,
    'order': NO_ORDERING,
    'order_by_label_key': 'mixed',
    'order_label_key': 'msid'
})
def sitemap_report():
    """'sitemap.xml' as served up by the journal.
    should contain a complete listing of journal content for reports to visit."""
    #article_q = models.Article.objects\
    #    .only("msid", "datetime_version_published")
    article_q = sitemap__article_data()

    content_q = models.Content.objects\
        .filter(content_type__in=models.NON_ARTICLE_CONTENT_TYPE_LIST)\
        .only("id", "datetime_updated", "datetime_published", "content_type")

    presspackage_q = models.PressPackage.objects\
        .only("id", "updated", "published")

    return itertools.chain(
        article_q,
        content_q,
        presspackage_q)

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
# EBSCO reports
#

def ebsco_new_and_updated_vor_articles_json_row_formatter(article_obj):
    "per-row value formatting for the `ebsco_new_and_updated_vor_articles` report"
    # has to match headers
    field_list = [
        'doi',
        'datetime_published', 'datetime_vor_published',
        'title', 'type'
    ]
    row = [getattr(article_obj, field) for field in field_list] + [article_obj.get_pdf_url()]
    row[1] = datetime.date(row[1]) # datetime_published
    row[2] = datetime.date(row[2]) # datetime_vor_published
    return row

@report(article_meta(
    title="EBSCO, new VOR articles",
    description="All new VOR articles ordered by their  date, most recent VOR articles to least recent.",
    serialisations=[JSON, CSV],
    row_formatters={JSON: ebsco_new_and_updated_vor_articles_json_row_formatter,
                    CSV: ebsco_new_and_updated_vor_articles_json_row_formatter
                    },
    order_by='datetime_vor_published',
    order=DESC,
    headers=['doi',
             'first-published-date', 'first-vor-date',
             'article-title', 'article-type', 'article-pdf-url'],
))
def ebsco_new_and_updated_vor_articles():
    """
    the new and updated VOR articles for Exeter report:
    * returns articles that have at least one VOR version
    * ordered by the date and time of the first VOR version published, most recent to least recent
    """
    one_day_ago = utcnow() - timedelta(days=1)
    return models.Article.objects \
        .filter(num_vor_versions__gte=1) \
        .exclude(datetime_vor_published__gt=one_day_ago) \
        .order_by('-datetime_vor_published')

#
#
#

def format_report(report_data, serialisation, context):
    # the report has been executed at this point
    known_formats = {
        JSON: json_lines.format_report,
        RSS: rss.format_report,
        CSV: csv.format_report,
        SITEMAP: sitemap.format_report,
    }
    ensure(serialisation in report_data['serialisations'], "unsupported format %r for report %s" % (format, report_data['title']))
    report_data = copy.deepcopy(report_data) # this is expensive!
    return known_formats[serialisation](report_data, context)

def known_report_idx():
    "a mapping of a report's name as it appears in the URL to a function that will generate the data for that report."
    # [(/report/$name, reportfn), ...]
    return OrderedDict([
        ('latest-articles', latest_articles),
        ('latest-articles-by-subject', latest_articles_by_subject),
        ('upcoming-articles', upcoming_articles),
        ('digests', digests),
        ('labs-posts', labs_posts),
        ('community', community),
        ('interviews', interviews),
        ('collections', collections),
        ('blog-articles', blog_articles),
        ('features', features),
        ('podcasts', podcasts),
        ('magazine', magazine),
        ('published-article-index', published_article_index),
        ('published-research-article-index', published_research_article_index),
        ('profile-count', profile_count),
        ('exeter-new-poa-articles', exeter_new_poa_articles),
        ('exeter-new-and-updated-vor-articles', exeter_new_and_updated_vor_articles),
        ('sitemap', sitemap_report),
        ('ebsco-new-and-updated-vor-articles', ebsco_new_and_updated_vor_articles),
    ])

def _report_meta(reportfn):
    """normalises the metadata attached to a report function `reportfn`.
    attaches friendly descriptions of report configuration suitable for use in the README."""
    labels = {
        'datetime_published': 'date and time this article was _first_ published',
        # poa published will always be the same as first published
        'datetime_poa_published': 'date and time this article was _first_ published',
        'datetime_vor_published': 'date and time the VOR of this article was published',
        'datetime_version_published': 'date and time this _version_ of the article was published',
        'msid': 'eLife manuscript ID',
        'day': 'year, month and day',
        DESC: '_most_ recent to least recent',
        ASC: '_least_ recent to most recent',
        'mixed': 'mixed, depending on content type'
    }
    url_to_kwarg_params = {
        'subjects': ('subject', ', '.join(logic.simple_subjects()))
    }
    meta = copy.deepcopy(reportfn.meta)
    meta['params'] = list((meta.get('params') or {})) # remove the param wrangling description
    meta['http_params'] = list(subdict(url_to_kwarg_params, meta['params']).values())

    # not all reports support `order_by` and `order` (see `NO_ORDERING`).
    # in these cases a `order_by_label_key` and `order_label_key` can be specified to find a description.
    # these descriptions are used in the README.
    meta['order_by_label'] = labels[meta.get('order_by_label_key') or meta.get('order_by')]
    meta['order_label'] = labels[meta.get('order_label_key') or meta['order']]
    return meta

def report_meta():
    """returns an ordered map of `{report-name: report-metadata, ...}`
    Used in generating the body of README file."""
    return OrderedDict([(name, _report_meta(fn)) for name, fn in known_report_idx().items()])

def get_report(name):
    """fetches a given report by its report `name`.
    report functions are associated to a name in the `known_report_idx` function."""
    return known_report_idx()[name]
