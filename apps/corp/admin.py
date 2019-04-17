# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from core import admin
from . import models


admin.site_register(models.User, addable=False, editable=False, exclude_list_display=['dingid', 'userid'])
