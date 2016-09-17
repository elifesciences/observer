from django.db import models
from django.db.models import PositiveSmallIntegerField, PositiveIntegerField, CharField, DateTimeField, IntegerField

POA, VOR = 'poa', 'vor'

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
        "tools-resources"
    ]
    return dict(zip(map(lambda s: s.replace('-', ' ').title(), lst), lst))

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

class Journal(models.Model):
    name = CharField(max_length=255, help_text="Name of the journal.")

'''
class JournalMetric(models.Model):
    journal = models.ForeignKey(Journal)
    period_type = CharField(max_length=5, choices=period_choices())
    period = CharField(max_length=10)
    metrics = CharField(max_length=10, choices=metric_choices())
'''

class PublishedArticle(models.Model):
    journal = models.ForeignKey(Journal)
    msid = PositiveIntegerField(unique=True, help_text="article identifier from beginning of submission process right through to end of publication.")
    title = CharField(max_length=255)
    doi = CharField(max_length=255)
    current_version = PositiveSmallIntegerField()
    status = CharField(max_length=3, choices=status_choices())
    type = CharField(max_length=50, choices=type_choices(), help_text="article as exported from EJP submission system")
    
    datetime_submitted = DateTimeField()
    datetime_accepted = DateTimeField()
    datetime_entered_review = DateTimeField()
    datetime_entered_production = DateTimeField()
    datetime_published = DateTimeField()
    datetime_version_published = DateTimeField(help_text="date and time this version of the article was published")

    datetime_poa_published = DateTimeField(blank=True, null=True, help_text="date and time first POA version published")
    datetime_vor_published = DateTimeField(blank=True, null=True, help_text="date and time first VOR version published")

    # create a view for these fields?
    #days_submission_to_acceptance
    #days_submission_to_review
    #days_submission_to_production
    #days_submission_to_publication
    #days_accepted_to_review
    #days_accepted_to_production
    #days_accepted_to_publication
    #days_review_to_production
    #days_review_to_publication
    #days_production_to_publication
    #days_publication_to_next_version

    volume = PositiveSmallIntegerField()
    issue = PositiveSmallIntegerField()
    
    num_authors = PositiveSmallIntegerField()
    num_references = PositiveSmallIntegerField()

    num_views = PositiveIntegerField(default=0)
    num_downloads = PositiveIntegerField(default=0)
    num_citations = PositiveIntegerField(default=0)

    #pdf_url
    #xml_url
    #json_url
    
class 
