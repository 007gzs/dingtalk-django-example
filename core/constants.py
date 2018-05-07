# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.code import Code

DELETE_CODE = Code((
    ('NORMAL',  0, '正常'),
    ('DELETED', 1, '已经删除'),
))
