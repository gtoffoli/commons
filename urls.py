
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib import admin
from django.contrib.flatpages import views as flatpages_views

from filebrowser.sites import site
import commons
from commons import search_indexes
from commons.views import UserAutocomplete, FeaturedAutocompleteView # , OerAutocomplete
from commons import bookmarklets
from commons.api import router
import commons.text_analysis

if settings.HAS_SAML2:
    import djangosaml2
    from djangosaml2.urls import urlpatterns as saml2_urls

if settings.DJANGO_VERSION > 1:
    from django.urls import path
    urlpatterns = [
        path('admin/filebrowser/', site.urls),
        path('admin/', admin.site.urls),
    ]
else:
    urlpatterns = [
        url(r'^admin/filebrowser/', include(site.urls)),
        url(r'^admin/', include(admin.site.urls)),
    ]

urlpatterns += [
    url(r'^robots.txt$', commons.views.robots, name='robots'),
    url(r'^error/$', commons.views.error, name='error'),
    url(r'^dmuc$', TemplateView.as_view(template_name='dmuc/home.html')),
    url(r'^ViewerJS', TemplateView.as_view(template_name='viewerjs/index.html')),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^xapi/', include('xapi_client.urls')),
    url(r'^datatrans/', include('datatrans.urls')),
    url(r'^accounts/', include('allauth.urls')),
    # url(r'^admin/filebrowser/', include(filebrowser.sites.urls)),
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^my_mail/', include('django_messages.urls')),
    url(r'^weblog/', include('zinnia.urls', namespace='zinnia')),
    url(r'^forum/', include('pybb.urls', namespace='pybb')),
    url(r'^comments/', include('django_comments.urls')),
    # url(r"^notification/", include("notification.urls")),
    url(r"^user_welcome/$", commons.views.user_welcome, name="user_welcome"),
    url(r"^my_profile/$", commons.views.my_profile, name="account_settings"),
    url(r"^my_home/$", commons.views.my_home, name="user_home"),
    url(r"^my_preferences/$", commons.views.my_preferences, name="my_preferences"),
    url(r"^edit_preferences/$", commons.views.edit_preferences, name="edit_preferences"),
    url(r"^dashboard/(?P<username>[\w\.-]+)/new_posts/$", commons.views.new_posts, name="new_posts"),
    url(r"^profile/(?P<username>[\w\.-]+)/edit/$", commons.views.profile_edit, name="profile_edit"),
    url(r"^profile/(?P<username>[\w\.-]+)/mentor_edit/$", commons.views.profile_mentor_edit, name="profile_mentor_edit"),
    url(r"^profile/(?P<username>[\w\.-]+)/upload/$", commons.views.profile_avatar_upload, name="profile_avatar_upload"),
    url(r"^profile/(?P<username>[\w\.-]+)/add_document/$", commons.views.profile_add_document, name='profile_add_document'),  
    url(r"^profile/(?P<username>[\w\.-]+)/delete_document/$", commons.views.profile_delete_document, name='profile_delete_document'),  
    url(r"^profile/(?P<username>[\w\.-]+)/$", commons.views.user_profile, name="user_profile"),
    url(r"^profile_strict/(?P<username>[\w\.-]+)/$", commons.views.user_strict_profile, name="user_strict_profile"),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r"^$", commons.views.home, name="commons.home"),
    url(r"^press_releases/$", commons.views.press_releases, name="press_releases"),
    url(r"^template_test/$", TemplateView.as_view(template_name="test.html"), name="test"),
    url(r"^cops/$", commons.views.cops_tree, name="cops_tree"),
    url(r"^create_project_folders/$", commons.views.create_project_folders, name="create_project_folders"),
    url(r"^projects/search/$", commons.views.projects_search, name="projects_search"),
    #180924 MMR url(r"^projects/$", commons.views.projects, name="projects"),
    url(r"^project/(?P<project_slug>[\w-]+)/apply/(?P<username>[\w\.-]+)/$", commons.views.apply_for_membership, name="apply_for_membership"),
    url(r"^project/(?P<project_slug>[\w-]+)/accept/(?P<username>[\w\.-]+)/$", commons.views.accept_application, name="accept_application"),
    url(r"^project/(?P<project_id>[\d-]+)/oer_new/$", commons.views.project_add_oer, name="project_add_oer"),
    url(r"^lp_new/$", commons.views.user_add_lp, name="user_add_lp"),
    url(r"^project/(?P<project_id>[\d-]+)/lp_new/$", commons.views.project_add_lp, name="project_add_lp"),
    url(r"^project/(?P<project_id>[\d-]+)/toggle_supervisor_role/$", commons.views.project_toggle_supervisor_role, name="project_toggle_supervisor_role"),
    url(r"^project/(?P<project_id>[\d-]+)/compose_message/$", commons.views.project_compose_message, name="project_compose_message"),
    url(r"^project/(?P<project_slug>[\w-]+)/mailing_list/$", commons.views.project_mailing_list, name="project_mailing_list"),
    url(r"^project/(?P<project_id>[\d-]+)/create_forum/$", commons.views.project_create_forum, name="project_create_forum"),
    url(r"^forum_edit/(?P<forum_id>[\d-]+)/$", commons.views.forum_edit_by_id, name="forum_edit"),
    # url(r"^project/(?P<project_id>[\d-]+)/create_room/$", 'commons.views.project_create_room', name="project_create_room"),
    # url(r"^project/(?P<project_id>[\d-]+)/sync_xmpp/$", 'commons.views.project_sync_xmppaccounts', name="project_sync_xmppaccounts"),
    url(r"^project/(?P<project_id>[\d-]+)/paste_oer/(?P<oer_id>[\d-]+)/$", commons.views.project_paste_oer, name="project_paste_oer"),
    url(r"^project/(?P<project_id>[\d-]+)/paste_lp/(?P<lp_id>[\d-]+)/$", commons.views.project_paste_lp, name="project_paste_lp"),
    url(r"^project/(?P<project_id>[\d-]+)/add_shared_oer/(?P<oer_id>[\d-]+)/$", commons.views.project_add_shared_oer, name="project_add_shared_oer"),
    url(r"^shared_oer_delete/(?P<shared_oer_id>[\d-]+)/$", commons.views.shared_oer_delete, name="shared_oer_delete"),
    url(r"^project/(?P<project_id>[\d-]+)/add_shared_lp/(?P<lp_id>[\d-]+)/$", commons.views.project_add_shared_lp, name="project_add_shared_lp"),
    url(r"^project/(?P<project_id>[\d-]+)/clone_lp/(?P<lp_id>[\d-]+)/$", commons.views.project_clone_lp, name="project_clone_lp"),
    url(r"^shared_lp_delete/(?P<shared_lp_id>[\d-]+)/$", commons.views.shared_lp_delete, name="shared_lp_delete"),
    url(r"^project/(?P<project_slug>[\w-]+)/edit/$", commons.views.project_edit_by_slug, name="project_edit_by_slug"),
    url(r"^project/(?P<project_slug>[\w-]+)/edit_mm/$", commons.mentoring.project_mentoring_model_edit, name="project_mentoring_model_edit"),
    url(r"^project/(?P<project_slug>[\w-]+)/edit_mp/$", commons.mentoring.project_mentoring_policy_edit, name="project_mentoring_policy_edit"),
    url(r"^project/(?P<project_id>[\d-]+)/propose/$", commons.views.project_propose, name="project_propose"),
    url(r"^project/(?P<project_id>[\d-]+)/delegate/$", commons.mentoring.project_delegate_admin, name="project_delegate_admin"),
    url(r"^project/(?P<project_id>[\d-]+)/draft_back/$", commons.mentoring.project_draft_back, name="project_draft_back"),
    url(r"^project/(?P<project_id>[\d-]+)/set_prototype_state/$", commons.mentoring.set_prototype_state, name="set_prototype_state"),
    url(r"^project/(?P<project_id>[\d-]+)/open/$", commons.views.project_open, name="project_open"),
    url(r"^project/(?P<project_id>[\d-]+)/close/$", commons.views.project_close, name="project_close"),
    url(r"^project/edit/$", commons.views.project_edit, name="project_edit"),
    url(r"^project/(?P<project_slug>[\w-]+)/upload/logo/$", commons.views.project_logo_upload, name="project_logo_upload"),
    url(r"^project/(?P<project_slug>[\w-]+)/upload/image/$", commons.views.project_image_upload, name="project_image_upload"),
    url(r"^project/(?P<project_slug>[\w-]+)/project_new/(?P<type_name>[\w-]+)/$", commons.views.project_new_by_slug, name="create_subproject"),
    url(r"^project/(?P<project_slug>[\w-]+)/oers/$", commons.views.oer_list, name="oer_list"),
    url(r"^project/(?P<project_slug>[\w-]+)/project_results/$", commons.views.project_results, name="project_results"),
    url(r"^folder/add_subfolder/$", commons.views.folder_add_subfolder, name="folder_add_subfolder"),
    url(r"^folder/add_document/$", commons.views.folder_add_document, name="folder_add_document"),
    url(r"^folder/add_resource_online/$", commons.views.folder_add_resource_online, name="folder_add_resource_online"),
    url(r"^folder/(?P<folder_id>[\d-]+)/edit/$", commons.views.folder_edit, name="folder_edit"),
    url(r"^folder/(?P<folder_id>[\d-]+)/delete/$", commons.views.folder_delete, name="folder_delete"),
    url(r"^folder/(?P<project_slug>[\w-]+)/$", commons.views.folder_detail, name="folder_detail"),
    url(r"^folder/(?P<path>[/\w\d-]+)$", commons.views.library_traverse),
    url(r"^project/add_document/$", commons.views.project_add_document, name="project_add_document"),
    url(r"^project/add_resource_online/$", commons.views.project_add_resource_online, name="project_add_resource_online"),
    url(r"^folderdocument/(?P<folderdocument_id>[\d-]+)/delete/$", commons.views.folderdocument_delete, name="folderdocument_delete"),
    url(r"^folderdocument/(?P<folderdocument_id>[\d-]+)/edit/$", commons.views.folderdocument_edit, name="folderdocument_edit"),
    url(r"^online_resource/(?P<folderdocument_id>[\d-]+)/edit/$", commons.views.online_resource_edit, name="online_resource_edit"),
    url(r"^project/(?P<project_slug>[\w-]+)/add_member/$", commons.views.project_add_member, name="project_add_member"),
    url(r"^project/(?P<project_slug>[\w-]+)/bulk_add_members/$", commons.views.bulk_add_members, name="bulk_add_members"),
    url(r"^project/(?P<project_slug>[\w-]+)/send_one2one_message/$", commons.mentoring.project_send_one2one_message, name="project_send_one2one_message"),
    url(r"^set_mentor/$", commons.mentoring.project_set_mentor, name="project_set_mentor"),
    url(r"^accept_mentor/$", commons.views.project_accept_mentor, name="project_accept_mentor"),
    url(r"^select_mentoring_journey/$", commons.views.project_select_mentoring_journey, name="project_select_mentoring_journey"),
    url(r"^browse_people/$", commons.views.browse_people, name="browse_people"),
    url(r"^people/search/$", commons.views.people_search, name="people_search"),
    url(r"^browse_mentors/$", commons.views.browse_mentors, name="browse_mentors"),
    url(r"^browse/$", commons.views.browse, name="browse"),
    url(r"^repos/$", commons.views.browse_repos, name="browse_repos"),
    url(r"^repos_by/(?P<username>[\w\.-]+)/$", commons.views.repos_by_user, name="repos_by_user"),
    url(r"^repo/new/$", commons.views.repo_new, name="repo_new"),
    url(r"^repo/save/$", commons.views.repo_save, name="repo_save"),
    url(r"^repo/(?P<repo_slug>[\w-]+)/edit/$", commons.views.repo_edit_by_slug, name="repo_edit"),
    url(r"^repo/(?P<repo_id>[\d-]+)/submit/$", commons.views.repo_submit, name="repo_submit"),
    url(r"^repo/(?P<repo_id>[\d-]+)/withdraw/$", commons.views.repo_withdraw, name="repo_withdraw"),
    url(r"^repo/(?P<repo_id>[\d-]+)/reject/$", commons.views.repo_reject, name="repo_reject"),
    url(r"^repo/(?P<repo_id>[\d-]+)/publish/$", commons.views.repo_publish, name="repo_publish"),
    url(r"^repo/(?P<repo_id>[\d-]+)/un_publish/$", commons.views.repo_un_publish, name="repo_un_publish"),
    url(r"^repo/(?P<repo_id>[\d-]+)/toggle_comments/$", commons.views.repo_toggle_comments, name="repo_toggle_comments"),
    url(r"^repo_oers/(?P<repo_slug>[\w-]+)/$", commons.views.repo_oers_by_slug, name="repo_oers"),
    url(r"^repos/search/$", commons.views.repos_search, name="repos_search"),
    #url(r"^oer/edit/$", commons.views.oer_edit, name='oer_new_edit'),
    url(r"^oer/(?P<oer_slug>[\w-]+)/upload/screenshot/$", commons.views.oer_screenshot_upload, name="oer_screenshot_upload"),
    url(r"^oer/add_document/$", commons.views.oer_add_document, name='oer_add_document'),  
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/edit/$", commons.views.oer_edit_by_slug, name="oer_edit"),
    url(r"^oer/(?P<oer_id>[\d-]+)/submit/$", commons.views.oer_submit, name="oer_submit"),
    url(r"^oer/(?P<oer_id>[\d-]+)/withdraw/$", commons.views.oer_withdraw, name="oer_withdraw"),
    url(r"^oer/(?P<oer_id>[\d-]+)/reject/$", commons.views.oer_reject, name="oer_reject"),
    url(r"^oer/(?P<oer_id>[\d-]+)/publish/$", commons.views.oer_publish, name="oer_publish"),
    url(r"^oer/(?P<oer_id>[\d-]+)/un_publish/$", commons.views.oer_un_publish, name="oer_un_publish"),
    url(r"^oer/(?P<oer_id>[\d-]+)/delete/$", commons.views.oer_delete, name="oer_delete"),
    url(r"^oer/(?P<oer_id>[\d-]+)/toggle_comments/$", commons.views.oer_toggle_comments, name="oer_toggle_comments"),
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/evaluate/$", commons.views.oer_evaluate_by_slug, name="oer_evaluate"),
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/evaluations/$", commons.views.oer_evaluations, name="oer_evaluations"),
    url(r"^oer_evaluation/edit/$", commons.views.oer_evaluation_edit, name='oer_evaluation_new_edit'),
    url(r"^oer_evaluation/(?P<evaluation_id>[\d-]+)/edit/$", commons.views.oer_evaluation_edit_by_id, name="oer_evaluation_edit"),
    url(r"^oer_evaluation/(?P<evaluation_id>[\d-]+)/$", commons.views.oer_evaluation_by_id, name="oer_evaluation"),
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/view/$", commons.views.oer_view_by_slug, name="oer_view"),
    url(r"^oers_by/(?P<username>[\w\.-]+)/$", commons.views.oers_by_user, name="oers_by_user"),
    url(r"^oers/search/$", commons.views.oers_search, name="oers_search"),
    url(r'^serve_ipynb_url/$', commons.views.serve_ipynb_url, name="serve_ipynb_url"),
    url(r'^document/(?P<document_id>[\d-]+)/serve/$', commons.views.document_serve, (), 'document_serve'),
    url(r'^document/(?P<document_id>[\d-]+)/download/$', commons.views.document_download, (), 'document_download'),
    # url(r'^document/(?P<document_id>[\d-]+)/download_range/(?P<page_range>[\d\,-]+)/$', commons.views.document_download_range, (), 'document_download_range'),
    # url(r'^document/(?P<document_id>[\d-]+)/download.pdf/$', commons.views.document_download, (), 'document_download_pdf'),
    url(r'^document/(?P<document_id>[\d-]+)/view/$', commons.views.document_view, (), 'document_view'),
    url(r'^online_resource/(?P<folderdocument_id>[\d-]+)/view/$', commons.views.online_resource_view,  name='online_resource_view'),
    # url(r'^document/(?P<document_id>[\d-]+)/view_range/(?P<page_range>[\d\,-]+)/$', commons.views.document_view_range, (), 'document_view_range'),
    url(r"^document/(?P<document_id>[\d-]+)/delete/$", commons.views.document_delete, name="document_delete"),
    url(r"^document/(?P<document_id>[\d-]+)/up/$", commons.views.document_up, name="document_up"),
    url(r"^document/(?P<document_id>[\d-]+)/down/$", commons.views.document_down, name="document_down"),
    url(r"^lp/edit/$", commons.views.lp_edit, name='lp_edit'),
    url(r"^lp/add_node/$", commons.views.lp_add_node, name='lp_add_node'),  
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/edit/$", commons.views.lp_edit_by_slug, name="lp_edit"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/pathnode_new/$", commons.views.lp_add_node, name="lp_add_node"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/pathnode_add/(?P<oer_id>[\d-]+)/$", commons.views.lp_add_oer, name="lp_add_oer"),
    url(r"^lp/(?P<lp_id>[\d-]+)/submit/$", commons.views.lp_submit, name="lp_submit"),
    url(r"^lp/(?P<lp_id>[\d-]+)/withdraw/$", commons.views.lp_withdraw, name="lp_withdraw"),
    url(r"^lp/(?P<lp_id>[\d-]+)/reject/$", commons.views.lp_reject, name="lp_reject"),
    url(r"^lp/(?P<lp_id>[\d-]+)/publish/$", commons.views.lp_publish, name="lp_publish"),
    url(r"^lp/(?P<lp_id>[\d-]+)/un_publish/$", commons.views.lp_un_publish, name="lp_un_publish"),
    url(r"^lp/(?P<lp_id>[\d-]+)/delete/$", commons.views.lp_delete, name="lp_delete"),
    url(r"^lp/(?P<lp_id>[\d-]+)/toggle_comments/$", commons.views.lp_toggle_comments, name="lp_toggle_comments"),
    url(r"^lp/(?P<lp_id>[\d-]+)/toggle_editor_role/$", commons.views.lp_toggle_editor_role, name="lp_toggle_editor_role"),
    url(r"^lp/(?P<lp_id>[\d-]+)/make_collection/$", commons.views.lp_make_collection, name="lp_make_collection"),
    url(r"^lp/(?P<lp_id>[\d-]+)/make_sequence/$", commons.views.lp_make_sequence, name="lp_make_sequence"),
    url(r"^lp/(?P<lp_id>[\d-]+)/make_unconnected_dag/$", commons.views.lp_make_unconnected_dag, name="lp_make_unconnected_dag"),
    url(r"^lp/(?P<lp_id>[\d-]+)/make_linear_dag/$", commons.views.lp_make_linear_dag, name="lp_make_linear_dag"),
    url(r"^lp/(?P<lp_id>[\d-]+)/make_tree_dag/$", commons.views.lp_make_tree_dag, name="lp_make_tree_dag"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/play/$", commons.views.lp_play_by_slug, name="lp_play"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/download/$", commons.views.lp_download_by_slug, name="lp_download"),
    url(r"^pathnode/edit/$", commons.views.pathnode_edit, name='pathnode_edit'),
    url(r"^pathnode/(?P<node_id>[\d-]+)/edit/$", commons.views.pathnode_edit_by_id, name="pathnode_edit"),
    url(r'^pathnode/(?P<node_id>[\d-]+)/download/$', commons.views.pathnode_download_range, (), 'pathnode_download_range'),
    url(r"^pathnode/(?P<node_id>[\d-]+)/delete/$", commons.views.pathnode_delete, name="pathnode_delete"),
    url(r"^pathnode/(?P<node_id>[\d-]+)/up/$", commons.views.pathnode_up, name="pathnode_up"),
    url(r"^pathnode/(?P<node_id>[\d-]+)/down/$", commons.views.pathnode_down, name="pathnode_down"),
    url(r"^pathnode/(?P<node_id>[\d-]+)/move_before/(?P<other_node_id>[\d-]+)/$", commons.views.pathnode_move_before, name="pathnode_move_before"),
    url(r"^pathnode/(?P<node_id>[\d-]+)/move_after/(?P<other_node_id>[\d-]+)/$", commons.views.pathnode_move_after, name="pathnode_move_after"),
    url(r"^pathnode/(?P<node_id>[\d-]+)/link_after/(?P<other_node_id>[\d-]+)/$", commons.views.pathnode_link_after, name="pathnode_link_after"),
    url(r"^pathedge/(?P<edge_id>[\d-]+)/delete/$", commons.views.pathedge_delete, name="pathedge_delete"),
    url(r"^pathedge/(?P<edge_id>[\d-]+)/move_after/(?P<other_edge_id>[\d-]+)/$", commons.views.pathedge_move_after, name="pathedge_move_after"),
    url(r"^lps/search/$", commons.views.lps_search, name="lps_search"),
    url(r"^resources_by/(?P<username>[\w\.-]+)/$", commons.views.resources_by, name="resources_by"),
    url(r"^testlive/$", commons.views.testlive, name="testlive"),
    url(r'^navigation_autocomplete$', commons.search_indexes.navigation_autocomplete, name='navigation_autocomplete'),
    url('user-autocomplete/$', UserAutocomplete.as_view(), name='user-autocomplete',),
    url('user-fullname-autocomplete/$', commons.views.user_fullname_autocomplete, name='user-fullname-autocomplete',),
    url('repo-autocomplete/$', commons.views.repo_autocomplete, name='repo-autocomplete',),
    url('oer-autocomplete/$', commons.views.oer_autocomplete, name='oer-autocomplete',),
    url('lp-autocomplete/$', commons.views.lp_autocomplete, name='lp-autocomplete',),
    url('featured-autocomplete/$', FeaturedAutocompleteView.as_view(), name='featured-autocomplete'),
    url(r"^report_meeting_in/(?P<project_id>[\d-]+)/$", commons.views.report_meeting_in, name="report_meeting_in"),
    url(r"^report_pageview/$", commons.bookmarklets.report_pageview, name="report_pageview"),
    url(r"^text_analyzer/$", commons.bookmarklets.text_analyzer, name="text_analyzer"),
    url(r"^web_resource_analyzer/$", commons.bookmarklets.web_resource_analyzer, name="web_resource_analyzer"),
    url(r"^analytics/activity_stream/$", commons.analytics.activity_stream, name="activity_stream"),
    url(r"^analytics/user_activity/(?P<username>[\w\.-]+)/$", commons.views.user_activity, name="user_activity"),
    url(r"^analytics/project_activity/(?P<project_slug>[\w-]+)/$",commons.views.project_activity, name="project_activity"),
    url(r"^analytics/forums/$", commons.analytics.forum_analytics, name="forum_analytics"),
    url(r"^analytics/messages/$", commons.analytics.message_analytics, name="message_analytics"),
    url(r"^analytics/oers/$", commons.analytics.oer_analytics, name="oer_analytics"),
    url(r"^analytics/lps/$", commons.analytics.lp_analytics, name="lp_analytics"),
    url(r"^analytics/mailing_list/$", commons.views.mailing_list, name="mailing_list"),
    url(r"^analytics/oer_duplicates/$", commons.analytics.oer_duplicates, name="oer_duplicates"),
    url(r"^analytics/content_languages/$", commons.analytics.content_languages, name="content_languages"),
    url(r"^analytics/count_users/$", commons.analytics.count_users, name="count_users"),
    url(r"^analytics/active_users/$", commons.analytics.active_users, name="active_users"),
    url(r"^analytics/active_comembers/$", commons.analytics.active_comembers, name="active_comembers"),
    url(r"^analytics/contributors/$", commons.analytics.resource_contributors, name="contributors"),
    url(r"^text_dashboard/(?P<obj_type>[\w\.-]+)/(?P<obj_id>[\d-]+)/$", commons.text_analysis.text_dashboard, name="text_dashboard"),
    url(r"^text_dashboard/(?P<obj_type>[\w\.-]+)/(?P<obj_id>.+)$", commons.text_analysis.text_dashboard, name="text_dashboard_by_url"),
    url(r'^brat$', commons.text_analysis.brat, name="brat"),
     # url(r"^bosh_prebind/$", dmuc.views.bosh_prebind, name="bosh_prebind"),
    path('wiki/', include('wiki.urls')),
   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
""" http://stackoverflow.com/questions/28013711/django-zinnia-can-not-get-image-for-entrys-illustration
    https://docs.djangoproject.com/en/1.8/howto/static-files/ """

if settings.HAS_SAML2:
    urlpatterns += [
        url(r"^saml2/acs/commons.home$", commons.views.home, name="commons.home"),
        path('saml2/', include(saml2_urls)),
        url(r'^test/', djangosaml2.views.echo_attributes, name="echo_attributes"),
    ]

if settings.HAS_EARMASTER:
    urlpatterns += [
        path('earmaster/', include('earmaster.urls')),
    ]

if settings.HAS_DMUC:
    urlpatterns += [
        url(r"^project/(?P<project_id>[\d-]+)/create_room/$", 'commons.views.project_create_room', name="project_create_room"),
        url(r"^project/(?P<project_id>[\d-]+)/sync_xmpp/$", 'commons.views.project_sync_xmppaccounts', name="project_sync_xmppaccounts"),
        url(r"^bosh_prebind/$", 'dmuc.views.bosh_prebind', name="bosh_prebind"),
    ]

urlpatterns += i18n_patterns(
    url(r"^project/(?P<project_slug>[\w-]+)/$", commons.views.project_detail_by_slug, name="project_detail"),
    url(r"^project/(?P<project_slug>[\w-]+)/text/$", commons.text_analysis.project_text, name="project_text"),
    url(r"^repo/(?P<repo_slug>[\w-]+)/$", commons.views.repo_detail_by_slug, name="repo_detail"),
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/$", commons.views.oer_detail_by_slug, name="oer_detail"),
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/text/$", commons.text_analysis.oer_text, name="oer_text"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/$", commons.views.lp_detail_by_slug, name="lp_detail"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/text/$", commons.text_analysis.lp_text, name="lp_text"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/download/$", commons.views.lp_download_by_slug, name="lp_download"),
    url(r"^pathnode/(?P<node_id>[\d-]+)/$", commons.views.pathnode_detail, name="pathnode_detail"),
    url(r"^pathnode/(?P<node_id>[\d-]+)/text/$", commons.text_analysis.pathnode_text, name="pathnode_text"),
    url(r"^flatpage/(?P<flatpage_id>[\d-]+)/text/$", commons.text_analysis.flatpage_text, name="flatpage_text"),
    url(r'^(?P<url>.*)$', flatpages_views.flatpage, name='django.contrib.flatpages.views.flatpage'),
)

if settings.USE_HAYSTACK:
    from haystack.views import SearchView
    from commons.search_indexes import commonsModelSearchForm
    from haystack.query import SearchQuerySet
    sqs = SearchQuerySet()
    urlpatterns += [
        url(r'^cercaveloce/', SearchView(
                template='search/search.html',
                searchqueryset=sqs,
                form_class=commonsModelSearchForm,
                results_per_page=100,
                load_all=False
            ), name='haystack_search'),
    #)
    ]
