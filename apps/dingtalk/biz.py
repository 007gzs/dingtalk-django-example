# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import redis
from dingtalk.storage.kvstorage import KvStorage
from django.conf import settings
from dingtalk.client import isv


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
