#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
from viewer import Viewer, Region
from selection import Selection
import console
from taskwarriorwrapper import TaskwarriorWrapper
from imenu import Menu, MenuItem, Navigable, BackMenuItem
from dataprovider import DataProvider
from taskwarriorreportparser import TaskwarriorReportParser
import io


class MainMenu(Navigable):

    def __init__(self):
        super(MainMenu, self).__init__()

        self.filter = None

        self._binary_wrapper = TaskwarriorWrapper()

        self._binary_wrapper.register_listener('data changed', self._data_changed)

        self._data_provider = DataProvider()

        self._report_parser = TaskwarriorReportParser()

        self._first_usable_line = 1

        self._do_data_update()

        self._make_menu()

        self._make_gui()

    def _make_menu(self):
        self.main_menu = Menu(title='Main Menu', back=False)

        self.main_menu.items.append(MenuItem(title='Add', hotkey='a', action=self.task_add))
        self.main_menu.items.append(MenuItem(title='Annotate', hotkey='n', action=self.task_annotate))
        self.main_menu.items.append(MenuItem(title='Done', hotkey='o', action=self.task_done))
        self.main_menu.items.append(MenuItem(title='View', hotkey='v', action=self.task_view))
        self.main_menu.items.append(MenuItem(title='Mod', hotkey='m', action=self.task_mod))
        self.main_menu.items.append(MenuItem(title='Filter', hotkey='f', action=self.task_filter))
        self.main_menu.items.append(MenuItem(title='Delete', hotkey='d', action=self.task_del))
        self.main_menu.items.append(MenuItem(title='Undo', hotkey='u', action=self.task_undo))
        self.main_menu.items.append(MenuItem(title='Sync', hotkey='s', action=self.task_sync))
        #self.main_menu.items.append(MenuItem(title='Unfilter', hotkey='x', action=self._binary_wrapper.clean_filter))
        #self.main_menu.items.append(MenuItem(title='Report', hotkey='r', action=self._binary_wrapper.select_report))

        self.main_menu.append_quit(self._quit)

        self.main_menu.append_navigation_keys(self)

        self.main_menu.register_listener('render', self.render)
        self.main_menu.register_listener('item chosen', self.item_chosen)
        self.main_menu.register_listener('after action', self.after_action)

    def _make_gui(self):
        fixed_left = 9
        fixed_top = 2
        menu_height = 1
        footer_height = 2

        fixed_region = Region(size={'width': fixed_left, 'height': fixed_top}, position={'left': 0, 'top': self._first_usable_line})

        self._fixed_viewer = Viewer(self._data_provider, fixed_region, screen_left=0, screen_top=0)

        terminal_size = shutil.get_terminal_size()

        data_width = terminal_size.columns - fixed_left - 1
        data_horizontal_constraints = {'left': fixed_left, 'right': self._data_provider.size.largest_line}
        header_region = Region(
            size={'width': data_width, 'height': fixed_top},
            position={'left': fixed_left, 'top': self._first_usable_line},
            horizontal_constraints=data_horizontal_constraints)

        self._header_viewer = Viewer(self._data_provider, header_region, screen_left=fixed_left, screen_top=0)

        data_height = terminal_size.lines - fixed_top - menu_height
        data_vertical_constraints = {'top': self._first_usable_line + fixed_top, 'bottom': self._data_provider.size.lines - footer_height}

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
        stream = self._binary_wrapper.load(self.filter)

        file = io.TextIOWrapper(stream)

        self._data_provider.update(file)

        file.close()

        self._report_parser.set_header_line(self._data_provider.lines[self._first_usable_line])

    def _data_changed(self, origin):
        self._do_data_update()

        self._selection.clear()

    def render(self, origin):
        console.change_cursor_visibility(False)
        console.change_getch_echo(False)

        self._fixed_viewer.update()
        self._header_viewer.update()
        self._left_viewer.update()
        self._data_viewer.update()

    def item_chosen(self, origin, item):
        if item.interactive:
            console.change_cursor_visibility(True)
            console.change_getch_echo(True)

            console.clear_screen()

            self._fixed_viewer.invalidate()
            self._header_viewer.invalidate()
            self._left_viewer.invalidate()
            self._data_viewer.invalidate()

    def after_action(self, origin, item):
        if item and item.interactive:
            console.change_cursor_visibility(True)
            console.change_getch_echo(True)

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
        new_filter = input("Enter new filter [::cancel for cancel, empty for clear]: ")

        if new_filter == '::cancel':
            return

        self.filter = new_filter

        if self.filter:
            self.main_menu.title = 'Main Menu (filter=\'{}\')'.format(self.filter)
        else:
            self.main_menu.title = 'Main Menu'

        self._binary_wrapper.invalidate_data()

    def task_del(self):
        menu = Menu("Are you sure you want to remove ids '{}'?".format(str(self._get_selected_ids())), redraw=False, back=False)

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


if __name__ == '__main__':
    handler = MainMenu()

    handler.run()
