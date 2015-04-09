'''
Created on 03/apr/2015
@author: Giovanni Toffoli - LINK srl
'''

from django.contrib import admin

from commons.models import Languages, RepoType, Repo

class LanguagesAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['code', 'name',]}),
    ]
    list_display = ('code', 'name',)
    search_fields = ['code', 'name',]

class RepoTypeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'description',]}),
    ]
    list_display = ('name', 'description',)
    search_fields = ['name',]

class RepoAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['name', 'description', 'repo_type', 'languages', 'url', 'info_page',]}),
    ]
    list_display = ('name', 'description', 'repo_type', 'url', 'info_page', 'created', 'modified',)
    search_fields = ['name', 'description', 'repo_type',]

    def save_model(self, request, obj, form, change):
        obj.lasteditor = request.user
        obj.save()

admin.site.register(Languages, LanguagesAdmin)
admin.site.register(RepoType, RepoTypeAdmin)
admin.site.register(Repo, RepoAdmin)
