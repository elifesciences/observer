from observer import models

def known_articles():
    "returns a query set of manuscript_ids from newest to olders"
    return models.ArticleJSON.objects \
        .values_list('msid', flat=True) \
        .order_by('-msid')
