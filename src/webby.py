#!/usr/bin/env python
import base
import logging
import sys

import uri_open
import uri_goto
import smappen

CLOSE_ON_EXIT = False
LOG = logging.getLogger(__name__)


class CommandCollection:
    """
    Kind of feels like recreating argparse in a way, but argparse doesn't lend itself to more than one co-existing command.
    This will split commands and work with our DSL even with multiple commands
    """
    def __init__(self):
        self._command_factories = []
        self._commands = []

    def register_command(self, command_factory):
        """
        Add a command factory - typically the class that provides the functionality of the command, but can be any object
        that responds to a "build_command" function with a string.
        """
        self._command_factories.append(command_factory)


    def build_commands(self, argument_str):
        """
        Simple implementation at first
        Loop over every command, and if its name matches the command, start adding the following non-matching arguments to that command.

        TODO: delegate to factories to decide if they can handle a set of arguments (can we use argparse for this proactively somehow?)
        """

        current_factory = None
        commands_buffer = []

        def flush():
            nonlocal current_factory, commands_buffer
            if current_factory:
                LOG.trace("Aggregating args for last command %s: %s", current_factory.name, commands_buffer)
                # "Flush" current command, which is just-now-determined-to-be "last" command
                # as we've found a new command name. That is, send the aggregated arguments
                # to a new instance of the just-now-"last" command before clearing for the
                # just-now "current" command
                command_instance = current_factory(commands_buffer)
                LOG.debug("Command: %s", command_instance)
                self._commands.append(command_instance)
                # Set up the next command factory by clearing buffers
                current_factory = None
                commands_buffer = []

        for token in argument_str:
            token_is_command = False
            for c in self._command_factories:
                if c.name == token:
                    token_is_command = True
                    LOG.trace("Found new command %s", c.name)
                    flush()
                    current_factory = c
                    next
            # We didn't register as a command name, it must be an argument.
            if not token_is_command:
                commands_buffer.append(token)
        # If there is a current factory (typical for the last factory we were building) there won't be a "next"
        # command name to trigger aggregation and building, so just flush manually at the end.
        flush()

    def execute(self):
        for c in self._commands:
            c.execute()



print(sys.argv)
cc = CommandCollection()
cc.register_command(uri_open.Open)
cc.register_command(uri_goto.Goto)
cc.register_command(smappen.SmappenEnsureLogin)

cc.build_commands(sys.argv[1:])

cc.execute()

LOG.info("Complete!")
if CLOSE_ON_EXIT:
    base.driver.close()