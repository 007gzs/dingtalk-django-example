# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import redis
from apiview import utility
from django.conf import settings

from dingtalk import SecretClient, AppKeyClient
from dingtalk.storage.kvstorage import KvStorage

from . import models


redis_client = redis.Redis.from_url(settings.REDIS_DINGTALK_URL)

if settings.DINGTALK_USE_APP_KEY:
    client = AppKeyClient(settings.DINGTALK_CORP_ID, settings.DINGTALK_APP_KEY, settings.DINGTALK_APP_SECRET,
                          settings.DINGTALK_TOKEN, settings.DINGTALK_AES_KEY, KvStorage(redis_client))
else:
    client = SecretClient(settings.DINGTALK_CORP_ID, settings.DINGTALK_CORP_SECRET,
                          settings.DINGTALK_TOKEN, settings.DINGTALK_AES_KEY, KvStorage(redis_client))

def get_department_ids(proced=set(), parent_id=None):

    ret = set()
    if parent_id is None:
        scopes = client.user.auth_scopes()
        parent_id = scopes.get('auth_org_scopes', {}).get('authed_dept', [])

    if isinstance(parent_id, (list, tuple)):
        for pid in parent_id:
            ret.update(get_department_ids(proced, pid))
        return ret

    if parent_id in proced:
        return ret
    ret.add(parent_id)
    ids = client.department.list_ids(parent_id)
    proced.add(parent_id)
    ret.update(set(ids))
    for _id in ids:
        ret.update(get_department_ids(proced, _id))
    return ret


def set_corp_user(user_info):
    user_id = user_info['userid']

    corp_user = models.User.objects.filter(userid=user_id).first()
    if corp_user is None:
        corp_user = models.User()
        corp_user.userid = user_id

    hired_date = user_info.get('hiredDate', None)
    if hired_date is not None:
        corp_user.hired_date = utility.timestamp2datetime(hired_date / 1000)

    lowerkeys = ('userid', 'name', 'tel', 'mobile', 'email', 'active', 'position', 'avatar', 'jobnumber')
    keys = {'org_email': 'orgEmail', 'work_place': 'workPlace', 'remark': 'ding_remark', 'dingid': 'dingId',
            'is_admin': 'isAdmin', 'is_boss': 'isBoss', 'is_hide': 'isHide'}

    for k in lowerkeys:
        keys[k] = k
    for k, v in keys.items():
        value = user_info.get(v, None)
        if value is not None:
            setattr(corp_user, k, value)
    corp_user.save_or_update()

    return corp_user


def sync_user(department_id):
    offset = 0
    while True:
        users = client.user.list(department_id)
        for user in users.get('userlist', []):
            offset += 1
            set_corp_user(user)
        if not users.get('hasMore', False):
            return


def sync_corp():
    department_ids = get_department_ids()
    for department_id in department_ids:
        sync_user(department_id)
