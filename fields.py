# -*- coding:utf-8 -*-

from django.db.models import OneToOneField
from django.db.models.fields.related import SingleRelatedObjectDescriptor 

class AutoSingleRelatedObjectDescriptor(SingleRelatedObjectDescriptor): # this line just can't be too long, right?
  def __get__(self, instance, instance_type=None):
    try:
      return super(AutoSingleRelatedObjectDescriptor, self).__get__(instance, instance_type)
    except self.related.model.DoesNotExist:
      obj = self.related.model(**{self.related.field.name: instance})
      obj.save()
      return obj

class AutoOneToOneField(OneToOneField):
  '''
  OneToOneField, которое создает зависимый объект при первом обращении
  из родительского, если он еще не создан.
  '''
  def contribute_to_related_class(self, cls, related):
    setattr(cls, related.get_accessor_name(), AutoSingleRelatedObjectDescriptor(related))
    if not cls._meta.one_to_one_field:
      cls._meta.one_to_one_field = self