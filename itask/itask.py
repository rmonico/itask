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


class MainMenu(Navigable):

    def __init__(self, taskwarrior_wrapper, args):
        super(MainMenu, self).__init__()

        self.report = args.report

        self.filters = args.filter.split(" ") if args.filter else None

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
        self.main_menu.items.append(MenuItem(title='Done', hotkey='O', action=self.task_done))
        self.main_menu.items.append(MenuItem(title='View', hotkey='v', action=self.task_view))
        self.main_menu.items.append(MenuItem(title='Mod', hotkey='m', action=self.task_mod))
        self.main_menu.items.append(MenuItem(title='Filter', hotkey='f', action=self.task_filter))
        self.main_menu.items.append(MenuItem(title='Delete', hotkey='D', action=self.task_del))
        self.main_menu.items.append(MenuItem(title='Undo', hotkey='U', action=self.task_undo))
        self.main_menu.items.append(MenuItem(title='Reload', hotkey='R', action=self.task_reload))
        self.main_menu.items.append(MenuItem(title='Sync', hotkey='S', action=self.task_sync))
        # self.main_menu.items.append(MenuItem(title='Unfilter', hotkey='x', action=self._binary_wrapper.clean_filter))
        # self.main_menu.items.append(MenuItem(title='Report', hotkey='r', action=self._binary_wrapper.select_report))

        self.main_menu.append_quit(self._quit)

        self.main_menu.append_navigation_keys(self)

        self.main_menu.register_listener('render', self.render)
        self.main_menu.register_listener('item chosen', self.item_chosen)
        self.main_menu.register_listener('after action', self.after_action)

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
        parameters = input("task add [empty for cancel]: ")

        if parameters == '':
            return

        self._binary_wrapper.add(parameters.split(' '))

        console.wait()

    def task_annotate(self):
        id = self._get_active_id()

        annotation = input("task {} annotate [empty for cancel]: ".format(id))

        if annotation == '':
            return

        self._binary_wrapper.annotate(id, annotation.split(' '))

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

        parameters = input("task {} mod [empty for cancel]: ".format(ids))

        if parameters == '':
            return

        self._binary_wrapper.mod(ids, parameters.split(' '))

        console.wait()

    def task_filter(self):
        new_filters = input("Enter new filters [::cancel for cancel, empty for clear]: ")

        if new_filters == '::cancel':
            return
        elif new_filters == '':
            self.filters = None
        else:
            self.filters = new_filters.split(" ")

        self._update_menu_title()

        self._binary_wrapper.invalidate_data()

    def _update_menu_title(self):
        if self.filters:
            filters = ' and '.join(self.filters)
        else:
            filters = ''

        if len(self._data_provider.lines) > 1:
            task_count = self._data_provider.lines[-2]
        else:
            task_count = 'no tasks'

        console.set_terminal_title('iTask [{}{}{}]'.format(filters, '' if not filters else '; ', task_count))

        filter_string = '; filter=' + filters if self.filters else ''

        self.main_menu.title = 'Main Menu{}; {}'.format(filter_string, task_count)

    def task_del(self):
        menu = Menu("Are you sure you want to remove ids '{}'?".format(str(self._get_selected_ids())), redraw=False,
                    back=False)

        menu.items.append(BackMenuItem("y", "Yes", action=self._delete_confirmed))
        menu.items.append(BackMenuItem("n", "No"))

        menu.run()

    def _delete_confirmed(self):
        ids = self._get_selected_ids()

        print('')

        self._binary_wrapper.delete(ids)

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

    parser.add_argument("--task-data", help="Override TASKDATA environment variable")

    parser.add_argument("-r", "--report", help="Initial report")

    parser.add_argument("-f", "--filter", help="Initial filter")

    parser.add_argument("-c", "--context", help="Initial context")

    return parser.parse_args()


def is_running_in_interactive_terminal():
    import os

    return os.isatty(1)


def recall_it_self_inside_terminal():
    import os
    terminal = os.getenv("TERMINAL", "termite")

    import sys
    arguments = [arg.replace(" ", "\\ ") for arg in sys.argv]

    import subprocess
    subprocess.run([terminal, "-e", " ".join(arguments)])


def main():
    if not is_running_in_interactive_terminal():
        recall_it_self_inside_terminal()

        return

    args = parse_command_line()

    handler = MainMenu(TaskwarriorWrapper(args.task_data), args)

    handler.run()


if __name__ == '__main__':
    main()
