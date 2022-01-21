import json
from . import base
from unittest.mock import patch, Mock
from observer import inc, models, ingest_logic, consume
import pytest
import requests

class One(base.BaseCase):

    def test_handling_event(self):
        msid = 13964
        fixture = base.jsonfix('ajson', 'elife-13964-v1.xml.json')
        ingest_logic.upsert_json(msid, 1, models.LAX_AJSON, fixture)
        self.assertEqual(0, models.Article.objects.count())
        self.assertEqual(1, models.RawJSON.objects.count()) # fixture

        # simulate receiving an event
        dummy_event = Mock()
        dummy_event.body = json.dumps({'type': 'article', 'id': str(msid)})
        with patch('observer.ingest_logic.download_article_versions'): # prevent downloading other versions
            inc.handler(dummy_event)

        # exactly one article exists
        self.assertEqual(1, models.Article.objects.count())
        models.Article.objects.get(msid=msid)

def test_handling_unhandled_event():
    "unhandled events should issue a warning"
    dummy_event = Mock()
    dummy_event.body = json.dumps({'type': 'pants', 'id': 'party'})
    with patch('observer.inc.LOG') as mock_logger:
        inc.handler(dummy_event)
        assert mock_logger.warn.called

def test_handling_malformed_json():
    "malformed events should issue an error"
    bad_event = 'foo'
    with patch('observer.inc.LOG') as mock_logger:
        inc.handler(bad_event)
        assert mock_logger.exception.called

        inc._handler(bad_event)
        assert mock_logger.error.called

def test_handling_unexpected_error():
    "handlers that cause an exception log an exception"
    dummy_event = json.dumps({'type': 'presspackage', 'id': 'whatevs'})
    with patch('observer.inc.LOG') as mock:
        with patch('observer.ingest_logic.download_regenerate', side_effect=RuntimeError('no pants')):
            inc.handler(dummy_event)
            assert mock.exception.called

@pytest.mark.django_db
def test_404_deletes_item():
    "receiving a 404 for content that exists causes the item to be deleted"
    item_id = 'ecc32978'
    fixture = base.jsonfix('interviews/ecc32978.json')

    consume.upsert(item_id, models.INTERVIEW, fixture)
    ingest_logic._regenerate_item(models.INTERVIEW, item_id)

    assert models.Content.objects.count() == 1
    assert models.RawJSON.objects.count() == 1

    # simulate receiving an event
    dummy_event = Mock()
    dummy_event.body = json.dumps({'type': models.INTERVIEW, 'id': item_id})

    # simulate a 404 error response
    response = requests.Response()
    response.status_code = 404
    exc = requests.exceptions.RequestException()
    exc.response = response
    with patch('observer.ingest_logic.download_item', side_effect=exc): # prevent downloading other versions
        inc.handler(dummy_event)

    assert models.Content.objects.count() == 0
    assert models.RawJSON.objects.count() == 0
