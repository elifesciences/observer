# from observer import ingest_logic # DONT DO THIS - circular dependencies.
from observer import models
from django.db.models import IntegerField
from django.db.models.functions import Cast

def known_content(json_type):
    """returns a queryset of object IDs from newest to oldest."""
    return models.RawJSON.objects \
        .filter(json_type=json_type) \
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

# lsh@2023-01-16: taken from observer--prod.
_KNOWN_SUBJECTS = set([
    "biochemistry", "biochemistry-chemical-biology", "biophysics-structural-biology", "cancer-biology", "cell-biology", "chromosomes-gene-expression", "computational-systems-biology", "developmental-biology", "developmental-biology-stem-cells", "ecology", "epidemiology-global-health", "evolutionary-biology", "genes-chromosomes", "genetics-genomics", "genomics-evolutionary-biology", "human-biology-medicine", "immunology", "immunology-inflammation", "living-science", "medicine", "microbiology-infectious-disease", "neuroscience", "physics-living-systems", "physics-of-living-systems", "plant-biology", "stem-cells-regenerative-medicine", "structural-biology-molecular-biophysics"])
def known_subjects():
    "returns a set of subjects both hardcoded and from the database"
    return _KNOWN_SUBJECTS.union(simple_subjects())

def verified_subjects(string_list):
    "returns the set of strings in `string_list` that are known to us ('verified')"
    return known_subjects().intersection(set(string_list))
