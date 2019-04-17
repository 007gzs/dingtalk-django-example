#! /usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from core import serializer
from . import models


class CorpSerializer(serializer.BaseSerializer):

    class Meta:
        model = models.Corp
        fields = ('id', 'corpid', 'status', 'corp_name', 'invite_code', 'industry', 'license_code',
                  'auth_channel', 'auth_channel_type', 'is_authenticated', 'auth_level', 'invite_url', 'corp_logo_url')


class UserSerializer(serializer.BaseSerializer):

    class Meta:
        model = models.User
        fields = ('id', 'dingid', 'name', 'active', 'avatar', 'last_deviceid')


class CorpUserSerializer(serializer.BaseSerializer):
    user = UserSerializer(many=False, read_only=True)
    corp = CorpSerializer(many=False, read_only=True)

    class Meta:
        model = models.CorpUser
        fields = ('id', 'userid', 'openid', 'unionid', 'is_admin', 'is_senior', 'is_boss',
                  'position', 'hired_date', 'jobnumber', 'state_code', 'corp', 'user')
