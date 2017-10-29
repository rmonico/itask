#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import subprocess
import io
import os

taskwarrior_binary = shutil.which('task')
__DEV__ = True


class TaskwarriorWrapper(object):

    def __init__(self):
        # TODO Its possible to improve this with more specific events
        self._listeners = {'data changed': []}

        if __DEV__:
            self._environment = os.environ.copy()
            self._environment['TASKDATA'] = '~/.itask_dev'
        else:
            self._environment = None

    def _internal_run(self, args, redirect_stdouterr=False):
        stdout = subprocess.PIPE if redirect_stdouterr else None
        stderr = subprocess.PIPE if redirect_stdouterr else None

        process = subprocess.Popen([taskwarrior_binary] + args, env=self._environment, stdout=stdout, stderr=stderr)

        process.wait()

        return process

    def register_listener(self, event, listener):
        self._listeners[event].append(listener)

    def remove_listener(self, event, listener):
        self._listeners[event].delete(listener)

    def _notify_listeners(self, event, *args, **kwargs):
        for listener in self._listeners[event]:
            listener(origin=self, *args, **kwargs)

    def load(self, filters):
        default_list_params = ['rc.defaultwidth:', 'rc._forcecolor:off', 'rc.color:off']
        if filters:
            process = self._internal_run(default_list_params + [filters], redirect_stdouterr=True)
        else:
            process = self._internal_run(default_list_params, redirect_stdouterr=True)

        return process.stdout

    def add(self, parameters):
        self._internal_run(['add'] + parameters)

        self._notify_listeners('data changed')

    def annotate(self, id, annotation):
        self._internal_run([str(id), 'annotate'] + annotation)

        self._notify_listeners('data changed')

    def done(self, ids):
        self._internal_run([str(i) for i in ids] + ['done'])

        self._notify_listeners('data changed')

    def view(self, ids):
        self._internal_run([str(i) for i in ids])

    def mod(self, ids, modifications):
        self._internal_run([str(i) for i in ids] + ['mod'] + modifications)

        self._notify_listeners('data changed')

    def delete(self, ids):
        self._internal_run([str(i) for i in ids] + ['del'])

        self._notify_listeners('data changed')

    def undo(self):
        self._internal_run(['undo'])

        self._notify_listeners('data changed')

    def sync(self):
        self._internal_run(['sync'])

        self._notify_listeners('data changed')

    def invalidate_data(self):
        self._notify_listeners('data changed')
