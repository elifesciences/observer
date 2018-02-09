# from observer import ingest_logic # DONT DO THIS - circular dependencies.
from observer import models

def known_blah(blah):
    return models.ArticleJSON.objects \
        .filter(ajson_type=blah) \
        .values_list('msid', flat=True) \
        .order_by('-msid') \
        .distinct()

def known_articles():
    "returns a query set of manuscript_ids from newest to oldest"
    return known_blah(models.LAX_AJSON)

def known_presspackages():
    return known_blah(models.PRESSPACKAGE)

def known_profiles():
    return known_blah(models.PROFILE)

def simple_subjects():
    "returns a flat list of subject names"
    return models.Subject.objects.values_list('name', flat=True) # ['foo', 'bar', 'baz']

def verified_subjects(string_list):
    "given a list of subject slugs, returns only those present in the database"
    return models.Subject.objects \
        .filter(name__in=string_list) \
        .values_list('name', flat=True) # ['foo', 'bar', 'baz']
