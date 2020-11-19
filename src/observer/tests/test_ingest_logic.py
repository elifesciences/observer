import json
from os.path import join
from . import base
from observer import ingest_logic, models, utils
from unittest.mock import patch
from observer.ingest_logic import p, pp
from datetime import datetime
import pytz

class IngestLogic(base.BaseCase):
    def setUp(self):
        self.unique_article_count = 5
        self.article_fixture_count = 12
        self.article_json = join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json')

    def test_flatten(self):
        "a basic transformation of the data is possible without errors"
        article_json = json.load(open(self.article_json, 'r'))
        article_json['version'] = 1 # patch fixture with missing
        ingest_logic.flatten_article_json(article_json)

    def test_upsert(self):
        "a basic upsert is possible"
        self.assertEqual(models.Article.objects.count(), 0)
        ingest_logic.file_upsert(self.article_json)
        self.assertEqual(models.Article.objects.count(), 1)

    def test_bulk_file_upsert(self):
        "we can create/update a sample of our articles across multiple versions"
        self.assertEqual(models.Article.objects.count(), 0)
        ingest_logic.bulk_file_upsert(join(self.fixture_dir, 'ajson'))
        self.assertEqual(models.Article.objects.count(), self.unique_article_count)

    def test_upsert_json(self):
        self.assertEqual(models.RawJSON.objects.count(), 0)
        ingest_logic.file_upsert(self.article_json)
        self.assertEqual(models.RawJSON.objects.count(), 1)

    def test_bulk_regenerate_ajson(self):
        "an error involving regenerating one article doesn't affect all articles in transaction"
        self.assertEqual(models.Article.objects.count(), 0)
        ingest_logic.bulk_file_upsert(join(self.fixture_dir, 'ajson'), regen=False)

        # no articles, expected json data
        self.assertEqual(0, models.Article.objects.count())
        self.assertEqual(self.article_fixture_count, models.RawJSON.objects.count())

        # skitch a fixture
        notajson = {'pants': 'party'}
        randajson = models.RawJSON.objects.filter(msid='13964', version=2)[0] # 13964 has three versions.
        randajson.json = notajson
        randajson.save()

        # now we regenerate and one less than expected is expected
        ingest_logic.regenerate_all_articles()
        self.assertEqual(self.unique_article_count - 1, models.Article.objects.count())

        # v1 and v3 would have been ingested fine but all should be rolled back when any one fails
        self.assertRaises(models.Article.DoesNotExist, models.Article.objects.get, msid=13964)


class IngestLogicFns(base.BaseCase):
    def test_find_author(self):
        cases = [
            ({'authors': []}, {}), # no authors -> empty dict
            ({'authors': [{'emailAddresses': True}]}, {'emailAddresses': True}), # one 'author' -> same author returned
            ({'authors': [{'emailAddresses': True}, {'emailAddresses': False}]}, {'emailAddresses': True}), # multiple authors -> first author returned
        ]
        for given, expected in cases:
            self.assertEqual(ingest_logic.find_author(given), expected)

    def test_find_author_name(self):
        cases = [
            ({'authors': []}, None), # no authors -> no name found
            # one 'author', no preferred name -> first author first name returned
            ({'authors': [{'emailAddresses': True, 'name': 'pants'}]}, 'pants'),
            # multiple authors -> first author first name returned
            ({'authors': [{'emailAddresses': True, 'name': 'pants'}, {'emailAddresses': False, 'name': 'party'}]}, 'pants'),
            # one 'author' w.preferred name -> first author preferred name returned
            ({'authors': [{'emailAddresses': True, 'name': {'preferred': 'party'}}]}, 'party'),
        ]
        for given, expected in cases:
            self.assertEqual(ingest_logic.find_author_name(given), expected, "failed on: %s" % given)

    def test_pp(self):
        struct = {'foo': {'bar': 'pants.party'}}
        cases = [
            (pp(p('foo.bar'), p('bar.baz')), 'pants.party'),
            (pp(p('bar.baz'), p('foo.bar')), 'pants.party'),

            (pp(p('foo.baz'), p('bar.foo', 0xFABBEEF)), 0xFABBEEF),
        ]
        for given, expected in cases:
            self.assertEqual(given(struct), expected, "failed on: %s" % given)

        case = pp(p('foo.baz'), p('bar.foo'))
        self.assertRaises(KeyError, case, struct)

class Article(base.BaseCase):
    def setUp(self):
        pass

    def test_upsert_json_msid_type(self):
        "integer and string values for msid are supported"
        ajson = {}
        cases = [
            # msid, version, type, data
            (1234, 1, models.LAX_AJSON, ajson), # integer msid
            ('1234', 1, models.LAX_AJSON, ajson), # string msid

            (720609628398071589300, 1, models.LAX_AJSON, ajson),
            ('720609628398071589300', 1, models.LAX_AJSON, ajson),
        ]
        for args in cases:
            ingest_logic.upsert_json(*args)
        self.assertEqual(2, models.RawJSON.objects.count())

    def test_id_normalised(self):
        msid, version, data = '00003', 1, {}
        ingest_logic.upsert_json(msid, version, models.LAX_AJSON, data)
        # JSON was inserted
        self.assertEqual(models.RawJSON.objects.count(), 1)
        # and it's msid was normalised
        expected_id = '3'
        models.RawJSON.objects.get(msid=expected_id)

#
#
#

class Subjects(base.BaseCase):
    def setUp(self):
        pass

    def test_subjects_created(self):
        self.assertEqual(0, models.Subject.objects.count())
        msid = ingest_logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        self.assertEqual(2, models.Subject.objects.count())
        art = models.Article.objects.get(msid=msid)
        self.assertEqual(2, art.subjects.count())

    def test_subjects_data(self):
        # alphabetical order, asc
        expected = [
            ('cancer-biology', 'Cancer Biology'),
            ('cell-biology', 'Cell Biology')
        ]
        msid = ingest_logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        art = models.Article.objects.get(msid=msid)
        subjects = [(s.name, s.label) for s in art.subjects.all()]
        self.assertEqual(subjects, expected)

class Authors(base.BaseCase):
    def setUp(self):
        pass

    def test_authors_created(self):
        self.assertEqual(0, models.Author.objects.count())
        msid = ingest_logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        self.assertEqual(24, models.Author.objects.count())
        art = models.Article.objects.get(msid=msid)
        self.assertEqual(24, art.authors.count())

    def test_authors_data(self):
        msid = ingest_logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        art = models.Article.objects.get(msid=msid)
        authors = art.authors.all()
        expected = [
            ('person', 'Anke Hartung', 'United States'),
            ('person', 'Christina A Kirby', 'United States'),
        ]
        actual = [(p.type, p.name, p.country) for p in authors[:2]]
        self.assertEqual(expected, actual)

        # there are 24, test the last two as well for correct ordering
        expected = [
            ('person', 'Yan Feng', 'United States'), # incredible name
            ('person', 'Zineb Mounir', 'United States'),
        ]
        actual = [(p.type, p.name, p.country) for p in list(authors)[-2:]]
        self.assertEqual(expected, actual)

class Metrics(base.BaseCase):
    def setUp(self):
        pass

    def test_metrics_summary_consume(self):
        "an article's metrics summary can be downloaded and turned into RawJSON"
        expected = self.jsonfix('metrics-summary', '9560.json')
        self.assertEqual(0, models.RawJSON.objects.count())
        with patch('observer.consume.consume', return_value=expected):
            ingest_logic.download_article_metrics(9560)
        self.assertEqual(1, models.RawJSON.objects.count())

    def test_metrics_summary_consume_all(self):
        "all metrics summaries can be downloaded and turned into RawJSON records"
        expected = self.jsonfix('metrics-summary', 'many.json')
        with patch('observer.consume.consume', return_value=expected):
            ingest_logic.download_all_article_metrics()
        self.assertEqual(100, models.RawJSON.objects.count())

        # ensure data is correct
        expected = {"id": 90560, "views": 11, "downloads": 0, "crossref": 0, "pubmed": 0, "scopus": 0}
        self.assertEqual(models.RawJSON.objects.get(msid=90560).json, expected)

class PressPackages(base.BaseCase):
    def test_download_single_presspackage(self):
        ppid = "81d42f7d"
        expected = self.jsonfix('presspackages', ppid + '.json')
        with patch('observer.consume.consume', return_value=expected):
            ppobj = ingest_logic.download_item(models.PRESSPACKAGE, ppid)
            self.assertEqual(models.RawJSON.objects.count(), 1)

        expected_attrs = {
            'version': None,
            'msid': ppid,
            'json_type': 'press-packages-id',
            'json': expected
        }
        for attr, expected in expected_attrs.items():
            self.assertEqual(getattr(ppobj, attr), expected)

    def test_download_many_presspackages(self):
        expected = self.jsonfix('presspackages', 'many.json')
        expected['total'] = 100
        with patch('observer.consume.consume', return_value=expected):
            ingest_logic.download_all(models.PRESSPACKAGE)
        self.assertEqual(models.RawJSON.objects.count(), 100)

        ingest_logic.regenerate(models.PRESSPACKAGE)
        self.assertEqual(models.PressPackage.objects.count(), 100)


class ProfileCount(base.BaseCase):
    def setUp(self):
        pass

    def test_download_single_profile(self):
        pfid = 'ssiyns7x'
        expected = self.jsonfix('profiles', pfid + '.json')
        with patch('observer.consume.consume', return_value=expected):
            ingest_logic.download_item(models.PROFILE, pfid)
        self.assertEqual(models.RawJSON.objects.count(), 1)

        ingest_logic.regenerate(models.PROFILE)
        self.assertEqual(models.Profile.objects.count(), 1)

    def test_download_many_profiles(self):
        expected = self.jsonfix('profiles', 'many.json')
        expected['total'] = 100
        with patch('observer.consume.consume', return_value=expected):
            ingest_logic.download_all(models.PROFILE)
        self.assertEqual(models.RawJSON.objects.count(), 100)

        ingest_logic.regenerate(models.PROFILE)
        self.assertEqual(models.Profile.objects.count(), 100)

class AggregateIngestLogic(base.BaseCase):
    def setUp(self):
        # 13964 v1,v2,v3
        # 14850 v1
        # 15378 v1,v2,v3
        # 18675 v1,v2,v3,v4
        ingest_logic.bulk_file_upsert(join(self.fixture_dir, 'ajson'))

    def test_calc_pub_to_current(self):
        cases = [
            # (msid, expected days)
            # (13964, # is actually fubar
            (15378, 35), # days
            (18675, 24), # days
        ]
        for msid, expected_num_days in cases:
            art = models.Article.objects.get(msid=msid)
            self.assertEqual(expected_num_days, art.days_publication_to_current_version)

    def test_num_authors(self):
        expected_authors = {
            '13964': 24,
            '14850': 4,
            '15378': 5,
            '18675': 9
        }
        for msid, author_count in expected_authors.items():
            art = models.Article.objects.get(msid=msid)
            self.assertEqual(art.num_authors, author_count)

    def test_num_versions(self):
        "ensure our version calculations are correct"
        expected_versions = {
            # expected ver, expected poa, expected vor
            13964: (3, 2, 1),
            14850: (1, 0, 1),
            15378: (3, 1, 2),
            18675: (4, 3, 1),
        }
        for msid, vers in expected_versions.items():
            try:
                expected_version, expected_poa, expected_vor = vers
                art = models.Article.objects.get(msid=msid)
                self.assertEqual(art.current_version, expected_version)
                self.assertEqual(art.num_poa_versions, expected_poa)
                self.assertEqual(art.num_vor_versions, expected_vor)
                self.assertEqual(art.status, models.VOR)
            except AssertionError as err:
                print('failed on', msid, 'with vers', vers)
                raise err

    def test_datetime_version_published(self):
        "this field is the date of the most recent version of this article"
        cases = [
            (13964, datetime(year=2016, month=6, day=15, tzinfo=pytz.utc)),
            (14850, datetime(year=2016, month=7, day=21, tzinfo=pytz.utc)),
            (15378, datetime(year=2016, month=9, day=2, hour=14, minute=51, second=0, tzinfo=pytz.utc)),
            (18675, datetime(year=2016, month=9, day=16, hour=10, minute=13, second=54, tzinfo=pytz.utc)),
            (20125, datetime(year=2016, month=9, day=8, tzinfo=pytz.utc)),
        ]
        for msid, expected_version_date in cases:
            art = models.Article.objects.get(msid=msid)
            self.assertEqual(expected_version_date, art.datetime_version_published)

    def test_calc_poa_published(self):
        poa_pubdates = {
            '13964': '2016-05-16T00:00:00Z',
            '14850': None, # no poa
            '15378': '2016-07-29T00:00:00Z',
            '18675': '2016-08-23T00:00:00Z'
        }
        for msid, expected_dt in poa_pubdates.items():
            obj = models.Article.objects.get(msid=msid)
            self.assertEqual(obj.datetime_poa_published, utils.todt(expected_dt))

    def test_calc_vor_published(self):
        vor_pubdates = {
            '13964': '2016-06-15T00:00:00Z',
            '14850': '2016-07-21T00:00:00Z',
            '15378': '2016-08-22T16:00:29Z',
            '18675': '2016-09-16T10:13:54Z'
        }
        for msid, expected_dt in vor_pubdates.items():
            obj = models.Article.objects.get(msid=msid)
            self.assertEqual(obj.datetime_vor_published, utils.todt(expected_dt), "failed to calculate vor for %s" % msid)

    def test_subjects_scraped(self):
        "subject slugs are scraped and are in alphabetical order"
        subjects = {
            '13964': ['cancer-biology', 'cell-biology'],
            '14850': ['cell-biology', 'immunology'],
            '15378': ['neuroscience', None, None], # subjects 2 and 3 should be empty
            '18675': ['biochemistry', 'biophysics-structural-biology']
        }
        for msid, expected_subjects in subjects.items():
            obj = models.Article.objects.get(msid=msid)
            for i, subj in enumerate(expected_subjects):
                actual_subj = getattr(obj, 'subject%s' % (i + 1))
                self.assertEqual(subj, actual_subj)

#
# digests
#

def test_flatten_digest():
    "digest json data is extracted into something Observer can store"
    fixture = json.load(open(join(base.FIXTURE_DIR, 'digests', '59885.json'), 'r'))
    expected = {'id': 59885,
                'content_type': models.DIGEST,
                'title': 'Splitting up',
                'description': 'Changes in protein levels during cell division reveal how the process is carefully controlled.',
                'image_uri': 'https://iiif.elifesciences.org/digests/59885%2Fdigest-59885.png',
                'image_width': 805,
                'image_height': 653,
                'image_mime': 'image/jpeg',
                'datetime_published': '2020-10-01T13:28:04Z',
                'datetime_updated': '2020-10-01T13:28:31Z',
                'categories': [{'label': 'Cell Biology', 'name': 'cell-biology'}]}
    actual = ingest_logic.flatten_data(models.DIGEST, fixture)
    assert expected == actual

class Content(base.BaseCase):
    def setUp(self):
        pass

    def test_download_content(self):
        "raw /collection data can be downloaded and is stored as individual items"
        fixture = self.jsonfix('community', 'many.json')
        with patch('observer.consume.consume', return_value=fixture):
            ingest_logic.download_all(models.COMMUNITY)
        expected = 11
        assert expected == models.RawJSON.objects.filter(json_type=models.COMMUNITY).count()

    def test_download_ingest_collection(self):
        "collections results are parsed out into their individual models"
        fixture = self.jsonfix('community', 'many.json')
        with patch('observer.consume.consume', return_value=fixture):
            ingest_logic.download_all(models.COMMUNITY)
        ingest_logic.regenerate(models.COMMUNITY)
        expected_blog_articles = 2
        expected_interviews = 3
        expected_features = 4
        expected_collections = 1
        expected_editorials = 1

        expected = expected_blog_articles + expected_interviews + expected_features + expected_collections + expected_editorials

        assert expected == models.Content.objects.count()

        assert expected_blog_articles == models.Content.objects.filter(content_type=models.BLOG_ARTICLE).count()
        assert expected_interviews == models.Content.objects.filter(content_type=models.INTERVIEW).count()
        assert expected_features == models.Content.objects.filter(content_type=models.FEATURE).count()
        assert expected_collections == models.Content.objects.filter(content_type=models.COLLECTION).count()
        assert expected_editorials == models.Content.objects.filter(content_type=models.EDITORIAL).count()


class Podcasts(base.BaseCase):
    def setUp(self):
        pass

    def test_download_results(self):
        "raw /podcast-episodes data can be downloaded and is stored as individual items"
        fixture = self.jsonfix('podcasts', 'many.json')
        with patch('observer.consume.consume', return_value=fixture):
            ingest_logic.download_all(models.PODCAST)
        expected = 10
        assert expected == models.RawJSON.objects.filter(json_type=models.PODCAST).count()
        expected = 70
        assert 1 == models.RawJSON.objects.filter(json_type=models.PODCAST, msid=expected).count()

    def test_download_ingest_results(self):
        "podcast-episodes results are parsed out into their individual models"
        fixture = self.jsonfix('podcasts', 'many.json')
        with patch('observer.consume.consume', return_value=fixture):
            ingest_logic.download_all(models.PODCAST)
        ingest_logic.regenerate(models.PODCAST)
        expected = 10
        assert expected == models.Content.objects.count()

class Insights(base.BaseCase):
    def setUp(self):
        pass

    def test_ingest_insight(self):
        """downloading and ingesting an Insight type article creates a Content item.
        slight overlap with the general article ingest/regenerate tests."""
        test_fixture = join(self.fixture_dir, 'insights', 'elife-63871-v1.xml.json')
        self.assertEqual(models.Article.objects.count(), 0)
        self.assertEqual(models.Content.objects.count(), 0)
        ingest_logic.file_upsert(test_fixture)
        self.assertEqual(models.Article.objects.count(), 1)
        self.assertEqual(models.Content.objects.count(), 1)

    def test_ingest_insight_update(self):
        """insight content is deleted and regenerated along with it's article (no duplicates)."""
        test_fixture = join(self.fixture_dir, 'insights', 'elife-63871-v1.xml.json')
        ingest_logic.file_upsert(test_fixture)
        self.assertEqual(models.Article.objects.count(), 1)
        self.assertEqual(models.Content.objects.count(), 1)
        ingest_logic.file_upsert(test_fixture)
        self.assertEqual(models.Article.objects.count(), 1)
        self.assertEqual(models.Content.objects.count(), 1)

    def test_ingest_insight_no_impact_statement(self):
        "older insight articles don't have an impactStatement field so we fall back to using the first line of the abstract."
        test_fixture = join(self.fixture_dir, 'insights', 'elife-23447-v1.xml.json')
        ingest_logic.file_upsert(test_fixture)
        self.assertEqual(models.Article.objects.count(), 1)
        self.assertEqual(models.Content.objects.count(), 1)
        expected = "Experiments on a single-celled ciliate reveal how mobile genetic elements can shape a genome, even one which is not transcriptionally active."
        self.assertEqual(expected, models.Content.objects.get(id="23447").description)
