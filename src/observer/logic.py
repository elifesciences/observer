# from observer import ingest_logic # DONT DO THIS - circular dependencies.
from observer import models

def known_articles():
    "returns a query set of manuscript_ids from newest to oldest"
    return models.ArticleJSON.objects \
        .values_list('msid', flat=True) \
        .order_by('-msid') \
        .distinct()

def verified_subjects(string_list):
    "given a list of subject slugs, returns only those present in the database"
    return models.Subject.objects \
        .filter(name__in=string_list) \
        .values_list('name', flat=True) # ['foo', 'bar', 'baz']
