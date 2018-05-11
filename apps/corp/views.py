# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.views import ViewSite

from core import view

from . import biz

site = ViewSite(name='isv', app_name='apps.corp')


@site
class TestSyncCorp(view.AdminApi):

    def get_context(self, request, *args, **kwargs):
        biz.sync_corp()
        return 'ok'


urlpatterns = site.urlpatterns
