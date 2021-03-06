"""Test-suite uses py.test (pip install pytest)."""
# -*- coding: utf-8 -*-
import os
import sys
from contextlib import contextmanager
try:
    from StringIO import StringIO
except ImportError:
    # Python 3.0 and later
    from io import StringIO

import mock
import pep8

import pep257


FILES = ['pep257.py', 'test_pep257.py']
default_options = mock.Mock(explain=False, range=False, quote=False)


@contextmanager
def capture_stdout(destination):
    real_stdout = sys.stdout
    sys.stdout = destination
    yield
    sys.stdout = real_stdout


def test_pep257_conformance():
    assert pep257.check_files(FILES) == []


def test_pep8_conformance():
    assert pep8.StyleGuide().check_files(FILES).total_errors == 0


def test_parse_docstring():
    s1 = '''def foo():  # o hai comment
    """docstring"""
    2 + 2'''
    assert pep257.parse_docstring(s1) == '"""docstring"""'

    s2 = '''def foo():  # o hai comment
    2 + 2'''
    assert pep257.parse_docstring(s2) is None

    assert pep257.parse_docstring("def foo():pass") is None
    # TODO
    #assert pep257.parse_docstring("def bar():'doc';pass") == "'doc'"


def test_abs_pos():
    assert pep257.abs_pos((1, 0), 'foo') == 0
    assert pep257.abs_pos((1, 2), 'foo') == 2
    assert pep257.abs_pos((2, 0), 'foo\nbar') == 4


def test_rel_pos():
    assert pep257.rel_pos(0, 'foo') == (1, 0)
    assert pep257.rel_pos(2, 'foo') == (1, 2)
    assert pep257.rel_pos(4, 'foo\nbar') == (2, 0)
    assert pep257.rel_pos(6, 'foo\nbar') == (2, 2)


def test_parse_functions():
    parse = pep257.parse_functions
    assert parse('') == []
    # TODO assert pf('def foo():pass') == ['def foo():pass']
    assert parse('def foo():\n    pass\n') == ['def foo():\n    pass\n']
    assert parse('def foo():\n  pass') == ['def foo():\n  pass']
    f1 = '''def foo():\n  pass\ndef bar():\n  pass'''
    assert parse(f1) == ['def foo():\n  pass\n',
                         'def bar():\n  pass']
    f2 = '''def foo():\n  pass\noh, hai\ndef bar():\n  pass'''
    assert parse(f2) == ['def foo():\n  pass\n',
                         'def bar():\n  pass']


def test_parse_methods():
    parse = pep257.parse_methods
    assert parse('') == []
    m1 = '''class Foo:
    def m1():
        pass
    def m2():
        pass'''
    assert parse(m1) == ['def m1():\n        pass\n    ',
                         'def m2():\n        pass']
    m2 = '''class Foo:
    def m1():
        pass
    attribute
    def m2():
        pass'''
    assert parse(m2) == ['def m1():\n        pass\n    ',
                         'def m2():\n        pass']


def test_check_triple_double_quotes():
    check = pep257.check_triple_double_quotes
    assert check("'''Not using triple douple quotes'''", None, None)
    assert not check('"""Using triple double quotes"""', None, None)
    assert not check('r"""Using raw triple double quotes"""', None, None)
    assert not check('u"""Using unicode triple double quotes"""', None, None)


def test_check_backslashes():
    check = pep257.check_backslashes
    assert check('"""backslash\\here""""', None, None)
    assert not check('r"""backslash\\here""""', None, None)


def test_check_unicode_docstring():
    check = pep257.check_unicode_docstring
    assert not check('"""No Unicode here."""', None, None)
    assert not check('u"""Здесь Юникод: øπΩ≈ç√∫˜µ≤"""', None, None)
    assert check('"""Здесь Юникод: øπΩ≈ç√∫˜µ≤"""', None, None)


def test_check_ends_with_period():
    check = pep257.check_ends_with_period
    assert check('"""Should end with a period"""', None, None)
    assert not check('"""Should end with a period."""', None, None)


def test_check_blank_before_after_class():
    check = pep257.check_blank_before_after_class
    c1 = '''class Perfect(object):

    """This should work perfectly."""

    pass'''
    assert not check('"""This should work perfectly."""', c1, False)

    c2 = '''class BadTop(object):
    """This should fail due to a lack of whitespace above."""

    pass'''
    assert check('"""This should fail due to a lack of whitespace above."""',
                 c2, False)
    c3 = '''class BadBottom(object):

    """This should fail due to a lack of whitespace below."""
    pass'''
    assert check('"""This should fail due to a lack of whitespace below."""',
                 c3, False)
    c4 = '''class GoodWithNoFollowingWhiteSpace(object):

    """This should work."""'''
    assert not check('"""This should work."""',
                     c4, False)
    c5 = '''class GoodWithFollowingWhiteSpace(object):

    """This should work."""


'''
    assert not check('"""This should work."""', c5, False)


def test_check_blank_after_summary():
    check = pep257.check_blank_after_summary
    s1 = '''"""Blank line missing after one-line summary.
    ....................
    """'''
    s2 = '''"""Blank line missing after one-line summary.

    """'''
    assert check(s1, None, None)
    assert not check(s2, None, None)


def test_check_indent():
    check = pep257.check_indent
    context = '''def foo():
    """Docstring.

    Properly indented.

    """
    pass'''
    assert not check('"""%s"""' % context.split('"""')[1], context, None)
    context = '''def foo():
    """Docstring.

Not Properly indented.

    """
    pass'''
    assert check('"""%s"""' % context.split('"""')[1], context, None)


def test_check_blank_after_last_paragraph():
    check = pep257.check_blank_after_last_paragraph
    s1 = '''"""Multiline docstring should end with 1 blank line.

    Blank here:

    """'''
    s2 = '''"""Multiline docstring should end with 1 blank line.

    No blank here.
    """'''
    assert not check(s1, None, None)
    assert check(s2, None, None)


def test_failed_open():
    filename = "non-existent-file.py"
    assert not os.path.exists(filename)

    captured = StringIO()
    with capture_stdout(captured):
        pep257.main(default_options, [filename])

    captured_lines = captured.getvalue().strip().split('\n')
    assert captured_lines == [
        '=' * 80,
        'Note: checks are relaxed for scripts (with #!) compared to modules',
        'Error opening file non-existent-file.py'
    ]


def test_failed_read():
    captured = StringIO()

    open_mock = mock.MagicMock()
    handle = mock.MagicMock()
    handle.read.side_effect = IOError('Stubbed read error')
    open_mock.__enter__.return_value = handle
    open_mock.return_value = handle

    with capture_stdout(captured):
        with mock.patch('__builtin__.open', open_mock, create=True):
            pep257.main(default_options, ['dummy-file.py'])

    open_mock.assert_called_once_with('dummy-file.py')
    handle.close.assert_called_once_with()

    captured_lines = captured.getvalue().strip().split('\n')
    assert captured_lines == [
        '=' * 80,
        'Note: checks are relaxed for scripts (with #!) compared to modules',
        'Error reading file dummy-file.py',
    ]


def test_opened_files_are_closed():
    files_opened = []
    real_open = open

    def open_wrapper(*args, **kw):
        opened_file = mock.MagicMock(wraps=real_open(*args, **kw))
        files_opened.append(opened_file)
        return opened_file
    open_mock = mock.MagicMock(side_effect=open_wrapper)
    open_mock.__enter__.side_effect = open_wrapper

    with mock.patch('__builtin__.open', open_mock, create=True):
        pep257.main(default_options, ['pep257.py'])

    open_mock.assert_called_once_with('pep257.py')
    assert len(files_opened) == 1
    for opened_file in files_opened:
        opened_file.close.assert_called_once_with()
