# from observer import ingest_logic # DONT DO THIS - circular dependencies.
from observer import models

def known_articles():
    "returns a query set of manuscript_ids from newest to oldest"
    return models.ArticleJSON.objects \
        .values_list('msid', flat=True) \
        .order_by('-msid') \
        .distinct()
