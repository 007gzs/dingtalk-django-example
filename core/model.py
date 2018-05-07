# encoding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db.models.fields import reverse_related

from apiview import model, admintools
from django.db import models

from example.celery import async_call
from . import constants


class DeletedManager(models.Manager):

    def get_queryset(self):
        queryset = super(DeletedManager, self).get_queryset()
        return queryset.filter(delete_status=constants.DELETE_CODE.NORMAL.code)

    def get_all_queryset(self):
        return super(DeletedManager, self).get_queryset()


class BaseModel(model.BaseModel):
    id = models.BigAutoField('主键ID', primary_key=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, db_index=True, editable=False)
    modify_time = models.DateTimeField('修改时间', auto_now=True, db_index=True, editable=False)
    delete_status = models.BooleanField('删除状态', choices=constants.DELETE_CODE.get_list(),
                                        default=constants.DELETE_CODE.NORMAL.code, null=False, db_index=True)
    remark = models.TextField('备注说明', null=True, blank=True, default='')

    default_manager = models.Manager()
    objects = DeletedManager()

    def __str__(self):
        if hasattr(self, 'name'):
            return self.name
        else:
            return super(BaseModel, self).__str__()

    class Meta:
        abstract = True

    @classmethod
    def ex_search_fields(cls):
        ret = set()
        for field in cls._meta.fields:
            if not field.db_index and not field.unique \
                    and field.name == 'name' and isinstance(field, models.CharField):
                ret.add(field.name)
        return ret

    @classmethod
    def search_fields(cls):
        ret = super(BaseModel, cls).search_fields()
        return ret.union(cls.ex_search_fields())

    def delete(self, using=None, keep_parents=False):
        self.delete_status = constants.DELETE_CODE.DELETED.code
        return super(BaseModel, self).delete(using=using, keep_parents=keep_parents)

    def save_or_update(self):
        if self.pk is None:
            self.save(force_insert=True)
        else:
            self.save_changed()


class ManyToManyRel(reverse_related.ForeignObjectRel):
    def __init__(self, field, to, related_name=None, related_query_name=None,
                 limit_choices_to=None, symmetrical=True, through=None,
                 through_fields=None, db_constraint=False):
        super(ManyToManyRel, self).__init__(
            field, to,
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
        )

        self.through = through

        if through_fields and not through:
            raise ValueError("Cannot specify through_fields without a through model")
        self.through_fields = through_fields

        self.symmetrical = symmetrical
        self.db_constraint = db_constraint

    def get_related_field(self):
        opts = self.through._meta
        field = None
        if self.through_fields:
            field = opts.get_field(self.through_fields[0])
        else:
            for field in opts.fields:
                rel = getattr(field, 'remote_field', None)
                if rel and rel.model == self.model:
                    break
        if field is None:
            return None
        else:
            return field.foreign_related_fields[0]


class ManyToManyField(models.ManyToManyField):

    rel_class = ManyToManyRel

    def __init__(self, to, related_name=None, related_query_name=None, limit_choices_to=None, symmetrical=None,
                 through=None, through_fields=None, db_constraint=False, db_table=None, swappable=True, **kwargs):
        super(ManyToManyField, self).__init__(to, related_name, related_query_name, limit_choices_to, symmetrical,
                                              through, through_fields, db_constraint, db_table, swappable, **kwargs)


class ForeignKey(models.ForeignKey):
    def __init__(self, to, on_delete=models.DO_NOTHING, related_name=None, related_query_name=None,
                 limit_choices_to=None, parent_link=False, to_field=None, db_constraint=False,  **kwargs):
        super(ForeignKey, self).__init__(to, on_delete, related_name, related_query_name, limit_choices_to,
                                         parent_link, to_field, db_constraint, **kwargs)


class OneToOneField(models.OneToOneField):
    def __init__(self, to, on_delete=models.DO_NOTHING, to_field=None, db_constraint=False, **kwargs):
        super(OneToOneField, self).__init__(to, on_delete, to_field, db_constraint=db_constraint, **kwargs)


class ExportMixin(admintools.ExportMixin):

    def async_export_data(self, func, *args, **kwargs):
        async_call(func, *args, **kwargs)


class ImportExportMixin(admintools.ImportExportMixin):

    def async_export_data(self, func, *args, **kwargs):
        async_call(func, *args, **kwargs)
