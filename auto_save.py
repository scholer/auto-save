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


settings_filename = "auto_save.sublime-settings"
on_modified_field = "auto_save_on_modified"
delay_field = "auto_save_delay_in_seconds"


class AutoSaveListener(sublime_plugin.EventListener):

    save_queue = [] # Save queue for on_modified events.

    def on_modified(self, view):
        ''' Invoked whenever the view's document is modified. '''
        settings = sublime.load_settings(settings_filename)
        delay = settings.get(delay_field)


        def callback():
            '''
            Must use this callback for ST2 compatibility
            '''
            view.run_command("save")


        def debounce_save():
            '''
            If the queue is longer than 1, pop the last item off,
            Otherwise save and reset the queue.
            '''
            if len(AutoSaveListener.save_queue) > 1:
                AutoSaveListener.save_queue.pop()
            else:
                sublime.set_timeout(callback, 0)
                AutoSaveListener.save_queue = []


        if settings.get(on_modified_field) and view.file_name():
            AutoSaveListener.save_queue.append(0) # Append to queue for every on_modified event.
            Timer(delay, debounce_save).start() # Debounce save by the specified delay.


class AutoSaveCommand(sublime_plugin.TextCommand):

    def run(self, view):
        '''
        This is used to toggle auto-save on and off.
        The user will generally bind this to a keystroke, e.g. ctrl+alt+s.
        '''
        settings = sublime.load_settings(settings_filename)

        if settings.get(on_modified_field):
            settings.set(on_modified_field, False)
            sublime.status_message("AutoSave Turned Off")
        else:
            settings.set(on_modified_field, True)
            sublime.status_message("AutoSave Turned On")
