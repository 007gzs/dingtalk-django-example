# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.err_code import ErrCode
from apiview.exceptions import CustomError
from apiview.views import ViewSite, fields
from dingtalk.core.constants import SuitePushType
from django.contrib.auth import login, authenticate
from django.utils.encoding import force_text
from rest_framework.response import Response

from core import view, constants as core_constants
from example import celery
from . import models, constants, biz, cache, serializer


site = ViewSite(name='isv', app_name='apps.isv')


@site
class TestCorpInfo(view.AdminApi):

    def get_context(self, request, *args, **kwargs):
        return biz.sync_corp(request.params.corp_pk)

    class Meta:
        param_fields = (
            ('corp_pk', fields.IntegerField(help_text='corp_pk', required=True)),
        )


@site
class SuiteCallback(view.APIBase):

    name = '授权事件接收URL'

    def proc_message(self, suite_key, message):
        event_type = message.get('EventType', None)
        ret = 'success'
        if event_type in (SuitePushType.CHECK_CREATE_SUITE_URL.value, SuitePushType.CHECK_UPDATE_SUITE_URL.value):
            ret = message.get('Random', '')
        elif event_type == SuitePushType.TMP_AUTH_CODE.value:
            permanent_code_data = message.get('__permanent_code_data', {})
            auth_corp_info = permanent_code_data.get('auth_corp_info', {})
            permanent_code = permanent_code_data.get('permanent_code', None)
            ch_permanent_code = permanent_code_data.get('ch_permanent_code', None)
            corpid = auth_corp_info.get('corpid', None)
            corp_name = auth_corp_info.get('corp_name', None)

            if permanent_code is None or corpid is None or corp_name is None:
                ret = 'fail'
            else:
                corp = models.Corp.objects.get_all_queryset().filter(suite_id=suite_key, corpid=corpid).first()
                if corp is None:
                    corp = models.Corp()
                    corp.suite_id = suite_key
                    corp.corpid = corpid
                if corp.status == constants.CORP_STSTUS_CODE.NO.code:
                    corp.status = constants.CORP_STSTUS_CODE.AUTH.code
                corp.permanent_code = permanent_code
                if ch_permanent_code is not None:
                    corp.ch_permanent_code = ch_permanent_code
                corp.corp_name = corp_name
                corp.save_or_update()
                celery.async_call(biz.sync_corp, corp.pk)

        elif event_type == SuitePushType.CHANGE_AUTH.value:
            pass

        elif event_type == SuitePushType.SUITE_RELIEVE.value:
            corp_id = message.get('AuthCorpId', None)
            if corp_id is None:
                ret = 'fail'
            else:
                corp = models.Corp.objects.get_all_queryset().filter(corpid=corp_id, suite_id=suite_key).first()
                if corp is not None:
                    corp.status = constants.CORP_STSTUS_CODE.NO.code
                    corp.save_changed()
                    for corp_agent in models.CorpAgent.objects.filter(corp_id=corp.pk):
                        corp_agent.delete()
        elif event_type == SuitePushType.CHECK_SUITE_LICENSE_CODE.value:
            pass
        elif event_type != SuitePushType.SUITE_TICKET.value:
            self.logger.warning("unkown event_type : %s %s", suite_key, message)
        return ret

    def get_context(self, request, suite_key=None, *args, **kwargs):
        self.logger.info("receive_ticket msg path: %s query: %s, body: %s",
                         request.path, request.META['QUERY_STRING'], self.get_req_body(request))
        msg = self.get_req_body(request)
        assert msg
        msg = force_text(msg)
        suite = models.Suite.objects.filter(suite_key=suite_key).first()
        assert suite
        client = suite.get_suite_client()
        message = client.parse_message(msg, request.params.signature, request.params.timestamp, request.params.nonce)
        self.logger.info("receive_ticket msg: %s" % force_text(message))

        return Response(client.crypto.encrypt_message(self.proc_message(suite_key, message)))

    class Meta:
        path = "suite/callback/(?P<suite_key>[0-9a-zA-Z]+)"
        param_fields = (
            ('timestamp', fields.CharField(help_text='timestamp', required=True)),
            ('nonce', fields.CharField(help_text='nonce', required=True)),
            ('signature', fields.CharField(help_text='signature', required=True))
        )


class CorpAgentMixin(object):

    param_fields = (
        ('corp_id', fields.CharField(help_text='corp_id', required=True)),
        ('app_id', fields.IntegerField(help_text='app_id', required=True)),
    )

    @classmethod
    def get_corp_agent_info(cls, request):
        corp_agent_id = cache.CorpAgentCache.get("%s|||%s" % (request.params.app_id, request.params.corp_id))
        if corp_agent_id is not None:
            corp_agent = models.CorpAgent.get_obj_by_pk_from_cache(corp_agent_id)
            if corp_agent is not None and corp_agent.delete_status == core_constants.DELETE_CODE.NORMAL.code:
                return corp_agent
            cache.CorpAgentCache.delete("%s|||%s" % (request.params.app_id, request.params.corp_id))
        agent = models.Agent.get_obj_by_unique_key_from_cache(appid=request.params.app_id)
        if agent is None:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM)
        suite = agent.suite
        corp = models.Corp.objects.filter(corpid=request.params.corp_id, suite_id=suite.suite_key).first()
        if corp is None:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM)

        corp_agent = models.CorpAgent.objects.filter(agent_id=agent.appid, corp_id=corp.pk).first()
        if corp_agent is None:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM)
        cache.CorpAgentCache.set("%s|||%s" % (request.params.app_id, request.params.corp_id), corp_agent.pk)
        return corp_agent


@site
class JsConfig(view.APIBase, CorpAgentMixin):

    def get_context(self, request, *args, **kwargs):
        url = request.META.get('HTTP_REFERER', None)
        if not url:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM, message='cannot found referer')
        corp_agent = self.get_corp_agent_info(request)
        client = corp_agent.get_client()
        if client is None:
            raise CustomError(ErrCode.ERR_COMMON_BAD_PARAM)
        ret = client.get_jsapi_params(url)
        ret['agentId'] = corp_agent.agentid
        return ret

    class Meta:
        param_fields = CorpAgentMixin.param_fields


@site
class JsLogin(view.APIBase, CorpAgentMixin):

    def get_context(self, request, *args, **kwargs):

        corp_agent = self.get_corp_agent_info(request)
        client = corp_agent.get_client()
        user_info = client.user.getuserinfo(request.params.code)
        corp_user = biz.get_corp_user(user_info['userid'], corp_agent.corp)
        assert corp_user
        if corp_user.user.last_deviceid != user_info['deviceId']:
            corp_user.user.last_deviceid = user_info['deviceId']
            corp_user.user.save_changed()
        corp_user = authenticate(isv_corp_user_id=corp_user.pk)
        if corp_user is not None:
            login(request, corp_user)
        return serializer.CorpUserSerializer(corp_user).data

    class Meta:
        param_fields = CorpAgentMixin.param_fields + (
            ('code', fields.CharField(help_text='code', required=True)),
        )


class DingtalkCorpUserBase(view.APIBase):

    def get_context(self, request, *args, **kwargs):
        raise NotImplementedError

    def check_api_permissions(self, request, *args, **kwargs):
        if not isinstance(request.user, models.CorpUser):
            raise CustomError(ErrCode.ERR_AUTH_NOLOGIN)

    class Meta:
        path = '/'


@site
class UserInfo(DingtalkCorpUserBase):

    def get_context(self, request, *args, **kwargs):
        return serializer.CorpUserSerializer(request.user).data


urlpatterns = site.urlpatterns
