# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import redis
from dingtalk.storage.kvstorage import KvStorage
from django.conf import settings
from dingtalk.client import isv

from . import models, constants

redis_client = redis.Redis.from_url(settings.REDIS_DINGTALK_URL)


class ISVClient(isv.ISVClient):
    def __init__(self, suite_key, suite_secret, token=None, aes_key=None, storage=None, timeout=None, auto_retry=True):
        if storage is None:
            storage = KvStorage(redis_client)
        super(ISVClient, self).__init__(suite_key, suite_secret, token, aes_key, storage, timeout, auto_retry)

    def get_corp_model(self, corp_id):
        from . import models
        return models.Corp.objects.filter(suite_id=self.suite_key, corpid=corp_id).first()

    def get_permanent_code_from_cache(self, corp_id):
        ret = super(ISVClient, self).get_permanent_code_from_cache(corp_id)
        if not ret:
            corp = self.get_corp_model(corp_id)
            if corp is not None and corp.permanent_code:
                self.cache.permanent_code.set(corp_id, corp.permanent_code)
                ret = corp.permanent_code
        return ret

    def get_ch_permanent_code_from_cache(self, corp_id):
        ret = super(ISVClient, self).get_ch_permanent_code_from_cache(corp_id)
        if not ret:
            corp = self.get_corp_model(corp_id)
            if corp is not None and corp.ch_permanent_code:
                self.cache.ch_permanent_code.set(corp_id, corp.ch_permanent_code)
                ret = corp.ch_permanent_code
        return ret


def set_agent(corp_model, agents, agent_type):
    for agent in agents:
        a = models.Agent.objects.get_all_queryset().filter(appid=agent['appid'], suite_id=corp_model.suite_id).first()
        if a is None:
            a = models.Agent()
            a.appid = agent['appid']
            a.suite_id = corp_model.suite_id
            a.agent_type = agent_type
        a.name = agent['agent_name']
        a.logo_url = agent['logo_url']
        a.save_or_update()
        ca = models.CorpAgent.objects.get_all_queryset().filter(agentid=agent['agentid'],
                                                                agent_id=a.pk, corp_id=corp_model.pk).first()
        if ca is None:
            ca = models.CorpAgent()
            ca.agentid = agent['agentid']
            ca.agent_id = a.pk
            ca.corp_id = corp_model.pk
            ca.save(force_insert=True)


def set_corp_info(corp_model, corp_info):
    auth_corp_info = corp_info.get('auth_corp_info', {})
    for key in ('corp_logo_url', 'corp_name', 'industry', 'invite_code', 'license_code', 'auth_channel',
                'auth_channel_type', 'is_authenticated', 'auth_level', 'invite_url'):
        value = auth_corp_info.get(key, None)
        if value is not None:
            setattr(corp_model, key, value)
    corp_model.save_changed()
    agents = corp_info.get('auth_info', {}).get('agent', [])
    set_agent(corp_model, agents, constants.AGENT_TYPE_CODE.MICRO.code)
    channel_agents = corp_info.get('channel_auth_info', {}).get('channelAgent', [])
    set_agent(corp_model, channel_agents, constants.AGENT_TYPE_CODE.CHANNEL.code)
