#
# dcolumn/dcolumns/admin.py
#

"""
Dynamic Column model admin.
"""
__docformat__ = "restructuredtext en"

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from dcolumn.common.admin_mixins import UserAdminMixin

from .models import DynamicColumn, ColumnCollection, KeyValue
from .forms import DynamicColumnForm, ColumnCollectionForm, KeyValueForm


#
# KeyValue
#
class KeyValueInline(admin.TabularInline):
    """
    Admin inline used in an admin class who's model inherits from
    ``CollectionBase``.
    """
    fieldsets = (
        (None, {'fields': ('dynamic_column', 'value',)}),
        )
    ordering = ('dynamic_column__location', 'dynamic_column__order',)
    extra = 0
    model = KeyValue
    form = KeyValueForm

    class Media:
        js = ('dcolumn/js/js.cookie-2.0.4.min.js',
              'dcolumn/js/inheritance.js',
              'dcolumn/js/dynamic-column.js',)


#
# ColumnCollection
#
class ColumnCollectionAdmin(UserAdminMixin):
    """
    Used internally to DColumn for the ``ColumnCollection`` model.
    """
    fieldsets = (
        (None, {'fields': ('name', 'related_model', 'dynamic_column',)}),
        (_('Status'), {'classes': ('collapse',),
                       'fields': ('active', 'creator', 'created', 'updater',
                                  'updated',)}),
        )
    readonly_fields = ('creator', 'created', 'updater', 'updated',)
    list_display = ('name', 'related_model', 'updater_producer', 'updated',)
    filter_horizontal = ('dynamic_column',)
    form = ColumnCollectionForm

    class Media:
        js = ('dcolumn/js/inheritance.js',
              'dcolumn/js/column-collection.js',)
        css = {'all': ('dcolumn/css/column-collection.css',)}


#
# DynamicColumn
#
class DynamicColumnAdmin(UserAdminMixin):
    """
    Used internally to DColumn for the ``DynamicColumn`` model.
    """
    fieldsets = (
        (None, {'fields': ('name', 'value_type', 'relation',
                           'store_relation',)}),
        (_('Screen Location'), {'fields': ('location', 'order', 'required',)}),
        (_('Status'), {'classes': ('collapse',),
                       'fields': ('preferred_slug', 'slug', 'active',
                                  'creator', 'created', 'updater',
                                  'updated',)}),
        )
    readonly_fields = ('creator', 'slug', 'updater', 'created', 'updated',)
    list_display = ('name', '_collection_producer', 'slug', 'value_type',
                    '_relation_producer', 'store_relation', 'required',
                    'location', 'order', 'updated', 'active',)
    list_editable = ('location', 'order', 'active',)
    ordering = ('column_collection__name', 'location', 'order', 'name',)
    form = DynamicColumnForm


admin.site.register(ColumnCollection, ColumnCollectionAdmin)
admin.site.register(DynamicColumn, DynamicColumnAdmin)
