import json
from os.path import join
from .base import BaseCase
from observer import ingest_logic as logic, models, utils

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
