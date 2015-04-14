from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pippo.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^mayan', include('mayan.urls')),
    url(r'^info/', include('django.contrib.flatpages.urls')),
    url(r"^$", TemplateView.as_view(template_name="homepage.html"), name="home"),
    url(r"^cops/$", 'commons.views.cops_tree', name="cops_tree"),
    url(r"^project/(?P<project_slug>[\w-]+)/$", 'commons.views.project_detail_by_slug', name="project_detail"),
    url(r"^repos/$", 'commons.views.repos_list', name="repos_list"),
    url(r"^repo/(?P<repo_slug>[\w-]+)/$", 'commons.views.repo_detail_by_slug', name="repo_detail"),
)
