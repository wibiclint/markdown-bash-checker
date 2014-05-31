#!/user/bin/env python3

description = """
Parses a specially-formatted markdown file and executes all of the specially-marked bash code blocks.  Useful for
checking that all of the commands in a tutorial work.

Code blocks to execute use the following special languages:
    * bash-env - Indicates a commands that modifies the environment somehow.  These commands will be run before every
        bash-exec command
    * bash-exec - Command to execute
    * bash-output - Indicates that the output of the previous command should match this.

Features to add:
    * Some flexible methodology for regular expressions in bash-output

"""

import argparse
import os
import re
import logging
import sys
import subprocess
import mistune


def run(cmd):
    result = ""
    try:
        result = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        sys.stderr.write("Error running command '%s'\n" % cmd)
        sys.stderr.write("Exit code = %s\n" % e.returncode)
        sys.stderr.write("Output = %s\n" % e.output)
        raise e
    # Decode bytes into a string.
    return result.decode('utf-8')


# Various types of code blocks to capture from the markdown source.
class BashExec(object):
    """ Superclass for executable bash commands. """
    def __init__(self, code):
        # TODO: Trim the shell prompt away?
        self._code = code

    def __str__(self):
        return "Bash executable command: %s" % self._code

    def get_executable_command_string(self):
        # TODO: Trim the shell prompt away?
        return self._code

    def execute_with_prereqs_and_return_results(self, prereqs):
        """
        Execute this command, along with some prerequisite commands that can alter the environment.

        :param prereqs: Prerequisite commands to run before this command (usually set environment vars).
        :return: The results of executing the prerequisites and then this command.
        """
        logging.debug("Running %s with prerequisites" % self)
        all_commands = [cmd.get_executable_command_string() for cmd in prereqs] + [self.get_executable_command_string(),]
        # TODO: Some try/catch here in case the command fails?
        result = run('\n'.join(all_commands))
        logging.debug("Result = %s" % result)
        return result


class BashEnv(BashExec):
    """ Executable bash commands that also alter the environment. """
    def __str__(self):
        return "Bash environment-altering command: %s" % self._code



class BashOutput(object):
    def __init__(self, output_to_check):
        self._output_to_check = output_to_check

    def compare_with_actual_output(self, actual_output, trim_trailing_newline=False):
        """
        Check that the user-specified output in the markdown file matches the actual result from running the previous
        executable command.

        :param actual_output: from the previous executable bash command.
        :param trim_trailing_newline: whether to trim the last newline in the actual output.
        """

        if trim_trailing_newline and actual_output.endswith("\n"):
            actual_output = actual_output[:-1]

        if self._output_to_check == actual_output:
            return

        raise Exception(
            'Expected result does not match actual result.  Expected = %s\nActual = %s\n' % (
                self._output_to_check,
                actual_output
            ))


class MyRenderer(mistune.Renderer):

    def __init__(self, *args, **kwargs):
        super(MyRenderer, self).__init__(*args, **kwargs)
        self._bash_commands = []

    @staticmethod
    def _bash_command_factory(code, lang):
        if lang == 'bash-env':
            return BashEnv(code)
        elif lang == 'bash-exec':
            return BashExec(code)
        elif lang == 'bash-output':
            return BashOutput(code)
        else:
            pass

    def _update_bash_commands(self, code, lang):
        bash_command_object = MyRenderer._bash_command_factory(code, lang)
        if bash_command_object is not None:
            self._bash_commands.append(bash_command_object)

    def block_code(self, code, lang=None):
        # Optionally create a new bash command to run later.
        self._update_bash_commands(code, lang)
        return super(MyRenderer, self).block_code(code, lang)

class MarkdownChecker(object):
    """
    Responsible for running a modified Markdown checker, gathering specially-formatted code blocks, running them in
    bash, and verifying that the outputs are correct.

    """

    def __init__(self):
        self._markdown_file = None
        self._markdown_text = None
        self._bash_commands = None

    def _create_parser(self):
        """ Create the command-line argument parser. """
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawTextHelpFormatter
        )

        parser.add_argument("markdown_file", help="Markdown file to parse.")

        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            default=False,
            help='Verbose mode (turn on logging.info)')

        parser.add_argument(
            '-d',
            '--debug',
            action='store_true',
            default=False,
            help='Debug (turn on logging.debug)')

        return parser

    def _parse_options(self, cmd_line_args):
        """ Parse the command-line options and store them in member variables. """
        args = self._create_parser().parse_args(cmd_line_args)

        if args.verbose and not args.debug:
            logging.basicConfig(level=logging.INFO)

        if args.debug:
            logging.basicConfig(level=logging.DEBUG)

        self._markdown_file = args.markdown_file
        assert os.path.isfile(self._markdown_file), "Cannot find markdown file %s" % self._markdown_file

    def _get_markdown(self):
        self._markdown_text = open(self._markdown_file).read()

    def _parse_markdown(self):
        """ Actually parse the markdown file, capturing the bash commands to run in a list. """
        renderer = MyRenderer()
        md = mistune.Markdown(renderer=renderer)
        md.render(self._markdown_text)
        self._bash_commands = renderer._bash_commands

    def _execute_bash_commands(self):
        """ Go through all of the commands and execute them (or verify the output of previous commands. """

        # Keep track of all of the env commands listed up until the current bash command.  We need to run the env
        # commands before every bash command.
        current_env_altering_commands = []
        most_recent_result = None

        for command in self._bash_commands:
            # Ah, if only for Scala's beautiful pattern matching...  Sigh.
            if isinstance(command, BashEnv):
                # Execute the command, just to make sure that it works.
                most_recent_result = command.execute_with_prereqs_and_return_results(current_env_altering_commands)

                # Add it to the list of environment-altering commands.
                current_env_altering_commands.append(command)

            elif isinstance(command, BashExec):
                # Execute all environment-altering commands, followed by this command.
                most_recent_result = command.execute_with_prereqs_and_return_results(current_env_altering_commands)

            elif isinstance(command, BashOutput):
                assert most_recent_result is not None
                command.compare_with_actual_output(most_recent_result, True)

            else:
                assert False, "Not sure what time of bash command %s is!" % command


    def go(self, cmd_line_args):
        self._parse_options(cmd_line_args)
        self._get_markdown()
        self._parse_markdown()
        self._execute_bash_commands()


if __name__ == "__main__":
    foo = MarkdownChecker()
    foo.go(sys.argv[1:])
