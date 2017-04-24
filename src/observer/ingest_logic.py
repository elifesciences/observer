import os
#from os.path import join
from django.db import transaction
import json
from et3 import render
from et3.extract import path as p
from . import utils, models
from .utils import lmap, lfilter, create_or_update, ensure
from kids.cache import cache
import logging
from django.conf import settings

LOG = logging.getLogger(__name__)

POA, VOR = 'poa', 'vor'
EXCLUDE_ME = 0xDEADBEEF

class StateError(Exception):
    pass

def doi2msid(doi):
    "doi to manuscript id used in EJP"
    prefix = '10.7554/eLife.'
    return doi[len(prefix):].lstrip('0')

def msid2doi(msid):
    assert len(str(msid)) <= 5, "given msid is too long: %r" % msid
    assert utils.isint(msid), "given msid must be an integer: %r" % msid
    return '10.7554/eLife.%05d' % int(msid)

def wrangle_dt_published(art):
    if art['version'] == 1:
        return art['published']
    # we can't determine the original datetime published from the data
    # return a marker that causes this key+val to be removed in post
    return EXCLUDE_ME

def getartobj(msid):
    try:
        return models.Article.objects.get(msid=msid)
    except models.Article.DoesNotExist:
        return None

def calc_num_poa(art):
    "how many POA versions of this article have we published?"
    if art['status'] == POA:
        return art['version']
    # vor
    elif art['version'] == 1:
        # the first version is a VOR, there are no POA versions
        return 0
    # we can't calculate this, exclude from update
    return EXCLUDE_ME

def calc_num_vor(args):
    "how many VOR versions of this article have we published?"
    art, artobj = args
    if art['status'] == VOR:
        if art['version'] == 1:
            return 1
        # ver=3, numpoa=1, then num vor must be 2
        return art['version'] - artobj.num_poa_versions
    return EXCLUDE_ME

@cache
def ao(ad):
    "returns the stored Article Object (ao) for the given row"
    msid = ad['id']
    return getartobj(msid)

def ado(ad):
    "returns the Article Data and stored article Object as a pair"
    return ad, ao(ad)

def todt(v):
    if v == EXCLUDE_ME:
        return v
    return utils.todt(v)

# shift to et3?
def _or(v):
    def fn(x):
        return x if x else v
    return fn

calc_sub_to_acc = 0
calc_sub_to_rev = 0
calc_sub_to_prod = 0
calc_sub_to_pub = 0
calc_acc_to_rev = 0
calc_acc_to_prod = 0
calc_acc_to_pub = 0
calc_rev_to_prod = 0
calc_rev_to_pub = 0
calc_prod_to_pub = 0

def calc_pub_to_current(v):
    art_struct, art_obj = v
    if not art_obj: # or art_struct['version'] == 1:
        # article doesn't exist yet must be a v1, or
        # we're reingesting v1 again
        return 0
    v1dt = art_obj.datetime_published
    vNdt = todt(art_struct['published'])
    return (vNdt - v1dt).days

#
#
#

def calc_poa_published(args):
    "returns the date the poa was first published. None if never published"
    art_struct, art_obj = args
    if art_struct['version'] == 1 and art_struct['status'] == models.POA:
        # ideal case, v1 POA
        return art_struct['published']
    # can't calculate, ignore
    return EXCLUDE_ME

def calc_vor_published(args):
    "returns the date the poa was first published. None if never published"
    art_struct, art_obj = args
    if art_struct['version'] == 1 and art_struct['status'] == models.VOR:
        # ideal case
        return art_struct['published']
    # consult previous obj
    if art_obj and art_obj.status == models.POA and art_struct['status'] == models.VOR:
        return art_struct['published']
    # can't calculate, ignore
    return EXCLUDE_ME

def has_key(key):
    def fn(v):
        return key in v
    return fn

def find_author(art):
    authors = lfilter(lambda a: 'emailAddresses' in a, art.get('authors', []))
    if authors:
        return authors[0]
    return {}

def find_author_name(art):
    author = find_author(art)
    nom = author.get('name', None)
    if isinstance(nom, dict):
        return nom['preferred']
    return nom

DESC = {
    #'journal_name': [p('journal.title')],
    'journal_name': ['elife'],
    'msid': [p('id'), int],
    'title': [p('title')],
    'doi': [p('id'), msid2doi],

    'abstract': [p('abstract.content.0.text', '')],
    # we have exactly one instance of a paper with no authors. ridiculous.
    'author_line': [p('authorLine', 'no-author?')],

    'author_name': [find_author_name],
    'author_email': [find_author, p('emailAddresses.0', None)],

    'impact_statement': [p('impactStatement', None)],
    'type': [p('type'), _or(models.UNKNOWN_TYPE)],
    'volume': [p('volume')],
    'num_authors': [p('authors', []), len],
    'num_references': [p('references', []), len],

    # assumes we're ingesting the most recent article!
    # this means bulk ingestion must be done in order
    # this means we ignore updates to previous versions of an article
    'current_version': [p('version')],
    'status': [p('status')],

    'num_poa_versions': [calc_num_poa],
    'num_vor_versions': [ado, calc_num_vor],

    'datetime_published': [wrangle_dt_published, todt],
    'datetime_version_published': [p('published'), todt],

    'datetime_poa_published': [ado, calc_poa_published, todt],
    'datetime_vor_published': [ado, calc_vor_published, todt],

    'days_publication_to_current_version': [ado, calc_pub_to_current],

    'has_digest': [has_key('digest')],
}

# calculated from art history response
ART_HISTORY = {
    #'num_revisions': [],
    'datetime_accept_decision': [p('history.received', None), todt],
    'days_submission_to_acceptance': [ao, calc_sub_to_acc],
    'days_submission_to_review': [ao, calc_sub_to_rev],
    'days_submission_to_production': [ao, calc_sub_to_prod],
    'days_submission_to_publication': [ao, calc_sub_to_pub],
    'days_accepted_to_review': [ao, calc_acc_to_rev],
    'days_accepted_to_production': [ao, calc_acc_to_prod],
    'days_accepted_to_publication': [ao, calc_acc_to_pub],
    'days_review_to_production': [ao, calc_rev_to_prod],
    'days_review_to_publication': [ao, calc_rev_to_pub],
    'days_production_to_publication': [ao, calc_prod_to_pub],
}

# calculated from art metrics
ART_POPULARITY = {
    'num_views': [],
    'num_downloads': [],
    'num_citations': [],
}

def flatten_article_json(article_data, article_history_data=None):
    "takes article-json and squishes it into something obs can digest"
    if not article_history_data:
        article_history_data = {}
    data = article_data
    data['history'] = article_history_data
    struct = render.render_item(DESC, data)
    return struct


@transaction.atomic
def upsert_article_json(article_data, article_history_data):
    "despite the name, it accepts the article-json as python data, not a json string"
    mush = flatten_article_json(article_data, article_history_data)

    # TODO: why is this check being done again ... ?
    ensure(mush['current_version'] == article_data['version'],
           "after scraping the article data, the given article version has changed")

    orig_art = getartobj(mush['msid'])
    new_ver = mush['current_version']
    if orig_art:
        # article exists, ensure we're not replacing newer with older content
        orig_ver = orig_art.current_version
        if new_ver < orig_ver:
            raise StateError("refusing to replace new article data (v%s) with old article data (v%s)" %
                             (orig_ver, new_ver))
    else:
        # article does not exist, ensure we're inserting v1 content
        if new_ver != 1:
            raise StateError("refusing to create article with non v1 article data (v%s). articles must be created in order!" % new_ver)

    return create_or_update(models.Article, mush, ['msid'])

#
# upsert from file/dir of article-json
#

def pathdata(path):
    """parses additional article values from the given path.
    assumes a file name similar to: elife-13964-v1"""
    fname = os.path.basename(path)
    _, msid, rest = fname.split('-')
    ver, rest = rest.split('.', 1)
    return msid, int(ver.strip('v'))

def file_upsert(path):
    article_json = json.load(open(path, 'r'))
    history_data = {}
    LOG.info("ingesting article %s-v%s", article_json['id'], article_json['version'])
    return upsert_article_json(article_json, history_data)

@transaction.atomic
def bulk_file_upsert(article_json_dir):
    #paths = utils.lmap(lambda fname: join(article_json_dir, fname), os.listdir(article_json_dir))
    paths = utils.listfiles(article_json_dir, ['.json'])

    def safe_handler(path):
        try:
            return file_upsert(path)
        except StateError:
            raise
        except Exception as err:
            LOG.error("failed to handle %r: %s", path, err)
            if settings.DEBUG:
                # failfast in debug mode
                raise
    return lmap(safe_handler, sorted(paths))
