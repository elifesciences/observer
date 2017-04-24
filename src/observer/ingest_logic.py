import os
#from os.path import join
from functools import partial
from django.db import transaction
import json
from et3 import render
from et3.extract import path as p
from . import utils, models
from .utils import lmap, lfilter, create_or_update, delall
from kids.cache import cache
import logging

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

def foreach(desc):
    def wrap(data):
        return [render.render_item(desc, row) for row in data]
    return wrap

AUTHOR_DESC = {
    'type': [p('type')],
    'name': [p('name.preferred', None)],
    'country': [p('affiliations.0.address.components.country', None)]
}

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

    #

    'subjects': [p('subjects'), lambda sl: [{'name': v['id'], 'label': v['name']} for v in sl]],
    'authors': [p('authors'), foreach(AUTHOR_DESC)]
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

#
#
#

def article_presave_checks(given_data, flat_data):
    mush = flat_data

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

def upsert_ajson(article_data):
    "insert/update ArticleJSON from a dictionary of article data"
    article_data = {
        'msid': article_data['id'],
        'version': article_data['version'],
        'ajson': article_data
    }
    return create_or_update(models.ArticleJSON, article_data, ['msid', 'version'])

def extract_children(mush):
    known_children = {
        'subjects': {'Model': models.Subject, 'key_list': ["name"]},
        'authors': {'Model': models.Author},
    }

    created_children = {}
    for key, kwargs in known_children.items():
        data = mush[key]
        if not isinstance(data, list):
            data = [data]

        objects = []
        for row in data:
            kwargs['orig_data'] = row
            objects.append(create_or_update(**kwargs)[0])

        created_children[key] = objects

    delall(mush, known_children.keys())

    return mush, created_children

@transaction.atomic
def regenerate(msid):
    "scrapes the stored article data to (re)generate a models.Article object"

    models.Article.objects.filter(msid=msid).delete() # destroy what we have

    for avobj in models.ArticleJSON.objects.filter(msid=msid).order_by('version'): # ASC
        article_history_data = {} # eh
        article_data = avobj.ajson
        LOG.info('regenerating %s v%s' % (article_data['id'], article_data['version']))
        mush = flatten_article_json(article_data, article_history_data)

        # extract sub-objects from the article data, insert/update them, re-attach as objects
        article_data, children = extract_children(mush)

        article_presave_checks(article_data, mush)
        artobj = create_or_update(models.Article, mush, ['msid'])[0]

    for childtype, childobjs in children.items():
        prop = getattr(artobj, childtype)
        prop.add(*childobjs)

    return artobj # return the final artobj

@transaction.atomic
def regenerate_many(msid_list):
    return lmap(regenerate, msid_list)

#
# upsert from file/dir of article-json
#

def file_upsert(path, regen=True, quiet=False):
    "insert/update ArticleJSON from a file"
    try:
        if not os.path.isfile(path):
            raise ValueError("can't handle path %r" % path)
        LOG.info('loading %s', path)
        article_data = json.load(open(path, 'r'))
        ajson = upsert_ajson(article_data)[0]
        if regen:
            regenerate(ajson.msid)
        return ajson.msid
    except Exception as err:
        LOG.exception("failed to insert article-json %r: %s", path, err)
        if not quiet:
            raise

@transaction.atomic
def bulk_file_upsert(article_json_dir):
    "insert/update ArticleJSON from a directory of files"
    paths = sorted(utils.listfiles(article_json_dir, ['.json']))
    msid_list = sorted(set(lmap(partial(file_upsert, regen=False, quiet=True), paths)))
    return lmap(regenerate, msid_list)
