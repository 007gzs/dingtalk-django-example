#! /usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.code import Code

CORP_AUTH_LEVEL_CODE = Code((
    ('NO',              0,  '未认证'),
    ('HIGH',            1,  '高级认证'),
    ('MID',             2,  '中级认证'),
    ('LOW',             3,  '初级认证'),
))

CORP_STSTUS_CODE = Code((
    ('NO',              0,  '未授权'),
    ('AUTH',            10, '已授权,未激活'),
    ('ACTIVE',          20, '已激活'),
))

AGENT_CLOSE_CODE = Code((
    ('FORBIDDEN',       0,  '禁用'),
    ('NORMAL',          1,  '正常'),
    ('NEED_ACTIVE',     2,  '待激活'),
))

AGENT_TYPE_CODE = Code((
    ('UNKNOWN',         0,  '未知'),
    ('MICRO',           10, '微应用'),
    ('CHANNEL',         20, '服务窗'),
))
