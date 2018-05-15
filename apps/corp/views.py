# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.views import ViewSite, fields
from rest_framework.response import Response

from core import view

from . import biz

site = ViewSite(name='isv', app_name='apps.corp')


@site
class TestSyncCorp(view.AdminApi):

    def get_context(self, request, *args, **kwargs):
        biz.sync_corp()
        return 'ok'


@site
class JsapiOauth(view.APIBase):

    def get_context(self, request, *args, **kwargs):
        ret = biz.client.get_jsapi_params(request.params.href)
        ret['errcode'] = 0
        return Response(ret)

    class Meta:
        param_fields = (
            ('href', fields.IntegerField(help_text='href', required=True)),
        )


@site
class UserInfoByCode(view.APIBase):

    def get_context(self, request, *args, **kwargs):
        ret = biz.client.user.getuserinfo(request.params.code)
        ret['errcode'] = 0
        return Response(ret)

    class Meta:
        param_fields = (
            ('code', fields.IntegerField(help_text='code', required=True)),
        )


@site
class UserInfoByUserId(view.APIBase):

    def get_context(self, request, *args, **kwargs):
        ret = biz.client.user.get(request.params.userid)
        ret['errcode'] = 0
        return Response(ret)

    class Meta:
        param_fields = (
            ('userid', fields.IntegerField(help_text='userid', required=True)),
        )


urlpatterns = site.urlpatterns
