# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.model import AbstractUserMixin
from django.db import models

from core import model


class User(AbstractUserMixin, model.BaseModel):
    dingid = models.CharField('钉钉Id', max_length=128, null=False, blank=False, default='', unique=True)
    userid = models.CharField('员工唯一标识ID', max_length=128, null=False, blank=False, default='', unique=True)
    name = models.CharField('成员名称', max_length=128, null=False, blank=False, default='')
    mobile = models.CharField('手机号码', max_length=64, null=False, blank=False, default='', db_index=True)
    tel = models.CharField('分机号', max_length=64, null=False, blank=False, default='', db_index=True)
    avatar = models.ImageField('头像url', max_length=1024, null=False, blank=False, default='')
    work_place = models.CharField('办公地点', max_length=128, null=False, blank=False, default='')
    ding_remark = models.CharField('备注', max_length=1024, null=False, blank=False, default='')
    email = models.CharField('员工的电子邮箱', max_length=128, null=False, blank=False, default='')
    org_email = models.CharField('员工的企业邮箱', max_length=128, null=False, blank=False, default='')
    active = models.BooleanField('是否已经激活', null=False, blank=False, default=False)
    is_admin = models.BooleanField('是否为企业的管理员', null=False, blank=False, default=False)
    is_boss = models.BooleanField('是否为企业的老板', null=False, blank=False, default=False)
    is_hide = models.BooleanField('是否号码隐藏', null=False, blank=False, default=False)
    position = models.CharField('职位信息', max_length=128, null=False, blank=False, default='')
    hired_date = models.DateTimeField('入职时间', null=True, default=None)
    jobnumber = models.CharField('员工工号', max_length=128, null=False, blank=False, default='', db_index=True)

    class Meta:
        verbose_name = verbose_name_plural = '用户信息'
