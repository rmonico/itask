#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import shutil
from itask.dataprovider import DataProvider
from itask.imenu import Menu, MenuItem, Navigable, BackMenuItem
from itask.selection import Selection
from itask.taskwarriorreportparser import TaskwarriorReportParser
from itask.taskwarriorwrapper import TaskwarriorWrapper
from itask.viewer import Viewer, Region

from itask import console


import signal


class MainMenu(Navigable):

    def __init__(self, taskwarrior_wrapper, args):
        super(MainMenu, self).__init__()

        self.report = args.report

        self.filters = args.filter.split(' ') if args.filter else None

        self.context = args.context

        self._binary_wrapper = taskwarrior_wrapper

        self._binary_wrapper.register_listener('data changed', self._data_changed)

        self._data_provider = DataProvider()

        self._report_parser = TaskwarriorReportParser()

        self._first_usable_line = 1

        self._make_menu()

        self._do_data_update()

    def _make_menu(self):
        self.main_menu = Menu(redraw=False, back=False)

        self.main_menu.items.append(MenuItem(title='Add', hotkey='a', action=self.task_add))
        self.main_menu.items.append(MenuItem(title='Annotate', hotkey='n', action=self.task_annotate))
        self.main_menu.items.append(MenuItem(title='Note', hotkey='N', action=self.task_note))
        self.main_menu.items.append(MenuItem(title='Done', hotkey='O', action=self.task_done))
        self.main_menu.items.append(MenuItem(title='View', hotkey='v', action=self.task_view))
        self.main_menu.items.append(MenuItem(title='Mod', hotkey='m', action=self.task_mod))
        self.main_menu.items.append(MenuItem(title='Filter', hotkey='f', action=self.set_filter))
        self.main_menu.items.append(MenuItem(title='Append filter', hotkey='F', action=self.append_filter))
        self.main_menu.items.append(MenuItem(title='Delete', hotkey='D', action=self.task_del))
        self.main_menu.items.append(MenuItem(title='Undo', hotkey='U', action=self.task_undo))
        self.main_menu.items.append(MenuItem(title='Reload', hotkey='R', action=self.task_reload))
        self.main_menu.items.append(MenuItem(title='Sync', hotkey='S', action=self.task_sync))
        # self.main_menu.items.append(MenuItem(title='Unfilter', hotkey='x', action=self._binary_wrapper.clean_filter))
        self.main_menu.items.append(MenuItem(title='Report', hotkey='r', action=self.select_report))
        self.main_menu.items.append(MenuItem(title='Context', hotkey='c', action=self.select_context))
        self.main_menu.items.append(MenuItem(title='Projects', hotkey='p', action=self.show_projects))
        self.main_menu.items.append(MenuItem(title='Tags', hotkey='t', action=self.show_tags))

        self.main_menu.append_quit(self._quit)

        self.main_menu.append_navigation_keys(self)

        self.main_menu.register_listener('render', self.render)
        self.main_menu.register_listener('item chosen', self.item_chosen)
        self.main_menu.register_listener('after action', self.after_action)

        signal.signal(signal.SIGWINCH, self._terminal_resized)

    def _terminal_resized(self, signal_number, stack):
        stack[len(stack)].f_back()

        self._make_menu()

        self._do_data_update()

    def _make_gui(self):
        if self._has_data():
            fixed_left = self._report_parser.idColumnWidth()
        else:
            fixed_left = 0
        fixed_top = 2
        menu_height = 2
        footer_height = 2

        left_top_fixed_region = Region(size={'width': fixed_left, 'height': fixed_top},
                                       position={'left': 0, 'top': self._first_usable_line})

        self._left_top_fixed_viewer = Viewer(self._data_provider, left_top_fixed_region, screen_left=0, screen_top=0)

        terminal_size = shutil.get_terminal_size()

        data_width = terminal_size.columns - fixed_left - 1
        data_horizontal_constraints = {'left': fixed_left, 'right': self._data_provider.size.largest_line}
        header_region = Region(
            size={'width': data_width, 'height': fixed_top},
            position={'left': fixed_left, 'top': self._first_usable_line},
            horizontal_constraints=data_horizontal_constraints)

        self._header_viewer = Viewer(self._data_provider, header_region, screen_left=fixed_left, screen_top=0)

        data_height = terminal_size.lines - fixed_top - menu_height
        data_vertical_constraints = {'top': self._first_usable_line + fixed_top,
                                     'bottom': self._data_provider.size.lines - footer_height - 1}

        self._selection = Selection(self._first_usable_line + fixed_top, constraints=data_vertical_constraints)

        left_region = Region(
            size={'width': fixed_left, 'height': data_height},
            position={'left': 0, 'top': self._first_usable_line + fixed_top},
            vertical_constraints=data_vertical_constraints)

        self._left_viewer = Viewer(self._data_provider, left_region, self._selection, screen_left=0, screen_top=2)

        data_region = Region(
            size={'width': data_width, 'height': data_height},
            position={'left': fixed_left, 'top': 3},
            horizontal_constraints=data_horizontal_constraints,
            vertical_constraints=data_vertical_constraints)

        self._data_viewer = Viewer(
            self._data_provider,
            data_region,
            self._selection,
            screen_left=fixed_left,
            screen_top=2)

    def run(self):
        self.main_menu.run()

    def _do_data_update(self):
        stream = self._binary_wrapper.load(self.report, self.filters, self.context)

        self._data_provider.update(stream)

        if self._has_data():
            self._report_parser.set_header_line(self._data_provider.lines[self._first_usable_line])

        self._update_menu_title()

        self._make_gui()

    def _has_data(self):
        return len(self._data_provider.lines) > 1

    def _data_changed(self, origin):
        self._do_data_update()

        self._selection.clear()

    def render(self, origin):
        console.change_cursor_visibility(False)
        console.change_getch_echo(False)

        self._left_top_fixed_viewer.update()
        self._header_viewer.update()
        self._left_viewer.update()
        self._data_viewer.update()

    def item_chosen(self, origin, item):
        if item.interactive:
            console.change_cursor_visibility(True)
            console.change_getch_echo(True)

            console.clear_screen()

            self._left_top_fixed_viewer.invalidate()
            self._header_viewer.invalidate()
            self._left_viewer.invalidate()
            self._data_viewer.invalidate()

    def after_action(self, origin, item):
        if item and item.interactive:
            console.change_cursor_visibility(True)
            console.change_getch_echo(True)
            console.clear_screen()

    def _quit(self):
        print('Bye!')

    def _get_selected_ids(self):
        if len(self._selection.selected_lines) == 0:
            active_line = self._data_provider.lines[self._selection.active_line]

            return [self._report_parser.getId(active_line)]

        ids = []

        for line in self._selection.selected_lines:
            ids.append(self._report_parser.getId(self._data_provider.lines[line]))

        return ids

    def _get_active_id(self):
        active_line = self._data_provider.lines[self._selection.active_line]

        return self._report_parser.getId(active_line)

    def task_add(self):
        print('cancel  :  - or empty')
        print()
        parameters = input('task add: ')

        if parameters in ['', '-']:
            return

        self._binary_wrapper.add(parameters.split(' '))

        console.wait()

    def task_annotate(self):
        id = self._get_active_id()

        print('cancel  :  - or empty')
        print()
        annotation = input('task {} annotate: '.format(id))

        if annotation in ['', '-']:
            return

        self._binary_wrapper.annotate(id, annotation.split(' '))

        console.wait()


    def task_note(self):
        id = self._get_active_id()

        from subprocess import run

        cmdline = f'tasknote {id} e'.split(' ')

        run(cmdline)

        console.wait()


    def task_done(self):
        ids = self._get_selected_ids()

        self._binary_wrapper.done(ids)

        console.wait()

    def task_view(self):
        ids = self._get_selected_ids()

        self._binary_wrapper.view(ids)

        console.wait()

    def task_mod(self):
        ids = self._get_selected_ids()

        print('cancel  :  - or empty')
        print()
        parameters = input('task {} mod: '.format(ids))

        if parameters in ['', '-']:
            return

        self._binary_wrapper.mod(ids, parameters.split(' '))

        console.wait()

    def set_filter(self):
        self._show_filter_headers()

        new_filters = input('Enter new filters: ')

        self._set_filter(new_filters, append=False)

    def append_filter(self):
        self._show_filter_headers()

        new_filters = input('Enter filters to append: ')

        self._set_filter(new_filters, append=True)

    def _show_filter_headers(self):
        print('Current filter: "{}"'.format(', '.join(self.filters) if self.filters else None))
        print()
        print('cancel  :  -')
        print('clear   :  empty')
        print()

    def _set_filter(self, new_filters, append=False):
        if new_filters == '-':
            return
        elif new_filters == '':
            self.filters = None
        elif append and self.filters:
            self.filters += new_filters.split(' ')
        else:
            self.filters = new_filters.split(' ')

        self._update_menu_title()

        self._binary_wrapper.invalidate_data()

    def _update_menu_title(self):
        context = f'Context: {self.context}; ' if (self.context and self.context != 'none') else ''

        report = f'Report: {self.report}; ' if self.report else ''

        filters = f'Filter: {" ".join(self.filters)}; ' if self.filters else ''

        if len(self._data_provider.lines) > 1:
            task_count = self._data_provider.lines[-2]
        else:
            task_count = 'no tasks'

        title_line = f'{context}{report}{filters}{task_count}'

        console.set_terminal_title(f'iTask: {title_line}')

        self.main_menu.title = f'{title_line}'

    def task_del(self):
        ids = self._get_selected_ids()

        print('cancel  :  -')
        print()
        comment = input('task {} delete comment: '.format(', '.join(str(id) for id in ids)))

        if comment == '-':
            return

        print('')

        self._binary_wrapper.delete(ids, comment)

        console.wait()

    def task_undo(self):
        self._binary_wrapper.undo()

        console.wait()

    def task_reload(self):
        print('Reloading data...')

        self._binary_wrapper.invalidate_data()

        console.wait()

    def task_sync(self):
        print('Sync command...')

        self._binary_wrapper.sync()

        console.wait()

    def select_report(self):
        reports = self._binary_wrapper.reports()

        # TODO Duplicated code
        ignored_reports = (self._binary_wrapper.get_config('itask.ignored_reports') or '').split(',')

        valid_reports = dict((report, description) for report, description in reports.items() if report not in ignored_reports)

        largest_name = -1

        for len_report in [ len(report) for report in valid_reports.keys()]:
            if len_report > largest_name:
                largest_name = len_report

        for report, description in valid_reports.items():
            alignment = ' ' * (largest_name - len(report))
            print(f'{report}{alignment}  {description}')

        print()
        print()
        print('cancel  :  - or empty')
        print()
        new_report = input('Enter new report name: ')

        if new_report in ['', '-']:
            return
        else:
            self.report = new_report

        self._binary_wrapper.invalidate_data()

    def select_context(self):
        # FIXME Não vai mostrar nada em tela, será necessário imprimir manualmente isso
        self._binary_wrapper.contexts()
        print()
        print(f'Current context: {self.context}')
        print()
        print('cancel              :  -')
        print('use global context  :  empty')
        print('unset               :  "none"')
        print()
        new_context = input('Enter new context: ')

        if new_context == '-':
            return
        elif new_context == '':
            self.context = None
        else:
            self.context = new_context

        self._binary_wrapper.invalidate_data()

    def show_projects(self):
        self._binary_wrapper.projects()

        console.wait()

    def show_tags(self):
        self._binary_wrapper.tags()

        console.wait()

    # Navigation
    def activate_next(self):
        super(MainMenu, self).activate_next()

        self._selection.move('down', 1)

    def activate_previous(self):
        super(MainMenu, self).activate_previous()

        self._selection.move('up', 1)

    def viewer_down(self):
        super(MainMenu, self).viewer_down()

        self._data_viewer.region.move('down', 1)
        self._left_viewer.region.move('down', 1)

    def viewer_up(self):
        super(MainMenu, self).viewer_up()

        self._data_viewer.region.move('up', 1)
        self._left_viewer.region.move('up', 1)

    def activate_first(self):
        super(MainMenu, self).activate_first()
        self._data_viewer.region.move('top')
        self._left_viewer.region.move('top')

    def activate_last(self):
        super(MainMenu, self).activate_last()
        self._data_viewer.region.move('bottom')
        self._left_viewer.region.move('bottom')

    def viewer_left(self):
        super(MainMenu, self).viewer_left()
        self._data_viewer.region.move('left', 1)
        self._header_viewer.region.move('left', 1)

    def viewer_right(self):
        super(MainMenu, self).viewer_right()
        self._data_viewer.region.move('right', 1)
        self._header_viewer.region.move('right', 1)

    def viewer_begin(self):
        super(MainMenu, self).viewer_begin()
        self._data_viewer.region.move('begin')
        self._header_viewer.region.move('begin')

    def viewer_end(self):
        super(MainMenu, self).viewer_end()
        self._data_viewer.region.move('end')
        self._header_viewer.region.move('end')

    # Selection
    def toggle_selected(self):
        super(MainMenu, self).toggle_selected()

        self._selection.toggle_active_line_selected()


def parse_command_line():
    parser = argparse.ArgumentParser()

    parser.add_argument('--task-data', help='Override TASKDATA environment variable')

    parser.add_argument('-r', '--report', default='next', help='Initial report')

    parser.add_argument('-f', '--filter', help='Initial filter')

    parser.add_argument('-c', '--context', help='Initial context')

    parser.add_argument('--rofi', action='store_true', help='Open rofi selection menu')

    return parser.parse_args()


def is_running_in_interactive_terminal():
    import os

    return os.isatty(1)


def recall_it_self_inside_terminal():
    import os
    terminal = os.getenv('TERMINAL', 'termite')

    import sys
    arguments = [arg.replace(' ', '\\ ') for arg in sys.argv]

    import subprocess
    subprocess.run([terminal, '-e', ' '.join(arguments)])


def main():
    args = parse_command_line()

    taskwarrior_wrapper = TaskwarriorWrapper(args.task_data)

    if args.rofi:
        import rofi

        rofi = rofi.Rofi()

        contexts = taskwarrior_wrapper.contexts()

        result = rofi.select(options=contexts, prompt='Context')[0]

        if result != -1:
            args.context = contexts[result]

        all_reports = taskwarrior_wrapper.reports()

        # TODO Duplicated code
        ignored_reports = (taskwarrior_wrapper.get_config('itask.ignored_reports') or '').split(',')

        reports = [report for report in all_reports.keys() if report not in ignored_reports]

        result = rofi.select(options=reports, prompt='Report')[0]

        if result != -1:
            args.report = reports[result]

    if not is_running_in_interactive_terminal():
        recall_it_self_inside_terminal()

        return

    handler = MainMenu(taskwarrior_wrapper, args)

    handler.run()


if __name__ == '__main__':
    main()
