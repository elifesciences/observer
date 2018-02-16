import json
from os.path import join
from .base import BaseCase
from observer import ingest_logic as logic, models, utils
from unittest.mock import patch
from observer.ingest_logic import p, pp

class Logic(BaseCase):
    def setUp(self):
        self.unique_article_count = 5
        self.article_json = join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json')

    def test_flatten(self):
        "a basic transformation of the data is possible without errors"
        article_json = json.load(open(self.article_json, 'r'))
        article_json['version'] = 1 # patch fixture with missing
        logic.flatten_article_json(article_json)

    def test_upsert(self):
        "a basic upsert is possible"
        self.assertEqual(models.Article.objects.count(), 0)
        logic.file_upsert(self.article_json)
        self.assertEqual(models.Article.objects.count(), 1)

    def test_bulk_file_upsert(self):
        "we can create/update a sample of our articles across multiple versions"
        self.assertEqual(models.Article.objects.count(), 0)
        logic.bulk_file_upsert(join(self.fixture_dir, 'ajson'))
        self.assertEqual(models.Article.objects.count(), self.unique_article_count)

    def test_upsert_ajson(self):
        self.assertEqual(models.ArticleJSON.objects.count(), 0)
        logic.file_upsert(self.article_json)
        self.assertEqual(models.ArticleJSON.objects.count(), 1)


class LogicFns(BaseCase):
    def test_find_author(self):
        cases = [
            ({'authors': []}, {}), # no authors -> empty dict
            ({'authors': [{'emailAddresses': True}]}, {'emailAddresses': True}), # one 'author' -> same author returned
            ({'authors': [{'emailAddresses': True}, {'emailAddresses': False}]}, {'emailAddresses': True}), # multiple authors -> first author returned
        ]
        for given, expected in cases:
            self.assertEqual(logic.find_author(given), expected)

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
            self.assertEqual(logic.find_author_name(given), expected, "failed on: %s" % given)

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

class Article(BaseCase):
    def setUp(self):
        pass

    def test_upsert_ajson_msid_type(self):
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
            logic.upsert_ajson(*args)
        self.assertEqual(2, models.ArticleJSON.objects.count())

#
#
#

class Subjects(BaseCase):
    def setUp(self):
        pass

    def test_subjects_created(self):
        self.assertEqual(0, models.Subject.objects.count())
        msid = logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        self.assertEqual(2, models.Subject.objects.count())
        art = models.Article.objects.get(msid=msid)
        self.assertEqual(2, art.subjects.count())

    def test_subjects_data(self):
        # alphabetical order, asc
        expected = [
            ('cancer-biology', 'Cancer Biology'),
            ('cell-biology', 'Cell Biology')
        ]
        msid = logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        art = models.Article.objects.get(msid=msid)
        subjects = [(s.name, s.label) for s in art.subjects.all()]
        self.assertEqual(subjects, expected)

class Authors(BaseCase):
    def setUp(self):
        pass

    def test_authors_created(self):
        self.assertEqual(0, models.Author.objects.count())
        msid = logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        self.assertEqual(24, models.Author.objects.count())
        art = models.Article.objects.get(msid=msid)
        self.assertEqual(24, art.authors.count())

    def test_authors_data(self):
        msid = logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
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

class Metrics(BaseCase):
    def setUp(self):
        pass

    def test_metrics_summary_consume(self):
        "an article's metrics summary can be downloaded and turned into ArticleJSON"
        expected = {"summaries": [{"msid": 9560, "views": 227161, "downloads": 16443, "crossref": 101, "pubmed": 21, "scopus": 52}], "totalArticles": 1}
        self.assertEqual(0, models.ArticleJSON.objects.count())
        with patch('observer.consume.consume', return_value=expected):
            logic.download_article_metrics(9560)
        self.assertEqual(1, models.ArticleJSON.objects.count())

    def test_metrics_summary_consume_all(self):
        "all metrics summaries can be downloaded and turned into ArticleJSON records"
        expected = json.load(open(join(self.fixture_dir, 'metrics-summary', 'many.json'), 'r'))
        with patch('observer.consume.consume', return_value=expected):
            logic.download_all_article_metrics()
        self.assertEqual(100, models.ArticleJSON.objects.count())

        # ensure data is correct
        expected = {"msid": 90560, "views": 11, "downloads": 0, "crossref": 0, "pubmed": 0, "scopus": 0}
        self.assertEqual(models.ArticleJSON.objects.get(msid=90560).ajson, expected)

class PressPackages(BaseCase):
    def test_download_single_presspackage(self):
        ppid = "81d42f7d"
        expected = self.jsonfix('presspackages', ppid + '.json')
        with patch('observer.consume.consume', return_value=expected):
            pp = logic.download_presspackage(ppid)
            self.assertEqual(models.ArticleJSON.objects.count(), 1)

        expected_attrs = {
            'version': None,
            'msid': ppid,
            'ajson_type': 'press-packages-id',
            'ajson': expected
        }
        for attr, expected in expected_attrs.items():
            self.assertEqual(getattr(pp, attr), expected)

    def test_download_many_presspackages(self):
        expected = self.jsonfix('presspackages', 'many.json')
        expected['total'] = 100
        with patch('observer.consume.consume', return_value=expected):
            logic.download_all_presspackages()
        self.assertEqual(models.ArticleJSON.objects.count(), 100)

        logic.regenerate_all_presspackages()
        self.assertEqual(models.PressPackage.objects.count(), 100)


class ProfileCount(BaseCase):
    def setUp(self):
        pass

    def test_download_single_profile(self):
        pfid = 'ssiyns7x'
        expected = self.jsonfix('profiles', pfid + '.json')
        with patch('observer.consume.consume', return_value=expected):
            logic.download_profile(pfid)
        self.assertEqual(models.ArticleJSON.objects.count(), 1)

        logic.regenerate_all_profiles()
        self.assertEqual(models.Profile.objects.count(), 1)

    def test_download_many_profiles(self):
        expected = self.jsonfix('profiles', 'many.json')
        expected['total'] = 100
        with patch('observer.consume.consume', return_value=expected):
            logic.download_all_profiles()
        self.assertEqual(models.ArticleJSON.objects.count(), 100)

        logic.regenerate_all_profiles()
        self.assertEqual(models.Profile.objects.count(), 100)

class AggregateLogic(BaseCase):
    def setUp(self):
        # 13964 v1,v2,v3
        # 14850 v1
        # 15378 v1,v2,v3
        # 18675 v1,v2,v3,v4
        logic.bulk_file_upsert(join(self.fixture_dir, 'ajson'))

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
