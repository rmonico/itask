#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

taskwarrior_binary = shutil.which('task')


class TaskwarriorWrapper(object):

    def __init__(self, task_data=None):
        # TODO Its possible to improve this with more specific events
        self._listeners = {'data changed': []}

        if task_data:
            self._environment = os.environ.copy()
            self._environment['TASKDATA'] = task_data
        else:
            self._environment = None

    def _internal_run(self, args, redirect_stdouterr=False):
        stdout = subprocess.PIPE if redirect_stdouterr else None
        stderr = subprocess.PIPE if redirect_stdouterr else None

        process = subprocess.run([taskwarrior_binary] + args, env=self._environment, stdout=stdout, stderr=stderr)

        return process

    def register_listener(self, event, listener):
        self._listeners[event].append(listener)

    def remove_listener(self, event, listener):
        self._listeners[event].delete(listener)

    def _notify_listeners(self, event, *args, **kwargs):
        for listener in self._listeners[event]:
            listener(origin=self, *args, **kwargs)

    def set_context(self, context):
        self._internal_run(['context', context])

    def get_context(self):
        process = self._internal_run(['context', 'list'], redirect_stdouterr = True)

        stdout = process.stdout.decode().split('\n')

        for line in stdout:
            fields = line.split(' ')

            if fields[-1] == 'yes':
                return fields[0]

            return None

    def load(self, report, filters, context=None):
        params = ['rc.defaultwidth:', 'rc._forcecolor:off', 'rc.color:off']

        if context:
            params += ['rc.context:{}'.format(context)]

        if report:
            params += [ report ]

        if filters:
            params += filters

        process = self._internal_run(params, redirect_stdouterr=True)

        return process.stdout.decode('utf-8')

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
