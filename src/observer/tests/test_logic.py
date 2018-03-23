from . import base
from observer import logic, ingest_logic, models

class One(base.BaseCase):
    def setUp(self):
        pass

    def test_known_articles(self):
        "a list of article manuscript IDs are returned as integers, highest to lowest"
        for i in range(1, 12):
            ingest_logic.upsert_ajson(i, 1, models.LAX_AJSON, {})
        # without the casting in logic.known_articles, you get ordering like this:
        # ['9', '8', '7', '6', '5', '4', '3', '2', '11', '10', '1']
        expected = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        self.assertEqual(expected, list(logic.known_articles()))
