This problem arose with the introduction of Django 4.0 when they added functionality.
See: https://docs.djangoproject.com/en/5.0/releases/4.0/#template-based-form-rendering

The following tests in dcolumn/dcolumns/tests/test_dcolumns_forms.py fail:
test_validate_choice_relation
test_validate_pseudo_choice_relation
test_validate_stored_relation
test_validate_data
test_validate_time
test_validate_datetime
test_validate_float
test_validate_integer
test_validate_text_block

As of now 2024-05-05 I do not know what the fix needs to be. As of now there is very
little usage of this Django plugin so it is at the bottom of my list to fix. If someone
is able to find the issues please send a PR or at least let me know by email.

carl dot nobile at gmail.com
