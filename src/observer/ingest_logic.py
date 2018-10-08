import os, math, json
from functools import partial
from django.db import transaction
from et3 import render
from et3.extract import path as p
from . import utils, models, logic, consume
from .utils import lmap, lfilter, create_or_update, delall, first, second, third, last, ensure, do_all_atomically
import logging
import requests

LOG = logging.getLogger(__name__)

POA, VOR = 'poa', 'vor'
EXCLUDE_ME = 0xDEADC0DE

class StateError(Exception):
    pass

def msid2doi(msid):
    assert utils.isint(msid), "given msid must be an integer: %r" % msid
    msid = int(msid)
    assert msid > 0, "given msid must be a positive integer: %r" % msid
    return '10.7554/eLife.%05d' % int(msid)

def todt(v):
    if v == EXCLUDE_ME:
        return v
    return utils.todt(v)

def key(k):
    def wrap(v):
        if isinstance(v, dict):
            return v.get(k)
        return v
    return wrap

# shift to et3?
def _or(v):
    def fn(x):
        return x if x else v
    return fn

#calc_sub_to_acc = 0
#calc_sub_to_rev = 0
#calc_sub_to_prod = 0
#calc_sub_to_pub = 0
#calc_acc_to_rev = 0
#calc_acc_to_prod = 0
#calc_acc_to_pub = 0
#calc_rev_to_prod = 0
#calc_rev_to_pub = 0
#calc_prod_to_pub = 0

def calc_pub_to_current(art):
    "the number of days between first publication and current publication"
    kv = art.get('known-versions', [])
    if not kv or len(kv) == 1:
        return None # cannot be calculated
    v1dt = todt(first(kv)['published'])
    vNdt = todt(last(kv)['versionDate'])
    return (vNdt - v1dt).days

#
#
#

def has_key(k):
    def fn(v):
        return k in v
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

# todo: add to et3?
def foreach_render(desc):
    "renders description for each item in iterable"
    def wrap(data):
        return [render.render_item(desc, row) for row in data]
    return wrap

def fltr(fn):
    def wrap(lst):
        return lfilter(fn, lst)
    return wrap

def known_versions(status=None):
    def wrap(art):
        res = art.get('known-versions', [])
        if status:
            res = lfilter(lambda av: av['status'] == status, res)
        return res
    return wrap

# todo: add to et3?
def pp(*pobjs):
    "returns the value at the first path that doesn't cause an error or raises the last error if all are in error"
    def wrapper(data):
        for i, pobj in enumerate(pobjs):
            try:
                return pobj(data)
            except BaseException:
                if (i + 1) == len(pobjs): # if this is the last p-obj ..
                    raise # die.
                continue
    return wrapper

#
#
#

AUTHOR_DESC = {
    'type': [p('type')],
    'name': [pp(p('name.preferred'), p('name', None))],
    'country': [p('affiliations.0.address.components.country', None)]
}

DESC = {
    # 'journal_name': [p('journal.title')],
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
    'type': [p('type'), _or(models.UNKNOWN_TYPE)], # TODO: good reason we're not using `p('type', models.UNKNOWN_TYPE)` ?
    'volume': [p('volume')],
    'num_authors': [p('authors', []), len],
    'num_references': [p('references', []), len],

    # assumes we're ingesting the most recent article!
    # this means bulk ingestion must be done in order
    # this means we ignore updates to previous versions of an article
    'current_version': [p('version')],
    'status': [p('status')],

    # how many POA/VOR versions of this article have we published?
    'num_poa_versions': [known_versions(POA), len],
    'num_vor_versions': [known_versions(VOR), len],

    # 'published' doesn't change, ever. it's the v1 pubdate
    'datetime_published': [p('published'), todt],
    # 'versionDate' changes on every single version
    'datetime_version_published': [p('versionDate'), todt],
    # poa pubdate is the date the state changed to POA, if any POA present
    'datetime_poa_published': [known_versions(POA), first, _or({}), p('statusDate', EXCLUDE_ME), todt],
    # vor pubdate is the date the state changed to VOR, if any VOR present
    'datetime_vor_published': [known_versions(VOR), first, _or({}), p('statusDate', EXCLUDE_ME), todt],

    'days_publication_to_current_version': [calc_pub_to_current],

    'has_digest': [has_key('digest')],

    #

    'subjects': [p('subjects', []), lambda sl: [{'name': v['id'], 'label': v['name']} for v in sl]],

    # not too helpful and may be confusing.
    'subject1': [p('subjects', []), first, key('id')],
    'subject2': [p('subjects', []), second, key('id')],
    'subject3': [p('subjects', []), third, key('id')],

    'authors': [p('authors', []), foreach_render(AUTHOR_DESC), fltr(lambda a: a['country'])]
}

# calculated from art history response
# ART_HISTORY = {
#    #'num_revisions': [],
#    'datetime_accept_decision': [p('history.received', None), todt],
#    'days_submission_to_acceptance': [ao, calc_sub_to_acc],
#    'days_submission_to_review': [ao, calc_sub_to_rev],
#    'days_submission_to_production': [ao, calc_sub_to_prod],
#    'days_submission_to_publication': [ao, calc_sub_to_pub],
#    'days_accepted_to_review': [ao, calc_acc_to_rev],
#    'days_accepted_to_production': [ao, calc_acc_to_prod],
#    'days_accepted_to_publication': [ao, calc_acc_to_pub],
#    'days_review_to_production': [ao, calc_rev_to_prod],
#    'days_review_to_publication': [ao, calc_rev_to_pub],
#    'days_production_to_publication': [ao, calc_prod_to_pub],
# }

# calculated from art metrics
ART_POPULARITY = {
    'num_views': [p('metrics.views', 0)],
    'num_downloads': [p('metrics.downloads', 0)],
    'num_citations': [(p('metrics.crossref', 0), p('metrics.pubmed', 0), p('metrics.scopus', 0)), max], # source with highest number of citations
    'num_citations_crossref': [p('metrics.crossref', 0)],
    'num_citations_pubmed': [p('metrics.pubmed', 0)],
    'num_citations_scopus': [p('metrics.scopus', 0)]
}
DESC.update(ART_POPULARITY)

def flatten_article_json(data, known_version_list=[], history=None, metrics=None):
    "takes article-json and squishes it into something obs can digest"
    data['known-versions'] = known_version_list # raw article json the scrape can use to inspect historical values
    data['history'] = history or {} # EJP
    data['metrics'] = metrics or {} # elife-metrics
    return render.render_item(DESC, data)

#
#
#

def upsert_ajson(msid, version, data_type, article_data):
    "insert/update ArticleJSON from a dictionary of article data"
    article_data = {
        'msid': utils.norm_msid(msid),
        'version': version,
        'ajson': article_data,
        'ajson_type': data_type
    }
    version and ensure(version > 0, "'version' in ArticleJSON must be as a positive integer")
    return create_or_update(models.ArticleJSON, article_data, ['msid', 'version'])

#
#
#

def extract_children(mush):
    known_children = {
        'subjects': {'Model': models.Subject, 'key_list': ["name"]},
        'authors': {'Model': models.Author},
    }

    children = []
    for childtype, kwargs in known_children.items():
        data = mush[childtype]

        children.extend([utils.dict_update(kwargs, {'orig_data': row, 'parent-relation': childtype}, immutable=True) for row in data])

    # remove the children from the mush, they must be saved separately
    delall(mush, known_children.keys())
    return mush, children

def extract_article(msid):
    article_data = models.ArticleJSON.objects.filter(msid=str(msid), ajson_type=models.LAX_AJSON).order_by('version') # ASC
    ensure(article_data.count(), "article %s does not exist" % msid)

    try:
        metrics_data = models.ArticleJSON.objects.get(msid=str(msid), ajson_type=models.METRICS_SUMMARY).ajson
    except models.ArticleJSON.DoesNotExist:
        metrics_data = {}

    # ajson for all known versions of this article
    article_version_data = [ajsonobj.ajson for ajsonobj in article_data]

    # the most recent known version of this article
    # scrape has access to historical versions too
    article_data = article_version_data[-1]

    # TODO: other objects need one of these lines. it's currently just 'committing N objects\ncommiting N objects\n...'
    LOG.info('extracting %s' % article_data.get('id', '???'))
    article_mush = flatten_article_json(article_data, known_version_list=article_version_data, metrics=metrics_data)

    # extract sub-objects from the article data
    article_mush, children = extract_children(article_mush)

    parent = {'Model': models.Article, 'orig_data': article_mush, 'key_list': ['msid']}
    return [(parent, children)]

def _regenerate_article(msid):
    object_list = extract_article(msid)
    with transaction.atomic():
        # destroy what we have, if anything. updating may be dangerous
        models.Article.objects.filter(msid=msid).delete()
        utils.save_objects(object_list)
        return models.Article.objects.get(msid=msid)

def regenerate_article(msid):
    "use this when regenerating individual or small numbers of articles."
    return _regenerate_article(msid)

def regenerate_many_articles(msid_list, batches_of=25):
    "commits articles in batches of 25 by default"
    def safe_regen(msid):
        try:
            # this is a nested transaction!
            # this is important for articles because they must be ingested in order
            # and rolled back as a logical group.
            # if one version of an article fails, they all do, but the parent transaction is not
            return regenerate_article(msid)
        except (AssertionError, KeyError):
            LOG.error("bad data encountered, skipping regeneration of %s" % msid)
    do_all_atomically(safe_regen, msid_list, batches_of)

def regenerate_all_articles():
    regenerate_many_articles(logic.known_articles())

#
# upsert article-json from api
#

def mkidx():
    "downloads *all* article snippets to create an msid:version index"
    ini = consume.consume("articles", {'per-page': 1})
    per_page = 100.0
    num_pages = math.ceil(ini["total"] / per_page)
    msid_ver_idx = {} # ll: {09560: 1, ...}
    LOG.info("%s pages to fetch" % num_pages)
    # for page in range(1, num_pages): # TODO: do we have an off-by-1 here?? shift this pagination into something generic
    for page in range(1, num_pages + 1):
        resp = consume.consume("articles", {'page': page})
        for snippet in resp["items"]:
            msid_ver_idx[snippet["id"]] = snippet["version"]
    return msid_ver_idx

def _download_versions(msid, latest_version):
    LOG.info('%s versions to fetch' % latest_version)
    version_range = range(1, latest_version + 1)

    def fetch(version):
        upsert_ajson(msid, version, models.LAX_AJSON, consume.consume("articles/%s/versions/%s" % (msid, version)))
    lmap(fetch, version_range)

def download_article_versions(msid):
    "loads *all* versions of given article via API"
    resp = consume.consume("articles/%s/versions" % msid)
    _download_versions(msid, len(resp["versions"]))

def download_all_article_versions():
    "loads *all* versions of *all* articles via API"
    msid_ver_idx = mkidx() # urgh. this sucks. lax needs a /summary endpoint too
    LOG.info("%s articles to fetch" % len(msid_ver_idx))
    idx = sorted(msid_ver_idx.items(), key=lambda x: x[0], reverse=True)
    for msid, latest_version in idx:
        _download_versions(msid, latest_version)

#
# metrics data
#

def _upsert_metrics_ajson(data):
    version = None
    # big ints in sqlite3 are 64 bits/8 bytes large
    try:
        # TODO: shift this check elsewhere, db field validation checking perhaps
        ensure(utils.byte_length(data['id']) <= 8, "bad data encountered, cannot store msid: %s", data['id'])
        upsert_ajson(data['id'], version, models.METRICS_SUMMARY, data)
    except AssertionError as err:
        LOG.error(err)

def download_article_metrics(msid):
    "loads *all* metrics for *specific* article via API"
    try:
        data = consume.consume("metrics/article/%s/summary" % msid)
        _upsert_metrics_ajson(data['items'][0]) # guaranteed to have either 1 result or 404
    except requests.exceptions.RequestException as err:
        LOG.error("failed to fetch page of summaries: %s", err)

# def download_article_metrics(msid):
#    consume.single("metrics/article/{id}/summary", id=msid)

def download_all_article_metrics():
    "loads *all* metrics for *all* articles via API"
    # calls `consume` until all results are consumed
    ini = consume.consume("metrics/article/summary", {'per-page': 1})
    per_page = 100.0
    num_pages = math.ceil(ini["total"] / per_page)
    LOG.info("%s pages to fetch" % num_pages)
    results = []
    for page in range(1, num_pages + 1):
        try:
            resp = consume.consume("metrics/article/summary", {'page': page})
            results.extend(resp['items'])
        except requests.exceptions.RequestException as err:
            LOG.error("failed to fetch page of summaries: %s", err)

    with transaction.atomic():
        lmap(_upsert_metrics_ajson, results)
    return results

# def download_all_article_metrics():
#    consume.all("metrics/article/summary")

#
# presspackages
#

PP_DESC = {
    'id': [p('id')],
    'title': [p('title')],
    'published': [p('published'), todt],
    'updated': [p('updated', None), todt] # f0114f21 missing an updated date
}

def _regenerate_presspackage(ppid):
    "creates PressPackage records with no transaction"
    data = models.ArticleJSON.objects.get(msid=ppid).ajson
    mush = render.render_item(PP_DESC, data)
    return first(create_or_update(models.PressPackage, mush, ['id', 'idstr']))

@transaction.atomic
def regenerate_presspackage(ppid):
    return _regenerate_presspackage(ppid)

def regenerate_many_presspackages(ppidlist):
    return do_all_atomically(_regenerate_presspackage, ppidlist)

def regenerate_all_presspackages():
    return regenerate_many_presspackages(logic.known_presspackages())

def download_presspackage(ppid):
    "download a specific press package"
    return first(consume.single("press-packages/{id}", id=ppid))

def download_all_presspackages():
    consume.allitems("press-packages")


#
# profiles
#

def trunc(length):
    def _(v):
        return str(v)[:length]
    return _

PF_DESC = {
    'id': [p('id')],
    # disabled in anticipation of GDPR
    # 'orcid': [p('orcid', None)],
    # 'name': [p('name'), trunc(255)],
}

def _regenerate_profile(pfid):
    data = models.ArticleJSON.objects.get(msid=pfid).ajson
    mush = render.render_item(PF_DESC, data)
    return first(create_or_update(models.Profile, mush, ['id']))

@transaction.atomic
def regenerate_profile(pfid):
    return _regenerate_profile(pfid)

def regenerate_many_profiles(pfidlist):
    return do_all_atomically(_regenerate_profile, pfidlist)

def regenerate_all_profiles():
    return regenerate_many_profiles(logic.known_profiles())

def download_profile(pfid):
    return consume.single("profiles/{id}", id=pfid)

def download_all_profiles():
    return consume.allitems("profiles")

#
#
#

def regenerate_all():
    regenerate_all_articles()
    regenerate_all_presspackages()
    regenerate_all_profiles()

#
#
#

def download_regenerate_article(msid):
    try:
        download_article_versions(msid)
        regenerate_article(msid)

    except requests.exceptions.RequestException as err:
        log = LOG.warn if err.response.status_code == 404 else LOG.error
        log("failed to fetch article %s: %s", msid, err) # probably an unpublished article.

    except BaseException:
        LOG.exception("unhandled exception attempting to download and regenerate article %s", msid)

def download_regenerate_presspackage(ppid):
    try:
        LOG.info("update event for presspackage %s", ppid)
        download_presspackage(ppid)
        regenerate_presspackage(ppid)

    except requests.exceptions.RequestException as err:
        log = LOG.warn if err.response.status_code == 404 else LOG.error
        log("failed to fetch presspackage %s: %s", ppid, err) # probably an unpublished presspackage ...?

    except BaseException:
        LOG.exception("unhandled exception attempting to download and regenerate presspackage %s", ppid)


#
# upsert article-json from file/dir
# this is used mostly for testing. consider shifting there
# the load_from_fs command isn't really used anymore
#

def file_upsert(path, ctype=models.LAX_AJSON, regen=True, quiet=False):
    "insert/update ArticleJSON from a file"
    try:
        if not os.path.isfile(path):
            raise ValueError("can't handle path %r" % path)
        LOG.info('loading %s', path)
        article_data = json.load(open(path, 'r'))
        if ctype == models.LAX_AJSON:
            ajson = upsert_ajson(article_data['id'], article_data['version'], ctype, article_data)[0]
            if regen:
                regenerate_article(ajson.msid)
        else:
            ajson = consume.upsert(article_data['id'], ctype, article_data)[0]
            if regen:
                regenerate_all()

        return ajson.msid

    except Exception as err:
        LOG.exception("failed to insert article-json %r: %s", path, err)
        if not quiet:
            raise

@transaction.atomic
def bulk_file_upsert(article_json_dir, regen=True):
    "insert/update ArticleJSON from a directory of files"
    paths = sorted(utils.listfiles(article_json_dir, ['.json']))
    msid_list = sorted(set(lmap(partial(file_upsert, regen=False, quiet=True), paths)))
    if regen:
        regenerate_many_articles(msid_list)
