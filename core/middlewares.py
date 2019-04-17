# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import time
import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("httpinfo")


class AccessControlAllowOriginMiddleware(MiddlewareMixin):

    @classmethod
    def process_request(cls, request):
        try:
            start = time.time()
            request.start = start
        except Exception as e:
            logging.error(e)

    @classmethod
    def process_response(cls, request, response):
        if request.META.get('HTTP_ORIGIN'):
            response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
            response['Access-Control-Allow-Credentials'] = 'true'
        # setattr(response, 'Access-Control-Allow-Origin', "*")
        response['X-Frame-Options'] = 'ALLOW-FROM *.007.pub'

        from rest_framework.request import Request

        try:
            if isinstance(request, Request):
                request = request._request
            end = time.time()
            exectime = end - request.start

            logger.info("stat exectime: time: %fs  path:%s  querystring:%s" % (
                         exectime, request.path, request.META['QUERY_STRING']))

        except Exception as e:
            logging.error(e)

        return response
