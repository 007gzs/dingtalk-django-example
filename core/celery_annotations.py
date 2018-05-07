# encoding: utf-8
from __future__ import absolute_import, unicode_literals

import logging


def on_bound(*args, **kwargs):
    logging.info("celery on_bound %s %s", args, kwargs)


def on_failure(task, exc, task_id, args, kwargs, einfo):
    logging.info("celery on_failure %s %s", (task, exc, task_id, args, kwargs, einfo), {}, exc_info=exc)


def on_retry(*args, **kwargs):
    logging.info("celery on_retry %s %s", args, kwargs)


def on_success(*args, **kwargs):
    logging.info("celery on_success %s %s", args, kwargs)


def after_return(*args, **kwargs):
    logging.info("celery after_return %s %s", args, kwargs)


celery_annotations_dict = {'on_failure': on_failure,
                           'on_retry': on_retry,
                           'on_success': on_success,
                           'after_return': after_return,
                           }
