# -*- coding: utf-8 -*-
#
# dcolumn/dcolumns/tests/test_dcolumns_autodisplay.py
#
# WARNING: These unittests can only be run from within the original test
#          framework from https://github.com/cnobile2012/dcolumn.
#

from datetime import datetime, timezone, time as dt_time
import io

from django.test import TestCase
from django.template import (
    Template, Context, TemplateSyntaxError, VariableDoesNotExist)

from example_site.books.models import Author, Book, Promotion, Publisher
from dcolumn.dcolumns.models import DynamicColumn

from ..views import ContextDataMixin
from .base_tests import BaseDcolumns


class ViewMixinTest(ContextDataMixin):
    model = None
    object = None

    def get_context_data(self, **kwargs):
        """
        This method dummys up the view. Example outputs are listed below.

        ``get_dynamic_column_context_data``::

          {'dynamicColumns': {
           u'author': [(0, 'Choose a value'),
                       (17, u'Jeremy Blum'),
                       (5, u'John Iovine'),
                       (23, u'Lauren Darcey & Shane Conder'),
                       (25, u'Peter Gasston'),
                       (6, u'Rajaram Regupathy'),
                       (7, u'Richard Stones'),
                       (15, u'Ruth Suehle & Tom Callaway'),
                       (8, u'Toby Segaran')],
           u'language': [(0, 'Choose a value'),
                         (1, 'Chinese'),
                         (2, 'English'),
                         (3, 'Portuguese'),
                         (4, 'Russian'),
                         (5, 'Japanese')],
           ...}
          }

        ``get_relation_context_data``::

          OrderedDict([
            (19,
              {'location': 'book-bottom',
               'name': u'Promotion',
               'order': 1,
               'pk': 19,
               'relation': 2,
               'required': False,
               'slug': u'promotion',
               'store_relation': True,
               'value_type': 2}),
            (20,
              {'location': 'book-center',
               'name': u'Language',
               'order': 6,
               'pk': 20,
               'relation': 1,
               'required': False,
               'slug': u'language',
               'store_relation': False,
               'value_type': 2}),
            ...])
        """
        context = {'object': self.object}
        context.update(self.get_dynamic_column_context_data(**kwargs))
        relation = self.get_relation_context_data(obj=self.object, **kwargs)
        pk, slug = kwargs.pop('munge_slug', (None, None))

        if pk and slug:
            # Munge the slug to cause a falure.
            item = relation.get('relations').get(pk)
            item['slug'] = slug

        context.update(relation)
        return context


class TestAutoDisplay(BaseDcolumns, TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def _setup_template(self, model, object=None, prefix=None, options=None,
                        display=None, except_test=False, invalid_kwargs=None,
                        relation_name='relation', munge_slug=(None, None)):
        # Setup the context.
        vmt = ViewMixinTest()
        vmt.model = model
        vmt.object = object
        context = Context(vmt.get_context_data(munge_slug=munge_slug))
        # Run the test.
        buff = io.StringIO()
        buff.write("{% load autodisplay %}")
        buff.write("{% for relation in relations.values %}")
        r = " {}".format(relation_name) if not except_test else ''
        p = " prefix={}".format(prefix) if prefix is not None else ''
        o = " options={}".format(options) if options is not None else ''
        d = " display={}".format(display) if display is not None else ''
        i = invalid_kwargs if invalid_kwargs else ''
        cmd = "{{% auto_display{}{}{}{}{} %}}".format(r, p, o, d, i)
        buff.write(cmd)
        buff.write("{% endfor %}")
        template = buff.getvalue()
        buff.close()
        tr = Template(template)
        return context, tr.render(context)

    def test_arguments(self):
        """
        Test that all the arguments function properly.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        book, b_cc, b_values = self._create_book_objects()
        # Execute the template tag and test.
        context, result = self._setup_template(
            Book, object=book, options='dynamicColumns', display=True,
            prefix='test-')
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('id-test-abstract'), 1, msg)
        # All other arguments combinations are tested elsewhere.

    def test_exceptions_and_errors(self):
        """
        Test that exceptions happen when they are supposed to happen.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        author, a_cc, a_values = self._create_author_objects()
        book, b_cc, b_values = self._create_book_objects(author=author)
        # Test for invalid number of args.
        with self.assertRaises(TemplateSyntaxError) as cm:
            context, result = self._setup_template(Book, except_test=True)
        # Test for invalid keyword.
        with self.assertRaises(TemplateSyntaxError) as cm:
            context, result = self._setup_template(
                Book, invalid_kwargs=" optionX")
        # Test that template.VariableDoesNotExist is raised and relation is
        # set to None.
        context, result = self._setup_template(
            Book, object=book, relation_name='relationX')
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertTrue('Invalid relation object: None' in result, msg)
        # Test 'Invalid option object'.
        author_dc = b_cc.dynamic_column.get(slug='author')
        context, result = self._setup_template(
            Book, object=book, munge_slug=(author_dc.pk, 'authorX'))
        msg = "result: {}, context: {}, values: {}".format(
            result, context, a_values)
        self.assertTrue('Invalid option object: None' in result, msg)
        # Test 'Invalid key for relation'.
        author_dc = b_cc.dynamic_column.get(slug='author')
        with self.assertRaises(TemplateSyntaxError) as cm:
            context, result = self._setup_template(
                Book, object=book, options='dynamicColumns',
                munge_slug=(author_dc.pk, 'authorX'))

    def test_BOOLEAN_display(self):
        """
        Test that the BOOLEAN type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Ignore", DynamicColumn.BOOLEAN, 'book_top', 1)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = 'FALSE'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertTrue("No" in result, msg)
        # Same test, but change the value to 0.
        value = '0'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        context, result = self._setup_template(Book, object=book, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertTrue("No" in result, msg)
        # Same test, but change the value to true.
        value = 'TrUe'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        context, result = self._setup_template(Book, object=book, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertTrue("Yes" in result, msg)
        # Same test, but change the value to non 0.
        value = '100'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        context, result = self._setup_template(Book, object=book, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertTrue("Yes" in result, msg)

    def test_BOOLEAN_entry(self):
        """
        Test that the BOOLEAN type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Ignore", DynamicColumn.BOOLEAN, 'book_top', 1)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        # Execute the template tag and test.
        context, result = self._setup_template(Book)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('option'), 4, msg)
        self.assertTrue("No" in result, msg)
        self.assertTrue("Yes" in result, msg)

    def test_CHOICE_display(self):
        """
        Test that the CHOICE type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        author, a_cc, a_values = self._create_author_objects()
        book, b_cc, b_values = self._create_book_objects(author=author)
        # Execute the template tag and test.
        context, result = self._setup_template(
            Book, object=book, options='dynamicColumns', display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        value = book.get_key_value('author')
        self.assertTrue(value in result, msg)
        # Test that partial dynamicColumns work properly.
        context, result = self._setup_template(
            Book, object=book, options='dynamicColumns.author', display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        value = book.get_key_value('author')
        self.assertTrue(value in result, msg)

    def test_CHOICE_entry(self):
        """
        Test that the CHOICE type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        author, a_cc, a_values = self._create_author_objects()
        book, b_cc, b_values = self._create_book_objects(author=author)
        # Execute the template tag and test.
        context, result = self._setup_template(
            Book, options='dynamicColumns')
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('option'), 4, msg)
        self.assertTrue("Choose a value" in result, msg)
        value = book.get_key_value('author')
        self.assertTrue(value in result, msg)

    def test_CHOICE_store_realtion_display(self):
        """
        Test that the CHOICE type with store_relation set True display HTML is
        corrent.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        promotion, p_cc, p_values = self._create_promotion_objects()
        book, b_cc, b_values = self._create_book_objects(promotion=promotion)
        # Execute the template tag and test.
        context, result = self._setup_template(
            Book, object=book, options='dynamicColumns', display=True)
        msg = "result: {}, context: {}, b_values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        value = book.get_key_value('promotion')
        self.assertTrue(value in result, msg)

    def test_CHOICE_store_relation_display_value_zero(self):
        """
        Test that the CHOICE type with store_relation set True fails when
        the value is zero.
        """
        dc0 = self._create_dynamic_column_record(
            "Promotion", DynamicColumn.CHOICE, 'book_top', 4,
            relation=self.choice2index.get("Promotion"),
            store_relation=DynamicColumn.YES, required=DynamicColumn.YES)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = 0
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(
            Book, object=book, options='dynamicColumns', display=True)
        msg = "result: {}, context: {}, b_values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertFalse(">0<" in result, msg)

    def test_CHOICE_store_relation_entry(self):
        """
        Test that the CHOICE type with store_relation set True entry HTML is
        corrent.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        promotion, p_cc, p_values = self._create_promotion_objects()
        book, b_cc, b_values = self._create_book_objects(promotion=promotion)
        # Execute the template tag and test.
        context, result = self._setup_template(
            Book, object=book, options='dynamicColumns')
        msg = "result: {}, context: {}, b_values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('option'), 4, msg)
        self.assertTrue("Choose a value" in result, msg)
        value = book.get_key_value('promotion')
        self.assertTrue(value in result, msg)

    def test_DATE_display(self):
        """
        Test that the DATE type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        promotion, p_cc, p_values = self._create_promotion_objects()
        # Execute the template tag and test.
        context, result = self._setup_template(
            Promotion, object=promotion, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, p_values)
        self.assertEqual(result.count('<span'), len(p_values), msg)
        value = promotion.get_key_value('start_date').isoformat()
        self.assertTrue(value in result, msg)

    def test_DATE_entry(self):
        """
        Test that the DATE type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        promotion, p_cc, p_values = self._create_promotion_objects()
        # Execute the template tag and test.
        context, result = self._setup_template(Promotion, object=promotion)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, p_values)
        self.assertEqual(result.count('input'), 3, msg)
        value = promotion.get_key_value('start_date').isoformat()
        self.assertTrue(value in result, msg)

    def test_DATETIME_display(self):
        """
        Test that the DATETIME type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Date & Time", DynamicColumn.DATETIME, 'promotion_top', 6)
        promotion, p_cc, p_values = self._create_promotion_objects(
            extra_dcs=[dc0])
        value = datetime.now(timezone.utc).isoformat().replace('T', ' ')
        kv0 = self._create_key_value_record(promotion, dc0, value)
        p_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(
            Promotion, object=promotion, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, p_values)
        self.assertEqual(result.count('<span'), len(p_values), msg)
        self.assertTrue(value in result, msg)

    def test_DATETIME_entry(self):
        """
        Test that the DATETIME type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Date & Time", DynamicColumn.DATETIME, 'promotion_top', 6)
        promotion, p_cc, p_values = self._create_promotion_objects(
            extra_dcs=[dc0])
        value = datetime.now(timezone.utc).isoformat().replace('T', ' ')
        kv0 = self._create_key_value_record(promotion, dc0, value)
        p_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Promotion, object=promotion)
        msg = "result: {}, context: {}, values: {}, value: {}".format(
            result, context, p_values, value)
        self.assertEqual(result.count('input'), 4, msg)
        self.assertTrue(value in result, msg)

    def test_TIME_display(self):
        """
        Test that the TIME type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        promotion, p_cc, p_values = self._create_promotion_objects()
        # Execute the template tag and test.
        context, result = self._setup_template(
            Promotion, object=promotion, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, p_values)
        self.assertEqual(result.count('<span'), len(p_values), msg)
        value = promotion.get_key_value('start_time').isoformat()
        self.assertTrue(value in result, msg)

    def test_TIME_entry(self):
        """
        Test that the TIME type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        promotion, p_cc, p_values = self._create_promotion_objects()
        # Execute the template tag and test.
        context, result = self._setup_template(Promotion, object=promotion)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, p_values)
        self.assertEqual(result.count('input'), 3, msg)
        value = promotion.get_key_value('start_time').isoformat()
        self.assertTrue(value in result, msg)

    def test_FLOAT_display(self):
        """
        Test that the FLOAT type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "percentage", DynamicColumn.FLOAT, 'book_top', 6)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = '10.9'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertTrue(value in result, msg)

    def test_FLOAT_entry(self):
        """
        Test that the FLOAT type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "percentage", DynamicColumn.FLOAT, 'book_top', 6)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = '10.9'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('input'), 1, msg)
        self.assertTrue(value in result, msg)

    def test_NUMBER_display(self):
        """
        Test that the NUMBER type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "percentage", DynamicColumn.NUMBER, 'book_top', 6)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = '1000'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertTrue(value in result, msg)

    def test_NUMBER_entry(self):
        """
        Test that the NUMBER type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "percentage", DynamicColumn.NUMBER, 'book_top', 6)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = '1000'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('input'), 1, msg)
        self.assertTrue(value in result, msg)

    def test_TEXT_display(self):
        """
        Test that the TEXT type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "percentage", DynamicColumn.TEXT, 'book_top', 6)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = 'Something to say.'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertTrue(value in result, msg)

    def test_TEXT_entry(self):
        """
        Test that the TEXT type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "percentage", DynamicColumn.TEXT, 'book_top', 6)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = 'Something to say.'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('input'), 1, msg)
        self.assertTrue(value in result, msg)

    def test_TEXT_BLOCK_display(self):
        """
        Test that the TEXT_BLOCK type display HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "percentage", DynamicColumn.TEXT_BLOCK, 'book_top', 6)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = 'A lot of something to say.'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book, display=True)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('<span'), len(b_values), msg)
        self.assertTrue(value in result, msg)

    def test_TEXT_BLOCK_entry(self):
        """
        Test that the TEXT_BLOCK type entry HTML is correct.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "percentage", DynamicColumn.TEXT_BLOCK, 'book_top', 6)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        value = 'A lot of something to say.'
        kv0 = self._create_key_value_record(book, dc0, value)
        b_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context, result = self._setup_template(Book, object=book)
        msg = "result: {}, context: {}, values: {}".format(
            result, context, b_values)
        self.assertEqual(result.count('textarea'), 4, msg)
        self.assertTrue(value in result, msg)


class TestSingleDisplay(BaseDcolumns, TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def _setup_template(self, model, object, slug, delimiter='as',
                        context_name=None, object_name='object'):
        # Setup the context.
        vmt = ViewMixinTest()
        vmt.model = model
        vmt.object = object
        context = Context(vmt.get_context_data())
        # Run the test.
        buff = io.StringIO()
        buff.write("{% load autodisplay %}")
        o = " {}".format(object_name)
        s = " {}".format(slug)
        d = " {}".format(delimiter)
        c = " {}".format(context_name) if context_name else ''
        cmd = "{{% single_display{}{}{}{} %}}".format(o, s, d, c)
        buff.write(cmd)
        template = buff.getvalue()
        buff.close()
        tr = Template(template)
        tr.render(context)
        return context

    def test_exceptions(self):
        """
        Test that exceptions happen when they are supposed to happen.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        book, b_cc, b_values = self._create_book_objects()
        # Test for tag requires four arguments.
        with self.assertRaises(TemplateSyntaxError) as cm:
            context = self._setup_template(Book, book, 'abstract')

        msg = "b_values: {}, exception: {}".format(b_values, cm.exception)
        self.assertTrue("requires four arguments" in str(cm.exception), msg)
        # Test for the word 'as'.
        with self.assertRaises(TemplateSyntaxError) as cm:
            context = self._setup_template(
                Book, book, 'abstract', delimiter='of',
                context_name='abstract')

        msg = "b_values: {}, exception: {}".format(b_values, cm.exception)
        self.assertTrue("must be the word 'as'" in str(cm.exception), msg)
        # Test KeyValue object does not exist with given slug.
        context = self._setup_template(
            Book, book, 'bad-slug', context_name='bad-slug')
        msg = "b_values: {}".format(b_values)
        self.assertEqual('', context.get('bad-slug'), msg)
        # Test that template.VariableDoesNotExist is raised and relation is
        # set to None.
        with self.assertRaises(VariableDoesNotExist) as cm:
            context = self._setup_template(
                Book, book, 'abstract', context_name='abstract',
                object_name='objectX')

    def test_BOOLEAN(self):
        """
        Test that the correct BOOLEAN type is returned in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Ignore", DynamicColumn.BOOLEAN, 'book_top', 2)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        # Test BOOLEAN with Yes
        value = "Yes"
        book.set_key_value('ignore', value)
        b_values['ignore'] = value
        context = self._setup_template(
            Book, book, 'ignore', context_name='ignore')
        msg= "context: {}, b_values: {}".format(context, b_values)
        self.assertEqual(True, context.get('ignore'), msg)
        # Test BOOLEAN with No
        value = "No"
        book.set_key_value('ignore', value)
        b_values['ignore'] = value
        context = self._setup_template(
            Book, book, 'ignore', context_name='ignore')
        msg= "context: {}, b_values: {}".format(context, b_values)
        self.assertEqual(False, context.get('ignore'), msg)
        # Test BOOLEAN with 1 (one)
        value = 1
        book.set_key_value('ignore', value)
        b_values['ignore'] = value
        context = self._setup_template(
            Book, book, 'ignore', context_name='ignore')
        msg= "context: {}, b_values: {}".format(context, b_values)
        self.assertEqual(True, context.get('ignore'), msg)
        # Test BOOLEAN with 0 (zero)
        value = 0
        book.set_key_value('ignore', value)
        b_values['ignore'] = value
        context = self._setup_template(
            Book, book, 'ignore', context_name='ignore')
        msg= "context: {}, b_values: {}".format(context, b_values)
        self.assertEqual(False, context.get('ignore'), msg)

    def test_CHOICE(self):
        """
        Test that the correct CHOICE type is returned in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        author, a_cc, a_values = self._create_author_objects()
        book, b_cc, b_values = self._create_book_objects(author=author)
        # Execute the template tag and test.
        context = self._setup_template(
            Book, book, 'author', context_name='author')
        value = book.get_key_value('author')
        msg = "context: {}, b_values: {}, value: {}".format(
            context, b_values, value)
        self.assertEqual(value, context.get('author'), msg)

    def test_CHOICE_store_relation(self):
        """
        Test that the correct CHOICE type with store_relation set is returned
        in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        promotion, p_cc, p_values = self._create_promotion_objects()
        book, b_cc, b_values = self._create_book_objects(promotion=promotion)
        # Execute the template tag and test.
        context = self._setup_template(
            Book, book, 'promotion', context_name='promotion')
        value = book.get_key_value('promotion')
        msg = "context: {}, b_values: {}, value: {}".format(
            context, b_values, value)
        self.assertTrue(value in context.get('promotion'), msg)

    def test_DATE(self):
        """
        Test that DATE is returned in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        promotion, p_cc, p_values = self._create_promotion_objects()
        # Execute the template tag and test.
        context = self._setup_template(
            Promotion, promotion, 'start_date', context_name='start_date')
        value = promotion.get_key_value('start_date')
        msg = "context: {}, p_values: {}, value: {}".format(
            context, p_values, value)
        self.assertEqual(value, context.get('start_date'), msg)

    def test_DATETIME(self):
        """
        Test that DATETIME is returned in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Date & Time", DynamicColumn.DATETIME, 'promotion_top', 6)
        promotion, p_cc, p_values = self._create_promotion_objects(
            extra_dcs=[dc0])
        value = datetime.now(timezone.utc).isoformat()
        kv0 = self._create_key_value_record(promotion, dc0, value)
        p_values[dc0.slug] = kv0.value
        # Execute the template tag and test.
        context = self._setup_template(
            Promotion, promotion, 'date-time', context_name='date_time')
        value = promotion.get_key_value('date-time')
        msg = "context: {}, p_values: {}, value: {}".format(
            context, p_values, value)
        self.assertEqual(value, context.get('date_time'), msg)

    def test_FLOAT(self):
        """
        Test that FLOAT is returned in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Percent", DynamicColumn.FLOAT, 'book_top', 2)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        # Set value
        value = 5.0
        book.set_key_value('percent', value)
        b_values['percent'] = value
        # Execute the template tag and test.
        context = self._setup_template(
            Book, book, 'percent', context_name='percent')
        value = book.get_key_value('percent')
        msg= "context: {}, b_values: {}, value: {}".format(
            context, b_values, value)
        self.assertEqual(value, context.get('percent'), msg)

    def test_NUMBER(self):
        """
        Test that NUMBER is returned in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Quanty", DynamicColumn.NUMBER, 'book_top', 2)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        # Set value
        value = 100
        book.set_key_value('quanty', value)
        b_values['quanty'] = value
        # Execute the template tag and test.
        context = self._setup_template(
            Book, book, 'quanty', context_name='quanty')
        value = book.get_key_value('quanty')
        msg= "context: {}, b_values: {}, value: {}".format(
            context, b_values, value)
        self.assertEqual(value, context.get('quanty'), msg)

    def test_TEXT_BLOCK(self):
        """
        Test that TEXT_BLOCK is returned in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Description", DynamicColumn.TEXT_BLOCK, 'book_top', 2)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        # Set value
        value = "This is a long description."
        book.set_key_value('description', value)
        b_values['description'] = value
        # Execute the template tag and test.
        context = self._setup_template(
            Book, book, 'description', context_name='description')
        value = book.get_key_value('description')
        msg= "context: {}, b_values: {}, value: {}".format(
            context, b_values, value)
        self.assertEqual(value, context.get('description'), msg)

    def test_TIME(self):
        """
        Test that TIME is returned in the context.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        dc0 = self._create_dynamic_column_record(
            "Now", DynamicColumn.TIME, 'book_top', 2)
        book, b_cc, b_values = self._create_book_objects(extra_dcs=[dc0])
        # Set value
        dt = datetime.now(tz=timezone.utc)
        value = dt_time(hour=dt.hour, minute=dt.minute, second=dt.second,
                        microsecond=dt.microsecond, tzinfo=dt.tzinfo)
        book.set_key_value('now', value)
        b_values['now'] = value
        # Execute the template tag and test.
        context = self._setup_template(
            Book, book, 'now', context_name='now')
        value = book.get_key_value('now')
        msg= "context: {}, b_values: {}, value: {}".format(
            context, b_values, value)
        self.assertEqual(value, context.get('now'), msg)


class TestCombineContexts(BaseDcolumns, TestCase):

    def __init__(self, name):
        super().__init__(name)

    def setUp(self):
        super().setUp()

    def _setup_template(self, model, object, obj, variable, extra_arg=''):
        # Setup the context.
        vmt = ViewMixinTest()
        vmt.model = model
        vmt.object = object
        context = Context(vmt.get_context_data())
        # Run the test.
        buff = io.StringIO()
        buff.write("{% load autodisplay %}")
        o = " {}".format(obj)
        v = " {}".format(variable)
        i = " {}".format(extra_arg)
        cmd = "{{% combine_contexts{}{}{} %}}".format(o, v, i)
        buff.write(cmd)
        template = buff.getvalue()
        buff.close()
        tr = Template(template)
        tr.render(context)
        return context

    def test_exceptions(self):
        """
        Test that any exceptions are raised in the proper conditions.
        """
        #self.skipTest("Temporarily skipped")
        # Create database objects.
        book, b_cc, b_values = self._create_book_objects()

        with self.assertRaises(TemplateSyntaxError) as cm:
            self._setup_template(Book, book, 'form.errors', 'relation.slug',
                                 extra_arg='junk')
