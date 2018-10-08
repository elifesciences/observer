from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^report/(?P<name>[\-\w]+)$', views.report, name='report'),
    url(r'^report/(?P<name>[\-\w]+)\.(?P<format_hint>[\w]{1,4})$', views.report, name='report'),
    url(r'^ping$', views.ping, name='ping'),
    url(r'^$', views.landing, name='pub-landing'),
]
