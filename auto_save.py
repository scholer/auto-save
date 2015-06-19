#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 James Zhang
# Copyright (c) 2015 Rasmus Sorensen
#
# The MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
AutoSave - Sublime Text Plugin

Provides a convenient way to turn on and turn off
automatically saving the current file after every modification.
'''


import sublime
import sublime_plugin
from threading import Timer

import logging
logger = logging.getLogger(__name__)

settings_filename = "auto_save.sublime-settings"
on_modified_field = "auto_save_on_modified"
delay_field = "auto_save_delay_in_seconds"


class AutoSaveListener(sublime_plugin.EventListener):

    save_queue = [] # Save queue for on_modified events.

    def on_modified(self, view):
        '''
        Invoked whenever the view's document is modified.
        '''
        # Note: It seems on_modified is actually called twice when re-loading a document.
        # The first time, view.is_dirty() is True, the second it is False.
        # Adding check for view.is_dirty() in the callback should do the
        # trick to prevent excessive saving conflicts.
        settings = sublime.load_settings(settings_filename)
        if not settings.get(on_modified_field):
            # auto-save not activated
            return
        if not view.is_dirty():
            logger.debug("on_modified invoked, but view is not dirty, so not scheduling auto-save.")
            return

        delay = settings.get(delay_field)

        def callback():
            '''
            Must use this callback for ST2 compatibility
            '''
            if view.is_dirty() and not view.is_loading():
                # This check seems to do the trick, preventing auto-save from saving file after reload from disk.
                logger.debug("Auto-save: Saving %s", view.file_name())
                view.run_command("save")
            else:
                logger.debug("Auto-save: callback invoked, but view is not dirty, so not saving document.")

        def debounce_save():
            '''
            If the queue is longer than 1, pop the last item off,
            Otherwise save and reset the queue.
            '''
            if len(AutoSaveListener.save_queue) > 1:
                AutoSaveListener.save_queue.pop()
            else:
                logger.debug("save_queue depleted, scheduling callback...")
                sublime.set_timeout(callback, 0)
                AutoSaveListener.save_queue = []

        # If auto_save_on_modified is enabled AND the view has an associated file:
        if settings.get(on_modified_field) and view.file_name() and view.is_dirty():
            AutoSaveListener.save_queue.append(0) # Append to queue for every on_modified event.
            Timer(delay, debounce_save).start() # Debounce save by the specified delay.


class AutoSaveCommand(sublime_plugin.WindowCommand):
    # Changed to be a Window command. Its effects are global and it doesn't use the active view...
    # We could have the option of having a per-view auto-save toggle in addition to a global one.

    def run(self, enable=None):
        '''
        This is used to toggle auto-save on and off.
        The user will generally bind this to a keystroke, e.g. ctrl+alt+s.
        If enable is given, auto save will be enabled (if True) or disabled (if False).
        If enable is not provided, auto save will be toggled (on if currently off and vice versa).
        '''
        settings = sublime.load_settings(settings_filename)
        if enable is None: # toggle
            enable = not settings.get(on_modified_field)
        on_or_off = "On" if enable else "Off"
        logger.info("Toggling auto-save %s.", on_or_off)
        settings.set(on_modified_field, enable)
        sublime.status_message("AutoSave Turned %s" % on_or_off)
