# from observer import ingest_logic # DONT DO THIS - circular dependencies.
from observer import models
from django.db.models import IntegerField
from django.db.models.functions import Cast

def known_content(content_type):
    """returns a queryset of object IDs from newest to oldest."""
    return models.RawJSON.objects \
        .filter(json_type=content_type) \
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

def simple_subjects():
    "returns a list of subject name strings"
    return models.Subject.objects.values_list('name', flat=True) # ['foo', 'bar', 'baz']

def verified_subjects(string_list):
    "given a list of subject slugs, returns only those present in the database"
    return models.Subject.objects \
        .filter(name__in=string_list) \
        .values_list('name', flat=True) # ['foo', 'bar', 'baz']
