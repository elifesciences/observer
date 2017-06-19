from django.conf.urls import url
from . import views

urlpatterns = [
    url('^report/(?P<name>[\-\w]+)/$', views.report, name='temp-report'),
    url('^report/(?P<name>[\-\w]+)$', views.report, name='report'),
    url('^report/(?P<name>[\-\w]+)\.(?P<format_hint>[\w]{1,4})$', views.report, name='report'),
    url(r'^$', views.landing, name='pub-landing'),
]
