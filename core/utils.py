# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import hashlib
import tempfile

import os

from apiview import common_view
from apiview.err_code import ErrCode
from apiview.views import fields
from django.utils.encoding import force_bytes
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import StaticHTMLRenderer
from rest_framework.response import Response

from core.view import APIBase, TextApiView, HtmlApiView, AdminApi


def get_temp_file(content):
    content = force_bytes(content)
    m = hashlib.md5()
    m.update(content)
    filename = "%s.tmp" % m.hexdigest()
    filename = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            f.write(content)
    return filename


@api_view(["GET"])
@renderer_classes((StaticHTMLRenderer,))
def generate_api_js(request):
    # api.js?package_name=bbapi.views&ext_params=referral_code,version,device_id,channel
    tags = ErrCode.get_tags()
    content = "import request from '@/utils/request'\n\n"
    content += "// export var server = '%s'; //服务地址\n\n" % request.build_absolute_uri("/")[:-1]
    content += 'export var ERROR_CODE = {\n'
    last = ''
    for tag in tags:
        code_data = getattr(ErrCode, tag)
        content += '  %s: %d, // %s\n' % (tag, code_data.code, code_data.message)
        last = ', // %s\n' % code_data.message
    if last:
        content = content[:-len(last)] + last[1:]
    content += '}\n'
    ext_params_str = request.GET.get("ext_params", None)
    if ext_params_str is not None:
        ext_params = set(ext_params_str.split(','))
    else:
        ext_params = set([k for k, v in APIBase.Meta.param_fields])
    views = common_view.get_view_list()
    for v in views:
        if issubclass(v['viewclass'], (TextApiView, HtmlApiView, AdminApi)):
            continue
        func_name = v['url'].replace('/', '_').strip('_')
        str_args = ''
        str_data = '\n'
        hasfile = False
        post = False
        length = 0
        count = 0
        for param, field in v['params'].items():
            if isinstance(field, (fields.FileField, fields.ImageField)):
                hasfile = True
                post = True
            if param in ext_params:
                continue
            if param == 'password':
                post = True
            if isinstance(field, fields.CharField):
                if field.max_length is None:
                    count += 1
                else:
                    length += field.max_length
            if str_args == '':
                str_args = param
            else:
                str_args += ', %s' % param
            str_data += "      %s: %s,\n" % (param, param)
        content_type = 'multipart/form-data' if hasfile else 'application/x-www-form-urlencoded'
        str_data = str_data[:-2]
        if len(str_data) > 1:
            str_data += "\n    "
        if count > 3 or length > 200:
            post = True
        content += '''
// %s
export function %s(%s) {
  return request({
    url: '%s',
    method: '%s',
    data: {%s},
    headers: { 'Content-Type': '%s' }
  })
}
''' % (v['name'], func_name, str_args, v['url'], 'POST' if post else 'GET', str_data, content_type)
    content += '\n'
    return Response(content.encode("utf8"), content_type='text/plain;charset=utf-8')
