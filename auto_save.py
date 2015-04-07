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
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

settings_filename = "auto_save.sublime-settings"
on_modified_field = "auto_save_on_modified"
delay_field = "auto_save_delay_in_seconds"


class AutoSaveListener(sublime_plugin.EventListener):

    save_queue = [] # Save queue for on_modified events.

    def on_load(self, view):
        """
        on_modified can be issued upon document reload.
        We want to check whether on_modified was called due to a
        document reload. If that is the case, then we should NOT
        attempt to save the document again.
        Why? If the document is being edited by another application,
        saving the document when it is reloaded can create a race
        condition between the two applications, producing version
        conflicts.

        Unfortunately, on_load is only called on initial load,
        not on automatic reload.

        So, uh... it seems on_modified is actually called twice when re-loading a document.
        The first time, view.is_dirty() is True, the second it is False.
        Regardless - adding checks for view.is_dirty() should do the trick to prevent excessive saving conflicts.

reloading /C/Users/(...)/Dropbox/(...)/test.txt
20:07:49 DEBUG  auto-save.auto_save:79           on_modified() view.is_dirty(): True, view.is_loading(): False
20:07:49 DEBUG  auto-save.auto_save:113          on_modified() Appending save_queue and setting debounce_save timer, view.is_dirty()=True, queue: [0]
20:07:49 DEBUG  auto-save.auto_save:115          on_modified() on_modified end
20:07:49 DEBUG  auto-save.auto_save:79           on_modified() view.is_dirty(): False, view.is_loading(): False
20:07:49 DEBUG  auto-save.auto_save:81           on_modified() on_modified invoked, but view is not dirty, so not scheduling auto-save.
20:07:50 DEBUG  auto-save.auto_save:105        debounce_save() save_queue depleted, scheduling callback...
20:07:50 INFO   auto-save.auto_save:90              callback() Saving C:/Users/(...)/Dropbox/(...)/test.txt
20:07:50 DEBUG  auto-save.auto_save:91              callback() view.is_dirty(): False, view.is_loading(): False
20:07:50 DEBUG  auto-save.auto_save:93              callback() auto-save CALLBACK invoked, but view is not dirty, so not saving document.

        """
        settings = sublime.load_settings(settings_filename)
        logger.info("Document previously loaded: %s", view.settings().get("auto_save_document_last_loaded"))
        settings.set("auto_save_document_last_loaded", datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
        logger.info("Document (re)loaded: %s", view.settings().get("auto_save_document_last_loaded"))


    def on_modified(self, view):
        ''' Invoked whenever the view's document is modified. '''
        settings = sublime.load_settings(settings_filename)
        if not settings.get(on_modified_field):
            # auto-save not activated
            logger.debug("Auto-save not activated...")
            return
        logger.debug("view.is_dirty(): %s, view.is_loading(): %s", view.is_dirty(), view.is_loading())
        if not view.is_dirty():
            logger.debug("on_modified invoked, but view is not dirty, so not scheduling auto-save.")
            return

        delay = settings.get(delay_field)

        def callback():
            '''
            Must use this callback for ST2 compatibility
            '''
            logger.info("Saving %s", view.file_name())
            logger.debug("view.is_dirty(): %s, view.is_loading(): %s", view.is_dirty(), view.is_loading())
            if not view.is_dirty() or view.is_loading():
                # This check seems to do the trick, preventing
                logger.debug("auto-save CALLBACK invoked, but view is not dirty, so not saving document.")
            else:
                view.run_command("save")

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
            logger.debug("Appending save_queue and setting debounce_save timer, view.is_dirty()=%s, queue: %s",
                         view.is_dirty(), AutoSaveListener.save_queue)
            Timer(delay, debounce_save).start() # Debounce save by the specified delay.
        logger.debug("on_modified end")


class AutoSaveCommand(sublime_plugin.TextCommand):

    def run(self, view):
        '''
        This is used to toggle auto-save on and off.
        The user will generally bind this to a keystroke, e.g. ctrl+alt+s.
        '''
        settings = sublime.load_settings(settings_filename)

        if settings.get(on_modified_field):
            logger.info("Toggling auto-save off.")
            settings.set(on_modified_field, False)
            sublime.status_message("AutoSave Turned Off")
        else:
            logger.info("Toggling auto-save on.")
            settings.set(on_modified_field, True)
            sublime.status_message("AutoSave Turned On")
