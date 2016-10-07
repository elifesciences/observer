from django.db import models
from django.db.models import PositiveSmallIntegerField, PositiveIntegerField, CharField, DateTimeField, TextField, NullBooleanField

POA, VOR = 'poa', 'vor'
UNKNOWN_TYPE = 'unknown-type'

def type_choices():
    # pull these from the json-spec somehow?
    lst = [
        "correction",
        "editorial",
        "feature",
        "insight",
        "research-advance",
        "research-article",
        "research-exchange",
        "retraction",
        "registered-report",
        "replication-study",
        "short-report",
        "tools-resources",
        
        UNKNOWN_TYPE
    ]
    return zip(map(lambda s: s.replace('-', ' ').title(), lst), lst)

def status_choices():
    return [
        (POA, 'POA'), (VOR, 'VOR')
    ]

def period_choices():
    lst = ['year', 'month', 'day']
    return dict(zip(lst, lst))

def metric_choices():
    lst = [
        'total-published'
        'total-poa-published',
        'total-vor-published',
    ]
    return dict(zip(map(lambda s: s.replace('-', ' ').title(), lst), lst))

'''
class JournalMetric(models.Model):
    journal = models.ForeignKey(Journal)
    period_type = CharField(max_length=5, choices=period_choices())
    period = CharField(max_length=10)
    metrics = CharField(max_length=10, choices=metric_choices())
'''

class Article(models.Model):
    journal_name = models.CharField(max_length=255)
    msid = PositiveIntegerField(unique=True, help_text="article identifier from beginning of submission process right through to end of publication.")
    title = CharField(max_length=255, null=True)
    doi = CharField(max_length=255)
    
    impact_statement = TextField(null=True)
    type = CharField(max_length=50, choices=type_choices(), help_text="article as exported from EJP submission system")    
    current_version = PositiveSmallIntegerField(null=True)
    status = CharField(max_length=3, choices=status_choices(), null=True)
    volume = PositiveSmallIntegerField(null=True)
    
    num_authors = PositiveSmallIntegerField(null=True)
    num_references = PositiveSmallIntegerField(null=True)

    # with some cleverness these can be calculated
    num_poa_versions = PositiveSmallIntegerField(default=0)
    num_vor_versions = PositiveSmallIntegerField(default=0)

    # these can all be pulled from the article-history endpoint
    datetime_submitted = DateTimeField(null=True, help_text="when the author uploaded their article")
    
    datetime_initial_qc_complete = DateTimeField(null=True, help_text="when author hands off submission for review")
    datetime_initial_decision = DateTimeField(null=True, help_text="when decision to accept/reject/revise was made")
    initial_decision = models.CharField(max_length=25, null=True, choices=decision_codes())

    datetime_full_qc = models.DateField(null=True)
    datetime_full_decision = models.DateField(null=True)
    decision = models.CharField(max_length=25, null=True, choices=decision_codes()) 

    datetime_accept_decision = DateTimeField(null=True, help_text="this is a accept OR reject decision")
    accepted_in_revision = PositiveSmallIntegerField(null=True, help_text="in which revision was the manuscript accepted?")

    # these two probably conflict with the initial_qc and full_qc above
    datetime_entered_review = DateTimeField(null=True)
    datetime_entered_production = DateTimeField(null=True)


    datetime_published = DateTimeField(null=True)
    datetime_version_published = DateTimeField(help_text="date and time current version of article published")

    datetime_poa_published = DateTimeField(null=True, help_text="date and time first POA version published")
    datetime_vor_published = DateTimeField(null=True, help_text="date and time first VOR version published")

    # create a view for these fields?
    days_submission_to_acceptance = PositiveSmallIntegerField(null=True)
    days_submission_to_review = PositiveSmallIntegerField(null=True)
    days_submission_to_production = PositiveSmallIntegerField(null=True)
    days_submission_to_publication = PositiveSmallIntegerField(null=True)
    days_accepted_to_review = PositiveSmallIntegerField(null=True)
    days_accepted_to_production = PositiveSmallIntegerField(null=True)
    days_accepted_to_publication = PositiveSmallIntegerField(null=True)
    days_review_to_production = PositiveSmallIntegerField(null=True)
    days_review_to_publication = PositiveSmallIntegerField(null=True)
    days_production_to_publication = PositiveSmallIntegerField(null=True)
    days_publication_to_next_version = PositiveSmallIntegerField(null=True)

    num_views = PositiveIntegerField(default=0)
    num_downloads = PositiveIntegerField(default=0)
    num_citations = PositiveIntegerField(default=0)

    #pdf_url
    #xml_url
    #json_url

    has_digest = NullBooleanField(null=True, help_text="Null/None means I don't know!")
    
    class Meta:
        db_table = 'articles'
