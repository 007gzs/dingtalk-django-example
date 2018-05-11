# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.admintools import ExportMixin
from django.core.exceptions import PermissionDenied

from apiview import admin
from django import forms

from core.model import BaseModel


class BaseAdmin(admin.BaseAdmin):
    extend_normal_fields = True
    exclude_list_display = ['remark', 'modify_time']
    list_display = []
    heads = ['id']
    tails = ['create_time', 'delete_status', 'remark']
    readonly_fields = ['create_time', 'modify_time']
    change_view_readonly_fields = []
    editable_fields = forms.ALL_FIELDS
    list_filter = ['create_time', ]
    limits = None
    advanced_filter_fields = []

    def __init__(self, *args, **kwargs):
        super(BaseAdmin, self).__init__(*args, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        db_field.remote_field.through._meta.auto_created = True
        return super(BaseAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def delete_view(self, *args, **kwargs):
        raise PermissionDenied('No Delete Permission Allowed')


class ExportAdmin(ExportMixin, BaseAdmin):
    pass


def site_register(model_or_iterable, admin_class=None, site=None, dismiss_create_time=False, **options):
    if admin_class is None:
        admin_class = BaseAdmin
    if not isinstance(model_or_iterable, (list, set, tuple)):
        model_or_iterable = [model_or_iterable]
    for m in model_or_iterable:
        if issubclass(m, BaseModel):
            if 'exclude_list_display' in options:
                options['exclude_list_display'] = ['remark', 'modify_time'] + list(options['exclude_list_display'])
            if 'list_filter' in options and not dismiss_create_time and 'create_time' not in options['list_filter']:
                options['list_filter'] = ['create_time', ] + list(options['list_filter'])
        admin.site_register(m, admin_class, site, **options)
