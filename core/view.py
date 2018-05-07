# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from apiview.err_code import ErrCode
from apiview.exceptions import CustomError

from django.contrib.auth import models as auth_models
from rest_framework.response import Response

from apiview import view, utility
from apiview.views import fields

from . import renderers


class APIBase(view.APIView):

    def get_context(self, request, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def get_req_body(request):
        return request.body if request.method == 'POST' else None

    class Meta:
        path = '/'
        param_fields = (
            ('channel', fields.CharField(help_text='App Channel', required=False)),
            ('version', fields.CharField(help_text='App Version', required=False)),
        )


class AdminApi(APIBase):

    need_superuser = True

    def get_context(self, request, *args, **kwargs):
        raise NotImplementedError

    def check_api_permissions(self, request, *args, **kwargs):
        if not isinstance(request.user, auth_models.AbstractUser):
            raise CustomError(ErrCode.ERR_AUTH_NOLOGIN)
        if not request.user.is_active or not request.user.is_staff:
            raise CustomError(ErrCode.ERR_AUTH_PERMISSION)
        if self.need_superuser:
            if not request.user.is_superuser:
                raise CustomError(ErrCode.ERR_AUTH_PERMISSION)

    class Meta:
        path = '/'


class PageMixin(object):
    PAGE_SIZE_MAX = 200
    param_fields = (
        ('page', fields.IntegerField(help_text='页码', required=False, omit=1)),
        ('page_size', fields.IntegerField(help_text='每页条数', required=False, omit=100)),
    )

    def get_page_context(self, request, queryset, serializer_cls):
        page_size = request.params.page_size
        if page_size <= 0 or page_size > self.PAGE_SIZE_MAX:
            raise CustomError(ErrCode.ERR_PAGE_SIZE_ERROR)
        total_data = queryset.count()
        total_page = (total_data + page_size - 1) // page_size
        page = request.params.page
        if page < 1:
            page = 1
        elif page > total_page:
            page = total_page
        start = (page - 1) * page_size
        data = []
        if total_data > 0:
            data = serializer_cls(queryset[start:start+page_size], request=request, many=True).data

        return {'page_size': page_size, 'list': data, 'page': page, 'total_page': total_page, 'total_data': total_data}


class TextApiView(APIBase):

    def __init__(self, *args, **kwargs):
        super(TextApiView, self).__init__(*args, **kwargs)
        self.renderer_classes = (renderers.PlainTextRenderer, )

    def format_res_data(self, context, timestamp=False):
        if isinstance(context, dict):
            if 'code' in context and context['code'] != 0:
                context = 'error: %d %s' % (context['code'], context.get('message', ''))
            else:
                context = utility.format_res_data(context)
        return Response(context)

    def get_context(self, request, *args, **kwargs):
        raise NotImplementedError

    class Meta:
        path = '/'


class HtmlApiView(APIBase):

    def __init__(self, *args, **kwargs):
        super(HtmlApiView, self).__init__(*args, **kwargs)
        self.renderer_classes = (renderers.PlainHtmlRenderer, )

    def get_context(self, request, *args, **kwargs):
        raise NotImplementedError

    def format_res_data(self, context, timestamp=False):
        from django.shortcuts import render_to_response
        if isinstance(context, dict):
            return render_to_response("error.html", context)
        return Response(context)

    class Meta:
        path = '/'
