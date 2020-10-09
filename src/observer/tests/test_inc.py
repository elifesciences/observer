import json
from .base import BaseCase
from unittest.mock import patch
from observer import inc, models, ingest_logic

class One(BaseCase):

    def test_handling_event(self):
        msid = 13964
        fixture = self.jsonfix('ajson', 'elife-13964-v1.xml.json')
        ingest_logic.upsert_ajson(msid, 1, models.LAX_AJSON, fixture)
        self.assertEqual(0, models.Article.objects.count())
        self.assertEqual(1, models.ArticleJSON.objects.count()) # fixture

        # simulate receiving an event
        dummy_event = json.dumps({'type': 'article', 'id': str(msid)})
        with patch('observer.ingest_logic.download_article_versions'): # prevent downloading other versions
            inc.handler(dummy_event)

        # exactly one article exists
        self.assertEqual(1, models.Article.objects.count())
        models.Article.objects.get(msid=msid)

def test_handling_unhandled_event():
    "unhandled events should issue a warning"
    dummy_event = json.dumps({'type': 'pants', 'id': 'party'})
    with patch('observer.inc.LOG') as mock_logger:
        inc.handler(dummy_event)
        assert mock_logger.warn.called

def test_handling_malformed_json():
    "malformed events should issue an error"
    bad_event = 'foo'
    with patch('observer.inc.LOG') as mock_logger:
        inc.handler(bad_event)
        assert mock_logger.error.called

def test_handling_unexpected_error():
    "handlers that cause an exception log an exception"
    dummy_event = json.dumps({'type': 'presspackage', 'id': 'whatevs'})
    with patch('observer.inc.LOG') as mock:
        with patch('observer.ingest_logic.download_regenerate_presspackage', side_effect=RuntimeError('no pants')):
            inc.handler(dummy_event)
            assert mock.exception.called
