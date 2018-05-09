# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from core import admin
from . import models


admin.site_register(models.Suite, exclude_list_display=['suite_secret', 'token', 'aes_key'],
                    change_view_readonly_fields=['suite_key', ])
admin.site_register(models.Agent, list_filter=['agent_type', ], list_display=['suite', ])
admin.site_register(models.CorpAgent, addable=False, editable=False, list_display=['agent', 'corp'])
admin.site_register(models.Corp, addable=False, editable=False, list_filter=['status', 'suite', ],
                    exclude_list_display=['permanent_code', 'ch_permanent_code'])
admin.site_register(models.User, addable=False, editable=False)
admin.site_register(models.CorpUser, addable=False, editable=False,
                    list_filter=['corp', ], list_display=['corp', 'user'])
