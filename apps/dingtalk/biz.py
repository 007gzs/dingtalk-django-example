# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import redis
from apiview import utility
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
        agent_model = models.Agent.get_obj_by_unique_key_from_cache(appid=agent['appid'])
        if agent_model is None:
            agent_model = models.Agent()
            agent_model.appid = agent['appid']
            agent_model.suite_id = corp_model.suite_id
            agent_model.agent_type = agent_type
        agent_model.name = agent['agent_name']
        agent_model.logo_url = agent['logo_url']
        agent_model.save_or_update()
        ca = models.CorpAgent.objects.get_all_queryset().filter(agentid=agent['agentid'],
                                                                agent_id=agent['appid'], corp_id=corp_model.pk).first()
        if ca is None:
            ca = models.CorpAgent()
            ca.agentid = agent['agentid']
            ca.agent_id = agent['appid']
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


def get_department_ids(corp_client, proced=set(), parent_id=1):
    if parent_id in proced:
        return
    ret = set()
    ret.add(parent_id)
    ids = corp_client.department.list_ids(parent_id)
    proced.add(parent_id)
    ret.update(set(ids))
    for _id in ids:
        ret.update(get_department_ids(corp_client, proced, _id))
    return ret


def set_corp_user(user_info, corp):
    user_id = user_info['userid']
    user = models.User.get_obj_by_unique_key_from_cache(dingid=user_info['dingId'])
    if user is None:
        user = models.User()
        user.dingid = user_info['dingId']
    user.name = user_info['name']
    user.active = user_info['active']
    user.avatar = user_info['avatar']
    user.save_or_update()
    corp_user = models.CorpUser.objects.filter(userid=user_id, corp_id=corp.pk).first()
    if corp_user is None:
        corp_user = models.CorpUser()
        corp_user.userid = user_id
        corp_user.corp = corp
    corp_user.user = user
    hired_date = user_info.get('hiredDate', None)
    if hired_date is not None:
        corp_user.hired_date = utility.timestamp2datetime(hired_date / 1000)
    keys = {'is_admin': 'isAdmin', 'is_senior': 'isSenior', 'is_boss': 'isBoss', 'state_code': 'stateCode',
            'openid': 'openid', 'unionid': 'unionid', 'position': 'position', 'jobnumber': 'jobnumber'}
    for k, v in keys.items():
        value = user_info.get(v, None)
        if value is not None:
            setattr(corp_user, k, value)
    corp_user.save_or_update()

    return corp_user


def sync_user(corp, corp_client, department_id):
    offset = 0
    while True:
        users = corp_client.user.list(department_id)
        for user in users.get('userlist', []):
            offset += 1
            set_corp_user(user, corp)
        if not users.get('hasMore', False):
            return


def sync_corp(corppk):
    corp = models.Corp.get_obj_by_pk_from_cache(corppk)
    if corp is None or corp.suite is None:
        return
    client = corp.suite.get_suite_client()
    if corp.status == constants.CORP_STSTUS_CODE.AUTH.code:
        client.activate_suite(corp.corpid)
        corp.status = constants.CORP_STSTUS_CODE.ACTIVE.code
    corp_info = client.get_auth_info(corp.corpid)
    set_corp_info(corp, corp_info)
    try:
        corp_client = corp.get_dingtalk_client()
        department_ids = get_department_ids(corp_client)
        for department_id in department_ids:
            sync_user(corp, corp_client, department_id)
    except Exception:
        pass
    return corp_info


def refresh_corp_user(user_id, corp):
    client = corp.get_dingtalk_client()
    return set_corp_user(client.user.get(user_id))


def get_corp_user(user_id, corp):
    corp_user = models.CorpUser.objects.filter(userid=user_id, corp_id=corp.pk).first()
    if corp_user is not None:
        return corp_user
    return refresh_corp_user(user_id, corp)
