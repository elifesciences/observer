from annoying.fields import JSONField
from django.db import models
from django.db.models import (
    BigIntegerField, PositiveSmallIntegerField, PositiveIntegerField,
    CharField, DateTimeField, TextField, NullBooleanField, EmailField,
    ManyToManyField, URLField
)

# see `observer.consume.content_type_from_endpoint` for these values
# essentially they are slugified api endpoints, e.g.: `/digests/id` => digests-id
LAX_AJSON = 'lax-ajson'
METRICS_SUMMARY = 'elife-metrics-summary'
PRESSPACKAGE = 'press-packages-id'
PROFILE = 'profiles-id'
# DIGEST = 'digests-id' # old, do not use, remove once RawJSON in db is removed

DIGEST = 'digest'
LABS_POST = 'labs-post'
COMMUNITY = 'community'
INTERVIEW = 'interview'
COLLECTION = 'collection'
BLOG_ARTICLE = 'blog-article'
FEATURE = 'feature'
EDITORIAL = 'editorial'
PODCAST = 'podcast'

# used in `reports.py` to group certain content types together
COMMUNITY_CONTENT_TYPE_LIST = [
    INTERVIEW,
    COLLECTION,
    BLOG_ARTICLE,
    FEATURE,
    EDITORIAL
]

# used in `reports.py` to group certain content types together
MAGAZINE_CONTENT_TYPE_LIST = [
    EDITORIAL, FEATURE, PODCAST, COLLECTION, DIGEST, INTERVIEW
]

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

def json_type_choices():
    return [
        (LAX_AJSON, 'lax article json'),
        # we don't serve certain dates with the article-json for some reason
        # this means we must do two calls and store two different types of data >:(
        #('lax-version-history', 'lax article version history'),
        (METRICS_SUMMARY, 'elife-metrics summary data'),

        # ---

        (PRESSPACKAGE, 'presspackage summary data'),
        (PROFILE, 'profiles'),
        (DIGEST, 'digests'),
    ]

class RawJSON(models.Model):
    msid = CharField(max_length=25) # todo: rename this field to just 'id'
    version = PositiveSmallIntegerField(null=True, blank=True) # only used by Article objects
    json = JSONField()
    json_type = CharField(max_length=25, choices=json_type_choices(), null=False, blank=False)

    class Meta:
        unique_together = ('msid', 'version')
        ordering = ('-msid', 'version') # [09561 v1, 09561 v2, 09560 v1]

    def __str__(self):
        return self.msid

    def __repr__(self):
        if self.version:
            return '<RawJSON %r %sv%s>' % (self.json_type, self.msid, self.version)
        return '<RawJSON %r %s>' % (self.json_type, self.msid)

# TODO - this would require scraping full press package data
# class PressPackageContact(models.Model):
#    id = CharField(max_length=150, primary_key=True)
#    name = CharField(max_length=150)

class PressPackage(models.Model):
    id = CharField(max_length=8, primary_key=True)
    title = CharField(max_length=255)
    published = DateTimeField()
    updated = DateTimeField(blank=True, null=True)
    subjects = ManyToManyField(Subject, blank=True, help_text="subjects this press package mentions directly")
    # TODO - this would require scraping full press package data
    #articles = ManyToManyField(Article, blank=True, help_text="articles this press package mentions directly")
    #contacts = ManyToManyField(PressPackageContact, blank=True)

    def __str__(self):
        return self.title

    def __repr__(self):
        return '<PressPackage %r>' % self.id

class Profile(models.Model):
    id = CharField(max_length=8, primary_key=True)
    # name = CharField(max_length=255) # disabled in anticipation of GDPR
    # https://support.orcid.org/knowledgebase/articles/116780-structure-of-the-orcid-identifier
    # four groups of four digits seperated by hyphens
    # orcid = CharField(max_length=19, null=True, blank=True) # disabled in anticipation of GDPR

    # WARN: this is data used in reports that cannot be re-created from the API
    # it doesn't exist anywhere else. all other data in observer can be re-scraped and re-generated except this.
    # as such, it doesn't belong here but in the profiles db
    datetime_record_created = DateTimeField(auto_now_add=True, help_text="added to the *observer database*, not date of profile creation")

    class Meta:
        ordering = ('-datetime_record_created',)

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<Profile "%s">' % self

class ContentCategory(models.Model):
    name = CharField(max_length=150, primary_key=True) # slug
    label = CharField(max_length=150)

    class Meta:
        ordering = ('name',) # alphabetically, asc

    def __str__(self):
        return self.label

    def __repr__(self):
        return '<ContentCategory "%s">' % self.name


CONTENT_TYPE_CHOICES = [
    INTERVIEW,
    COLLECTION,
    BLOG_ARTICLE,
    FEATURE,
    DIGEST,
    LABS_POST,
    EDITORIAL,
    PODCAST,
]
CONTENT_TYPE_CHOICES = zip(CONTENT_TYPE_CHOICES, CONTENT_TYPE_CHOICES)

IMAGE_MIME_CHOICES = [
    ('jpg', 'image/jpeg'),
    ('png', 'image/png'),
]

class Content(models.Model):
    id = CharField(max_length=25, primary_key=True)
    content_type = CharField(max_length=12, choices=CONTENT_TYPE_CHOICES)

    title = CharField(max_length=255)
    description = TextField(null=True)
    image_uri = URLField(max_length=500, null=True)
    image_height = PositiveSmallIntegerField(null=True)
    image_width = PositiveSmallIntegerField(null=True)
    image_mime = CharField(max_length=10, choices=IMAGE_MIME_CHOICES, null=True)
    datetime_published = DateTimeField()
    datetime_updated = DateTimeField(null=True)

    categories = models.ManyToManyField(ContentCategory)

    datetime_record_created = DateTimeField(auto_now_add=True)
    datetime_record_updated = DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-datetime_updated', '-datetime_published',)

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<Content "%s">' % self
