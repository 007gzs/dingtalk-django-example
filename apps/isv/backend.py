#! /usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals

from core import constants
from .models import CorpUser


class ISVBackend(object):

    def authenticate(self, isv_corp_user_id, **kwargs):
        if isv_corp_user_id is None:
            return None
        user = CorpUser.get_obj_by_pk_from_cache(isv_corp_user_id)
        if user and self.user_can_authenticate(user):
            return user

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        delete_status = getattr(user, 'delete_status', None)
        return delete_status == constants.DELETE_CODE.NORMAL.code or delete_status is None

    def get_user(self, corp_user_id):
        user = CorpUser.get_obj_by_pk_from_cache(corp_user_id)
        return user if self.user_can_authenticate(user) else None
