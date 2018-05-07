# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from core import admin
from . import models


admin.site_register(models.Suite, exclude_list_display=['suite_secret', 'token', 'aes_key'],
                    change_view_readonly_fields=['suite_key', ])
admin.site_register(models.Corp, addable=False, editable_fields=[], list_filter=['status', 'suite', ],
                    exclude_list_display=['permanent_code', 'ch_permanent_code'])
