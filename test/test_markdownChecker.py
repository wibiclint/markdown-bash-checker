import unittest
from markdown_bash_checker import MarkdownChecker
from textwrap import dedent
import logging

__author__ = 'clint'

class TestMarkdownChecker(unittest.TestCase):
    legal_markdown = """
        ```bash-env
        export FOO=foo
        ```
        ```bash-exec
        echo $FOO
        ```
        ```bash-output
        foo
        ```
    """

    markdown_output_check_fails = """
        ```bash-env
        export FOO=foo
        ```
        ```bash-exec
        echo $FOO
        ```
        ```bash-output
        foobar
        ```
    """

    markdown_illegal_exec = """
        ```bash-exec
        ezport FOO=foo
        ```
    """

    markdown_illegal_env = """
        ```bash-env
        ezport FOO=foo
        ```
    """

    def test_legal_markdown(self):
        """ Try running a basic test on a legal markdown file. """
        foo = MarkdownChecker()
        foo._markdown_text = dedent(self.legal_markdown)
        foo._parse_markdown()
        self.assertEqual(3, len(foo._bash_commands))
        foo._execute_bash_commands()

    @unittest.expectedFailure
    def test_markdown_incorrect_output(self):
        """ This markdown has an output check that should fail. """
        foo = MarkdownChecker()
        foo._markdown_text = dedent(self.markdown_output_check_fails)
        foo._parse_markdown()
        self.assertEqual(3, len(foo._bash_commands))
        foo._execute_bash_commands()

    @unittest.expectedFailure
    def test_markdown_illegal_exec(self):
        """ This markdown has an illegal bash statement in it. """
        foo = MarkdownChecker()
        foo._markdown_text = dedent(self.markdown_illegal_exec)
        foo._parse_markdown()
        self.assertEqual(1, len(foo._bash_commands))
        foo._execute_bash_commands()

    @unittest.expectedFailure
    def test_markdown_illegal_env(self):
        """ This markdown has an illegal env bash statement in it. """
        foo = MarkdownChecker()
        foo._markdown_text = dedent(self.markdown_illegal_env)
        foo._parse_markdown()
        self.assertEqual(1, len(foo._bash_commands))
        foo._execute_bash_commands()
