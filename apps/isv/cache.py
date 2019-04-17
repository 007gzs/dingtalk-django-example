# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview import cache


class CorpAgentCache(cache.BaseCacheItem):
    _prefix = 'corp_agent'
