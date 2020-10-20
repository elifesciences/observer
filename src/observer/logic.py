# from observer import ingest_logic # DONT DO THIS - circular dependencies.
from observer import models
from django.db.models import IntegerField
from django.db.models.functions import Cast

def known_content(blah):
    """returns a queryset of object IDs from newest to oldest."""
    return models.RawJSON.objects \
        .filter(json_type=blah) \
        .values_list('msid', flat=True) \
        .order_by('-msid') \
        .distinct()

def known_articles():
    "returns a query set of manuscript_ids from newest to oldest"
    return models.RawJSON.objects \
        .filter(json_type=models.LAX_AJSON) \
        .annotate(msid_as_int=Cast('msid', IntegerField())) \
        .values_list('msid_as_int', flat=True) \
        .order_by('-msid_as_int') \
        .distinct()

def known_presspackages():
    "returns a queryset of PressPackage IDs from newest to oldest"
    return known_content(models.PRESSPACKAGE)

def known_profiles():
    "returns a queryset of Profile IDs from newest to oldest"
    return known_content(models.PROFILE)

def known_digests():
    "returns a queryset of Digest IDs from newest to oldest"
    return known_content(models.DIGEST)

def simple_subjects():
    "returns a flat list of subject names"
    return models.Subject.objects.values_list('name', flat=True) # ['foo', 'bar', 'baz']

def verified_subjects(string_list):
    "given a list of subject slugs, returns only those present in the database"
    return models.Subject.objects \
        .filter(name__in=string_list) \
        .values_list('name', flat=True) # ['foo', 'bar', 'baz']
