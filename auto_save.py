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
    settings = sublime.load_settings(settings_filename)
    if not (settings.get(on_modified_field) and view.file_name() and view.is_dirty()):
      return

    delay = settings.get(delay_field)


    def callback():
      '''
      Must use this callback for ST2 compatibility
      '''
      if view.is_dirty() and not view.is_loading():
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


    AutoSaveListener.save_queue.append(0) # Append to queue for every on_modified event.
    Timer(delay, debounce_save).start() # Debounce save by the specified delay.


class AutoSaveCommand(sublime_plugin.ApplicationCommand):

  def run(self, enable=None):
    '''
    Toggle auto-save on and off. Can be bound to a keystroke, e.g. ctrl+alt+s.
    If enable argument is given, auto save will be enabled (if True) or disabled (if False).
    If enable is not provided, auto save will be toggled (on if currently off and vice versa).
    '''
    settings = sublime.load_settings(settings_filename)
    if enable is None: # toggle
      enable = not settings.get(on_modified_field)
    logger.info("Toggling auto-save %s.", "On" if enable else "Off")
    settings.set(on_modified_field, enable)
    sublime.status_message("AutoSave Turned %s" % ("On" if enable else "Off"))
