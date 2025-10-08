#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import re

taskwarrior_binary = shutil.which('task')


class TaskwarriorWrapper(object):

    def __init__(self, task_data=None, context=None):
        # TODO Its possible to improve this with more specific events
        self._listeners = {'data changed': []}

        if task_data:
            self._environment = os.environ.copy()
            self._environment['TASKDATA'] = task_data
        else:
            self._environment = None

        self._context = context

        if self._context is None:
            self._context = self.get_external_context()

    def _auto_args(self):
        if self._context is not None:
            return [f'rc.context={self._context}']
        else:
            return []

    def _internal_run(self, args, redirect_stdouterr=False):
        stdout = subprocess.PIPE if redirect_stdouterr else None
        stderr = subprocess.PIPE if redirect_stdouterr else None

        process_args = [taskwarrior_binary] + self._auto_args() + args

        process = subprocess.run(process_args, env=self._environment,
                                 stdout=stdout, stderr=stderr)

        return process

    def _parse_table(self, raw_stdout):
        stdout = raw_stdout.decode().split('\n')

        stdout = stdout[2:-2]

        items = dict()

        for line in stdout:
            matchs = re.match('^([a-z0-9_\.]+) +(.*)', line)
            if matchs:
                groups = matchs.groups()
                key = groups[0]
                value = groups[1]
                items[key] = value

        return items

    def register_listener(self, event, listener):
        self._listeners[event].append(listener)

    def remove_listener(self, event, listener):
        self._listeners[event].delete(listener)

    def _notify_listeners(self, event, *args, **kwargs):
        for listener in self._listeners[event]:
            listener(origin=self, *args, **kwargs)

    def get_external_context(self):
        process = self._internal_run(['context', 'show'],
                                     redirect_stdouterr=True)

        stdout = process.stdout.decode().split('\n')

        first_line = stdout[0]

        match = re.match(r'Context \'(.*)\' with', first_line)

        if not match:
            return None

        return match.groups()[0]

    def get_context(self):
        return self._context

    def set_context(self, context):
        self._context = context

    def contexts(self):
        process = self._internal_run(['show', 'context.'],
                                     redirect_stdouterr=True)

        raw = self._parse_table(process.stdout)

        contexts_ = dict()

        for key, value in raw.items():
            tokens = key.split('.')
            name = tokens[1]

            active = self._context == name

            context = contexts_.setdefault(name, {'name': name,
                                                  'active': active})

            prop = tokens[2]

            context[prop] = value

        return contexts_.values()

    def load(self, report, filters):
        params = ['rc.defaultwidth:', 'rc._forcecolor:off', 'rc.color:off']

        if report:
            params += [report]

        if filters:
            params += filters

        process = self._internal_run(params, redirect_stdouterr=True)

        return process.stdout.decode()

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

    def delete(self, ids, comment):
        self._internal_run([str(i) for i in ids] + ['del', comment])

        self._notify_listeners('data changed')

    def undo(self):
        self._internal_run(['undo'])

        self._notify_listeners('data changed')

    def sync(self):
        self._internal_run(['sync'])

        self._notify_listeners('data changed')

    def reports(self):
        # TODO Usar o _parse_table
        process = self._internal_run(['reports'], redirect_stdouterr=True)

        stdout = process.stdout.decode().split('\n')

        stdout = stdout[2:-2]

        reports = dict()

        for line in stdout:
            matchs = re.match('^([a-z0-9_\.]+) +(.*)', line)
            if matchs:
                groups = matchs.groups()
                reports[groups[0]] = groups[1]

        return reports

    def projects(self):
        self._internal_run(['projects'])

    def tags(self):
        self._internal_run(['tags'])

    def get_config(self, config):
        # TODO Usar o _parse_table
        process = self._internal_run(['show', config], redirect_stdouterr=True)

        stdout = process.stdout.decode().split('\n')

        entry = [line for line in stdout[3:] if line.startswith(config)]
        if len(entry) == 0:
            return None
        else:
            entry = entry[0]

        separator_index = entry.find(' ')

        return entry[separator_index + 1:]

    def invalidate_data(self):
        self._notify_listeners('data changed')
