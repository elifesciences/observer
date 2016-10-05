import os
from os.path import join
from django.db import transaction
import json
from et3 import render
from et3.extract import path as p
from . import utils, models
from .utils import subdict, gmap
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
    msid = ad['article']['id']
    return getartobj(msid)

def ado(ad):
    "returns the Article Data and stored article Object as a pair"
    return ad['article'], ao(ad)

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
calc_pub_to_next = 0


#
#
#

DESC = {
    'journal_name': [p('journal.title')],
    'msid': [p('article.id'), int],
    'title': [p('article.title')],
    'doi': [p('article.id'), msid2doi],
    'impact_statement': [p('article.impactStatement', None)],
    'type': [p('article.type'), _or(models.UNKNOWN_TYPE)],
    'volume': [p('article.volume')],
    'num_authors': [p('article.authors', []), len],
    'num_references': [p('article.references', []), len],

    # assumes we're ingesting the most recent article!
    # this means bulk ingestion must be done in order
    # this means we ignore updates to previous versions of an article
    'current_version': [p('article.version')],
    'status': [p('article.status')],
    
    #'datetime_accept_decision': [p('history.received', None), todt],

    'num_poa_versions': [p('article'), calc_num_poa],
    'num_vor_versions': [ado, calc_num_vor],
    
    'datetime_published': [p('article'), wrangle_dt_published, todt],
    'datetime_version_published': [p('article.published'), todt],

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
    'days_publication_to_next_version': [ao, calc_pub_to_next]
}

def flatten_article_json(article_data, article_history_data=None):
    "takes article-json and squishes it into something obs can digest"
    if not article_history_data:
        article_history_data = {}        
    data = article_data
    data['history'] = article_history_data
    struct = render.render_item(DESC, data)    
    return struct

def create_or_update(Model, orig_data, key_list, create=True, update=True, commit=True, **overrides):
    inst = None
    created = updated = False
    data = {}
    data.update(orig_data)
    data.update(overrides)
    try:
        # try and find an entry of Model using the key fields in the given data
        inst = Model.objects.get(**subdict(data, key_list))
        # object exists, otherwise DoesNotExist would have been raised
        if update:
            [setattr(inst, key, val) for key, val in data.items() if val != EXCLUDE_ME]
            updated = True
    except Model.DoesNotExist:
        if create:
            #inst = Model(**data)
            # shift this exclude me handling to et3
            inst = Model(**{k:v for k,v in data.items() if v != EXCLUDE_ME})
            created = True

    if (updated or created) and commit:
        inst.save()
    
    # it is possible to neither create nor update.
    # in this case if the model cannot be found then None is returned: (None, False, False)
    return (inst, created, updated)

@transaction.atomic
def upsert_article_json(article_data, article_history_data):
    "despite the name, it accepts the article-json as python data, not a json string"
    mush = flatten_article_json(article_data, article_history_data)

    assert mush['current_version'] == article_data['article']['version']

    orig_art = getartobj(mush['msid'])
    new_ver = mush['current_version']
    if orig_art:
        # article exists, ensure we're not replacing newer with older content
        orig_ver = orig_art.current_version
        if new_ver < orig_ver:
            raise StateError("refusing to replace new article data (v%s) with old article data (v%s)" % \
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
    def extra(p):
        _, ver = pathdata(p)
        return {
            'article': {
                'version': ver
            }
        }
    article_json = json.load(open(path, 'r'))

    # TODO: remove - the fixtures we're using are only partial
    if not article_json['article'].get('version'):
        article_json = utils.deepmerge(article_json, extra(path))
    
    history_data = {}
    LOG.info("ingesting article %s-v%s", article_json['article']['id'], article_json['article']['version'])
    return upsert_article_json(article_json, history_data)

@transaction.atomic
def bulk_upsert(article_json_dir):
    paths = utils.gmap(lambda fname: join(article_json_dir, fname), os.listdir(article_json_dir))
    def safe_handler(path):
        try:
            return file_upsert(path)
        except StateError:
            raise
        except Exception as err:
            LOG.error("failed to handle %r: %s", path, err)
    return gmap(safe_handler, sorted(paths))
