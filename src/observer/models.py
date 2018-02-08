from annoying.fields import JSONField
from django.db import models
from django.db.models import BigIntegerField, PositiveSmallIntegerField, PositiveIntegerField, CharField, DateTimeField, TextField, NullBooleanField, EmailField

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

def decision_codes():
    "mapping of EJP decision codes to words"
    return [
        ('reject-initial-submission', 'RJI'),
        ('reject-full-submission', 'RJF'),
        ('revise-full-submission', 'RVF'),
        ('accept-full-submission', 'AF'),
        ('encourage-full-submission', 'EF'),
        ('simple-withdraw', 'SW')
    ]


class Subject(models.Model):
    name = CharField(max_length=150, primary_key=True) # slug
    label = CharField(max_length=150)

    class Meta:
        ordering = ('name',) # alphabetically, asc

    def __str__(self):
        return self.label

    def __repr__(self):
        return '<Subject "%s">' % self.name

class Author(models.Model):
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=150, null=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Author "%s">' % self

class Article(models.Model):
    journal_name = CharField(max_length=255)
    msid = BigIntegerField(unique=True, help_text="article identifier from beginning of submission process right through to end of publication.")
    title = CharField(max_length=255, null=True)
    doi = CharField(max_length=255)

    subjects = models.ManyToManyField(Subject)
    authors = models.ManyToManyField(Author)

    abstract = TextField(null=True)
    author_line = TextField(null=True, help_text="abbreviated way of referring to the article's authors")
    author_name = CharField(null=True, max_length=150, help_text="coresponding author name")
    author_email = EmailField(null=True, help_text="corresponding author email.")

    impact_statement = TextField(null=True)
    type = CharField(max_length=50, choices=type_choices(), help_text="article as exported from EJP submission system")
    current_version = PositiveSmallIntegerField(null=True)
    status = CharField(max_length=3, choices=status_choices(), null=True, help_text="article's current status (poa or vor)")
    volume = PositiveSmallIntegerField(null=True)

    num_authors = PositiveSmallIntegerField(null=True)
    num_references = PositiveSmallIntegerField(null=True)

    # with some cleverness these can be calculated
    num_poa_versions = PositiveSmallIntegerField(default=0)
    num_vor_versions = PositiveSmallIntegerField(default=0)

    # these can all be pulled from the article-history endpoint
    datetime_submitted = DateTimeField(null=True, help_text="when the author uploaded their article")

    num_revisions = PositiveSmallIntegerField(null=True, help_text="number of revisions article has currently gone through")

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
    days_publication_to_current_version = PositiveSmallIntegerField(null=True, help_text="day elapsed between v1 and current versionb")

    num_views = PositiveIntegerField(default=0)
    num_downloads = PositiveIntegerField(default=0)
    num_citations = PositiveIntegerField(default=0)
    num_citations_crossref = PositiveIntegerField(default=0)
    num_citations_pubmed = PositiveIntegerField(default=0)
    num_citations_scopus = PositiveIntegerField(default=0)

    # pdf_url
    # xml_url
    # json_url

    has_digest = NullBooleanField(null=True, help_text="Null/None means I don't know!")

    subject1 = CharField(max_length=50, null=True)
    subject2 = CharField(max_length=50, null=True)
    subject3 = CharField(max_length=50, null=True)

    class Meta:
        db_table = 'articles'

    datetime_record_created = DateTimeField(auto_now_add=True)
    datetime_record_updated = DateTimeField(auto_now=True)

    def __str__(self):
        return "%05d" % self.msid

    def __repr__(self):
        return '<Article "%s">' % self

LAX_AJSON, METRICS_SUMMARY = 'lax-ajson', 'elife-metrics-summary'

def ajson_type_choices():
    return [
        (LAX_AJSON, 'lax article json'),
        # we don't serve certain dates with the article-json for some reason
        # this means we must do two calls and store two different types of data >:(
        #('lax-version-history', 'lax article version history'),
        (METRICS_SUMMARY, 'elife-metrics summary data')
    ]

class ArticleJSON(models.Model):
    msid = BigIntegerField()
    version = PositiveSmallIntegerField(null=True, blank=True)
    ajson = JSONField()
    ajson_type = CharField(max_length=25, choices=ajson_type_choices(), null=False, blank=False)

    class Meta:
        unique_together = ('msid', 'version')
        ordering = ('-msid', 'version') # [09561 v1, 09561 v2, 09560 v1]

    def __str__(self):
        return "%05d v%s" % (self.msid, self.version)

    def __repr__(self):
        return '<ArticleJSON "%s">' % self

class ProfileCount(models.Model):
    total = PositiveIntegerField(null=False, blank=False)
    timestamp = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        return "%s" % self.total

    def __repr__(self):
        return '<ProfileCount "%s">' % self
