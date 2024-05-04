# -*- coding: utf-8 -*-
#
# dcolumn/dcolumns/tests/base_tests.py
#

from datetime import datetime, timezone, date as dt_date, time as dt_time
import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from example_site.books.models import Author, Book, Publisher, Promotion
from dcolumn.dcolumns.manager import DynamicColumnManager

from ..models import DynamicColumn, ColumnCollection, KeyValue

User = get_user_model()


class BaseDcolumns(object):
    _TEST_USERNAME = 'TestUser'
    _TEST_PASSWORD = 'TestPassword_007'

    def __init__(self, name):
        super().__init__(name)
        self.user = None
        self.manager = DynamicColumnManager()
        self.choice2index = dict(
            [(v, k) for k, v in self.manager.choice_relations])

    def setUp(self):
        self.user = self._create_user()

    def tearDown(self):
        self.user = None

    def _create_user(self, username=_TEST_USERNAME, email=None,
                     password=_TEST_PASSWORD, is_superuser=True):
        user = User.objects.create_user(username=username, password=password)
        user.first_name = "Test"
        user.last_name = "User"
        user.is_active = True
        user.is_staff = True
        user.is_superuser = is_superuser
        user.save()
        return user

    def _create_dynamic_column_record(
        self, name, value_type, location, order, preferred_slug=None,
        relation=None, required=DynamicColumn.NO, active=True,
        store_relation=DynamicColumn.NO):
        kwargs = {}
        kwargs['name'] = name
        kwargs['value_type'] = value_type
        kwargs['location'] = location
        kwargs['order'] = order
        kwargs['preferred_slug'] = preferred_slug
        kwargs['relation'] = relation
        kwargs['required'] = required
        kwargs['store_relation'] = store_relation
        kwargs['active'] = active
        kwargs['creator'] = self.user
        kwargs['updater'] = self.user
        return DynamicColumn.objects.create(**kwargs)

    def _create_column_collection_record(self, name, related_model,
                                         dynamic_columns=[], active=True):
        kwargs = {}
        kwargs['name'] = name
        kwargs['related_model'] = related_model
        kwargs['active'] = active
        kwargs['creator'] = self.user
        kwargs['updater'] = self.user
        obj = ColumnCollection.objects.create(**kwargs)
        obj.process_dynamic_columns(dynamic_columns)
        return obj

    def _create_dcolumn_record(self, model, collection, **kwargs):
        kwargs['creator'] = self.user
        kwargs['updater'] = self.user
        return model.objects.create(column_collection=collection, **kwargs)

    def _create_key_value_record(self, collection, dynamic_column, value):
        kwargs = {}
        kwargs['value'] = value
        obj, created = KeyValue.objects.get_or_create(
            collection=collection, dynamic_column=dynamic_column,
            defaults=kwargs)

        if not created:
            obj.value = value
            obj.save()

        return obj

    def _create_author_objects(self, name='Pickup Andropoff', extra_dcs=[],
                               required=DynamicColumn.NO):
        """
        Create  a set of Author objects.
        """
        dcs = extra_dcs
        dc0 = self._create_dynamic_column_record(
            "Web Site", DynamicColumn.TEXT, 'author_top', 1, required=required)
        dcs.append(dc0)
        # Add to a collection.
        cc = self._create_column_collection_record(
            "Author Current", 'author', dynamic_columns=dcs)
        # Create a author entry.
        author = self._create_dcolumn_record(
            Author, cc, name=name)
        value = "example.org"
        dc0_slug = 'web_site'
        author.set_key_value(dc0_slug, value)
        return author, cc, {dc0.slug: author.get_key_value(dc0_slug)}

    def _create_publisher_objects(self, name='Some big Publisher',
                                  extra_dcs=[], required=DynamicColumn.NO):
        """
        Create  a set of Publisher objects.
        """
        dcs = extra_dcs
        dc0 = self._create_dynamic_column_record(
            "Web Site", DynamicColumn.TEXT, 'publisher_top', 1,
            required=required)
        dcs.append(dc0)
        # Add to a collection.
        cc = self._create_column_collection_record(
            "Publisher Current", 'publisher', dynamic_columns=dcs)
        # Create a publisher entry.
        publisher = self._create_dcolumn_record(
            Publisher, cc, name=name)
        value = "example.org"
        dc0_slug = 'web_site'
        publisher.set_key_value(dc0_slug, value)
        return publisher, cc, {dc0.slug: publisher.get_key_value(dc0_slug)}

    def _create_promotion_objects(self, name="50% off everything forever.",
                                  extra_dcs=[], required=[
                                      DynamicColumn.NO, DynamicColumn.NO,
                                      DynamicColumn.NO]):
        """
        Create  a set of Promotion objects.
        """
        dcs = extra_dcs
        # Create promotion description
        dc0 = self._create_dynamic_column_record(
            "Description", DynamicColumn.TEXT, 'promotion_top', 1,
            required=required[0])
        dcs.append(dc0)
        # Create promotion start date.
        dc1 = self._create_dynamic_column_record(
            "Start Date", DynamicColumn.DATE, 'promotion_top', 2,
            required=required[1])
        dcs.append(dc1)
        # Create promotion start time.
        dc2 = self._create_dynamic_column_record(
            "Start Time", DynamicColumn.TIME, 'promotion_top', 3,
            required=required[2])
        dcs.append(dc2)
        # Add to a collection.
        cc = self._create_column_collection_record(
            "Promotion Current", 'promotion', dynamic_columns=dcs)
        # Create a book entry.
        promotion = self._create_dcolumn_record(
            Promotion, cc, name=name)
        value = "Everything sale."
        dc0_slug = 'description'
        promotion.set_key_value(dc0_slug, value)
        value = dt_date.today()
        dc1_slug = 'start_date'
        promotion.set_key_value(dc1_slug, value)
        dt = datetime.now(timezone.utc)
        value = dt_time(hour=dt.hour, minute=dt.minute, second=dt.second,
                        microsecond=dt.microsecond, tzinfo=dt.tzinfo)
        dc2_slug = 'start_time'
        promotion.set_key_value(dc2_slug, value)
        return promotion, cc, {dc0.slug: promotion.get_key_value(dc0_slug),
                               dc1.slug: promotion.get_key_value(dc1_slug),
                               dc2.slug: promotion.get_key_value(dc2_slug)}

    def _create_book_objects(self, title='Test Book', author=None,
                             publisher=None, promotion=None, language=None,
                             extra_dcs=[], required=DynamicColumn.NO):
        """
        Create  a set of Book objects.
        """
        dcs = extra_dcs
        dc0 = self._create_dynamic_column_record(
            "Abstract", DynamicColumn.TEXT_BLOCK, 'book_top', 1,
            required=required)
        dcs.append(dc0)

        if author: # Database table
            dc1 = self._create_dynamic_column_record(
                "Author", DynamicColumn.CHOICE, 'book_top', 2,
                relation=self.choice2index.get("Author"))
            dcs.append(dc1)

        if publisher: # Database table
            dc2 = self._create_dynamic_column_record(
                "Publisher", DynamicColumn.CHOICE, 'book_top', 3,
                relation=self.choice2index.get("Publisher"))
            dcs.append(dc2)

        if promotion: # Database table
            dc3 = self._create_dynamic_column_record(
                "Promotion", DynamicColumn.CHOICE, 'book_top', 4,
                relation=self.choice2index.get("Promotion"),
                store_relation=DynamicColumn.YES)
            dcs.append(dc3)

        if language: # Choice object
            dc4 =self._create_dynamic_column_record(
                "Language", DynamicColumn.CHOICE, 'book_top', 5,
                relation=self.choice2index.get("Language"))
            dcs.append(dc4)

        # Add to a collection.
        cc = self._create_column_collection_record(
            "Book Current", 'book', dynamic_columns=dcs)
        # Create a book entry.
        book = self._create_dcolumn_record(Book, cc, title=title)
        value = "Very very short abstract."
        dc0_slug = 'abstract'
        book.set_key_value(dc0_slug, value)
        values = {dc0.slug: book.get_key_value(dc0_slug)}

        if author:
            dc1_slug = 'author'
            book.set_key_value(dc1_slug, author)
            values[dc1.slug] = author.pk

        if publisher:
            dc2_slug = 'publisher'
            book.set_key_value(dc2_slug, publisher)
            values[dc2.slug] = publisher.pk

        if promotion:
            dc3_slug = 'promotion'
            book.set_key_value(dc3_slug, promotion)
            # store_relation not PK
            values[dc3.slug] = book.get_key_value(dc3_slug)

        if language:
            dc4_slug = 'language'
            book.set_key_value(dc4_slug, language)
            values[dc4.slug] = language.pk

        return book, cc, values

    def _has_error(self, response, message=None, error_key=None):
        result = False

        if (error_key and hasattr(response, 'data')
              and response.data.get(error_key)):
            result = True
        elif (hasattr(response, 'context_data')
            and response.context_data.get('form')
            and response.context_data.get('form').errors):
            result = True
        elif (message and hasattr(response, '__str__')
              and message in str(response)):
            result = True

        return result

    def _test_errors(self, response, tests={}, exclude_keys=[]):
        if (hasattr(response, 'context_data') and
            response.context_data.get('form')):
            errors = dict(response.context_data.get('form').errors)
            self._find_tests(errors, tests, exclude_keys, is_context_data=True)
        elif hasattr(response, 'data'):
            errors = response.data
            self._find_tests(errors, tests, exclude_keys)
        elif hasattr(response, 'content'):
            errors = json.loads(response.content.decode('utf-8'))
            self._find_tests(errors, tests, exclude_keys)
        elif isinstance(response, (dict, Mapping)): # Embedded errors
            errors = response
            self._find_tests(errors, tests, exclude_keys)
        else:
            msg = "No data found."
            self.assertTrue(False, msg)

        msg = "Unaccounted for errors: {}".format(errors)
        self.assertFalse(len(errors) != 0 and True or False, msg)

    def _find_tests(self, errors, tests, exclude_keys, is_context_data=False):
        msg = "All errors: {}".format(errors)

        for key, value in tests.items():
            if key in exclude_keys:
                errors.pop(key, None)
                continue

            err_msg = errors.pop(key, None)
            self.assertTrue(
                err_msg, "Could not find key: {}. {}".format(key, msg))

            if is_context_data:
                err_msg = err_msg.as_text()
            else:
                msg = "More than one error for key '{}', error: {}".format(
                    key, err_msg)
                self.assertTrue(len(err_msg), msg)

            msg = "For key '{}', value '{}' not found in '{}'".format(
                key, value, err_msg)

            if not is_context_data:
                if isinstance(err_msg, (list, tuple)):
                    err_msg = err_msg[0]
                elif isinstance(err_msg, dict):
                    err_msg = err_msg.get(key)

            self.assertTrue(value and value in err_msg, msg)
