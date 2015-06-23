from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from django.contrib import admin
admin.autodiscover()

# from .wizards import DocumentCreateWizard

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pippo.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^robots.txt$', 'commons.views.robots', name='robots'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r"^my_profile/$", 'commons.views.my_profile', name="account_settings"),
    url(r"^profile/(?P<username>[\w\.-]+)/edit/$", 'commons.views.profile_edit', name="profile_edit"),
    url(r"^profile/(?P<username>[\w\.-]+)/$", 'commons.views.user_profile', name="user_profile"),
    # url(r'^/mayansources/create/from/local/multiple/$', DocumentCreateWizard.as_view(), name='commons_document_create_multiple'),
    url(r'^mayan', include('mayan.urls')),
    url(r'^sources', include('sources.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^info/', include('django.contrib.flatpages.urls')),
    url(r"^$", TemplateView.as_view(template_name="homepage.html"), name="commons.home"),
    url(r"^test/$", TemplateView.as_view(template_name="test.html"), name="home"),
    url(r"^cops/$", 'commons.views.cops_tree', name="cops_tree"),
    url(r"^project/(?P<project_slug>[\w-]+)/apply/(?P<username>[\w\.-]+)/$", 'commons.views.apply_for_membership', name="apply_for_membership"),
    url(r"^project/(?P<project_slug>[\w-]+)/accept/(?P<username>[\w\.-]+)/$", 'commons.views.accept_application', name="accept_application"),
    url(r"^project/(?P<project_id>[\d-]+)/oer_new/$", 'commons.views.project_add_oer', name="project_add_oer"),
    url(r"^project/(?P<project_slug>[\w-]+)/edit/$", 'commons.views.project_edit_by_slug', name="project_edit_by_slug"),
    url(r"^project/edit/$", 'commons.views.project_edit', name="project_edit"),
    url(r"^project/(?P<project_slug>[\w-]+)/project_new/$", 'commons.views.project_new_by_slug', name="create_subproject"),
    url(r"^project/(?P<project_slug>[\w-]+)/oers/$", 'commons.views.oer_list', name="oer_list"),
    url(r"^project/(?P<project_slug>[\w-]+)/$", 'commons.views.project_detail_by_slug', name="project_detail"),
    url(r"^repos/$", 'commons.views.repo_list', name="repo_list"),
    url(r"^repos_by/(?P<username>[\w\.-]+)/$", 'commons.views.repos_by_user', name="repos_by_user"),
    url(r"^repositories/contributors/$", 'commons.views.repo_contributors', name="repo_contributors"),
    url(r"^repo/new/$", 'commons.views.repo_new', name="repo_new"),
    url(r"^repo/save/$", 'commons.views.repo_save', name="repo_save"),
    url(r"^repo/(?P<repo_slug>[\w-]+)/edit/$", 'commons.views.repo_edit_by_slug', name="repo_edit"),
    url(r"^repo/(?P<repo_slug>[\w-]+)/$", 'commons.views.repo_detail_by_slug', name="repo_detail"),
    url(r"^repo_oers/(?P<repo_slug>[\w-]+)/$", 'commons.views.repo_oers_by_slug', name="repo_oers"),
    url(r"^repos/search/$", 'commons.views.repos_search', name="repos_search"),
    url(r"^oer/edit/$", 'commons.views.oer_edit', name='oer_new_edit'),
    url(r"^oer/add_document/$", 'commons.views.oer_add_document', name='oer_add_document'),  
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/edit/$", 'commons.views.oer_edit_by_slug', name="oer_edit"),
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/$", 'commons.views.oer_detail_by_slug', name="oer_detail"),
    url(r"^oers/by_project/$", 'commons.views.oers_by_project', name="oers_by_project"),
    url(r"^oers/search/$", 'commons.views.oers_search', name="oers_search"),
    # url(r"^oers/by_project/$", 'commons.views.oers_by_project', name="oers_by_project"),
    # url(r"^oers/by_project/$", 'commons.views.oers_by_project', name="oers_by_project"),
    # url(r"^oers/by_user/$", 'commons.views.oers_by_user', name="oers_by_user"),
    # url(r"^oers/search/$", 'commons.views.oers_search', name="oers_search"),
)
