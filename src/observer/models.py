from annoying.fields import JSONField
from django.db import models
from django.db.models import (
    BigIntegerField, PositiveSmallIntegerField, PositiveIntegerField,
    CharField, DateTimeField, TextField, BooleanField,
    EmailField,
    ManyToManyField, URLField
)
from observer import utils

# see `observer.consume.content_type_from_endpoint` for these values
# essentially they are slugified api endpoints, e.g.: `/digests/id` => digests-id
LAX_AJSON = 'lax-ajson'
METRICS_SUMMARY = 'elife-metrics-summary'
PRESSPACKAGE = 'press-packages-id'
PROFILE = 'profiles-id'

DIGEST = 'digest'
LABS_POST = 'labs-post'
COMMUNITY = 'community'
INTERVIEW = 'interview'
COLLECTION = 'collection'
BLOG_ARTICLE = 'blog-article'
FEATURE = 'feature'
EDITORIAL = 'editorial'
PODCAST = 'podcast'
REVIEWED_PREPRINT = 'reviewed-preprint'

# insights are regular articles stored in lax but a subset of data
# is stored as a Content type to make RSS feeds more convenient.
INSIGHT = 'insight'

ALL_CONTENT_TYPES = [LAX_AJSON, METRICS_SUMMARY, PRESSPACKAGE, PROFILE, DIGEST, LABS_POST, COMMUNITY, INTERVIEW, COLLECTION, BLOG_ARTICLE, FEATURE, EDITORIAL, PODCAST, REVIEWED_PREPRINT, INSIGHT]

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
    INSIGHT, EDITORIAL, FEATURE, PODCAST, COLLECTION, DIGEST, INTERVIEW
]

# models.Content types that are *not* covered by an entry in models.Article
NON_ARTICLE_CONTENT_TYPE_LIST = [
    INTERVIEW,
    COLLECTION,
    BLOG_ARTICLE,
    LABS_POST,
    PODCAST,
    REVIEWED_PREPRINT
]

#

def find_content_type(val):
    "given a `content_type` value, returns the canonical version or raises a `KeyError`"

    if val in ALL_CONTENT_TYPES:
        return val

    aliases = {
        # PODCAST == 'podcast' and not 'podcast-episode' :(
        'podcast-episodes': PODCAST,
        'podcast-episodes-id': PODCAST,

        # PRESSPACKAGE == 'press-packages-id' :(
        'press-packages-id': PRESSPACKAGE,
        'press-packages': PRESSPACKAGE,

        # PROFILE == 'profiles-id' :(
        # as of 2022-01-31 we have 47k 'profiles-id' in RawJSON
        'profiles': PROFILE,
        'profiles-id': PROFILE,

        # "/articles/{id}/versions/{version}"
        'articles-id-versions-version': LAX_AJSON, # 'lax-ajson'
        'articles-id': LAX_AJSON, # not actually used except in bad tests

        # "/metrics/article-summary" (non-api)
        'metrics-article-summary': METRICS_SUMMARY, # 'elife-metrics-summary'

        # ---

        'digests': DIGEST,
        'digests-id': DIGEST,

        'labs-posts': LABS_POST,
        'labs-posts-id': LABS_POST,

        'interviews': INTERVIEW,
        'interviews-id': INTERVIEW,

        'collections': COLLECTION,
        'collections-id': COLLECTION,

        'blog-articles': BLOG_ARTICLE,
        'blog-articles-id': BLOG_ARTICLE,

        'reviewed-preprints': REVIEWED_PREPRINT,
        'reviewed-preprints-id': REVIEWED_PREPRINT,

        'features': FEATURE,
        'features-id': FEATURE,

        'editorials': EDITORIAL,
        'editorials-id': EDITORIAL,
    }
    if val not in aliases:
        raise KeyError("could not coerce %r to a known content_type" % val)
    return aliases[val]


#

POA, VOR = 'poa', 'vor'
UNKNOWN_TYPE = 'unknown-type'

IMAGE_MIME_CHOICES = [
    ('jpg', 'image/jpeg'),
    ('png', 'image/png'),
]

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

    has_digest = BooleanField(null=True, blank=True, help_text="Null/None means I don't know!")
    has_pdf = BooleanField(null=True, blank=True, help_text="Null/None means I don't know!")

    subject1 = CharField(max_length=50, null=True)
    subject2 = CharField(max_length=50, null=True)
    subject3 = CharField(max_length=50, null=True)

    social_image_uri = URLField(max_length=500, null=True)
    social_image_height = PositiveSmallIntegerField(null=True)
    social_image_width = PositiveSmallIntegerField(null=True)
    social_image_mime = CharField(max_length=10, choices=IMAGE_MIME_CHOICES, null=True)

    class Meta:
        db_table = 'articles'
        indexes = [
            models.Index(fields=["type"], name="type_idx"),
        ]

    datetime_record_created = DateTimeField(auto_now_add=True)
    datetime_record_updated = DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "https://elifesciences.org/articles/" + utils.pad_msid(self.msid)

    def get_pdf_url(self):
        return self.get_absolute_url() + ".pdf"

    def get_xml_url(self):
        return self.get_absolute_url() + ".xml"

    def get_json_url(self):
        return "https://api.elifesciences.org/articles/" + utils.pad_msid(self.msid)

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
        indexes = [
            models.Index(fields=['msid', 'json_type'], name='msid_json_type_idx')
        ]

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

    def get_absolute_url(self):
        return "https://elifesciences.org/for-the-press/{id}".format(id=self.id)

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
    # INSIGHT # lsh@2022-01-21: is this supposed to be missing?
    INTERVIEW,
    COLLECTION,
    BLOG_ARTICLE,
    FEATURE,
    DIGEST,
    LABS_POST,
    EDITORIAL,
    PODCAST,
    REVIEWED_PREPRINT,
]
CONTENT_TYPE_CHOICES = zip(CONTENT_TYPE_CHOICES, CONTENT_TYPE_CHOICES)

class Content(models.Model):
    id = CharField(max_length=25, primary_key=True)
    content_type = CharField(max_length=17, choices=CONTENT_TYPE_CHOICES)

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
        indexes = [
            models.Index(fields=['content_type'], name="content_type_idx")
        ]

    def get_absolute_url(self):
        # todo: pad feature
        path_map = {
            INTERVIEW: "interviews/{id}",
            COLLECTION: "collections/{id}",
            BLOG_ARTICLE: "inside-elife/{id}",
            FEATURE: "articles/{id}",
            EDITORIAL: "articles/{id}",
            INSIGHT: "articles/{id}",
            DIGEST: "digests/{id}",
            LABS_POST: "labs/{id}",
            PODCAST: "podcast/episode{id}",
            REVIEWED_PREPRINT: "reviewed-preprints/{id}",
        }
        assert self.content_type in path_map, "cannot find path to content for content type %r" % self.content_type
        path = path_map[self.content_type].format(id=self.id)
        return "https://elifesciences.org/" + path

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<Content %s "%s">' % (self.content_type, self)
