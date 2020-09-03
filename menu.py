import os
import sys
import inspect
import types
import numpy as np


ROOT_DIRECTORY = 'data-utility'
PROJECT_DIRECTORY = 'projects'
SEPARATOR_LENGTH = 80


# import all python modules in the root directory
for (root, dirs, files) in os.walk(ROOT_DIRECTORY):
    if '__pycache__' not in root and len(files) != 0:
        sys.path.append(root)
        for f in files:
            if f.endswith('.py'):
                import_str = f'import {f[:-3]}'
                exec(import_str)


def separator():
    return "-" * SEPARATOR_LENGTH + "\n"


def menu_print_none(to_print):
    """
    If string is None, then don't print None
    """
    if to_print is None:
        return ""
    else:
        return f"  {to_print}\n"


def change_project(proj):
    """
    Change the global variable for the current project directory
    """
    global current_project_directory
    global current_menu
    current_project_directory = f"{PROJECT_DIRECTORY}/{proj}"
    current_menu = menu_store[ROOT_DIRECTORY]
    print(current_menu)


def change_current_menu(menu_key):
    """
    Change the global variable for the current menu
    """
    global current_menu
    if menu_key == 'EXIT_MENU':
        menu_store['EXIT_MENU'].most_recent_menu_key = current_menu.path
    current_menu = menu_store[menu_key]
    # print(current_menu)


class Menu:
    """
    Menu object

    Extended description of function.

    Attributes
    ----------
    title : str
    subtitle : str
    description : str
    options : dict
        Dictionary of (name, number) : function  for a user to call
    parent : Menu
        If parent is null, then the Menu is assumed to be the root Menu..........
    """
    def __init__(self, parent, path, options, title=None, subtitle=None, description=None):
        self.title = title
        self.subtitle = subtitle
        self.description = description
        self.parent = parent
        self.path = path

        if self.assertTrue(issubclass(ExitMenu, Menu)):
            options_count = max((t[0] for t in options.keys()))
            options[(int(options_count) + 1, 'GO_BACK')] = change_current_menu
        self.options = options

    def __len__(self):
        return len(self.options)

    def __str__(self):
        # options_text = ""
        # for i, opt in enumerate(self.options.keys(), start=1):
        #     options_text += f"  {i} - {opt}\n"

        prompt = f"{menu_print_none(self.parent)}{menu_print_none(self.path)}{menu_print_none(self.title)}{menu_print_none(self.subtitle)}" \
                 f"{menu_print_none(self.description)}\n{self.options}\n"

        return separator() + prompt + separator()

    def selection(self, select):
        """
        User selects a number, change the menu

        Parameters
        ----------
        select : int
            Integer from user selection
        """
        # if select == 99:
        #     # figure out what to do with the exit screen
        #     menu_store['EXIT_MENU'].most_recent_menu_key = current_menu
        #     change_current_menu('EXIT_MENU')

        for key, value in self.options.items():
            if select == key[0]:
                selected_function = self.options[(key[0], key[1])]
                selected_text = key[1]
                print(selected_function, selected_text)

                if type(selected_function) == str:
                    change_current_menu(f"{self.path}/{selected_function}")
                elif key[1] == 'GO_BACK':   # and selected_function == change_current_menu:
                    change_current_menu(self.parent)
                elif selected_function == change_project:
                    change_project(selected_text)
                elif selected_function == ExitMenu.go_back_exit:
                    change_current_menu(menu_store['EXIT_MENU'].most_recent_menu_key)
                else:
                    selected_function()
        # else:
        #     print("Selection not found on current menu. Try again.")


class ProjectMenu(Menu):
    def __init__(self):
        _title = "Select a Project"
        _description = "Choose a project to load from your project directory:"
        projects = {}

        for (root, dirs, files) in os.walk(PROJECT_DIRECTORY):
            projects = {(c, d): change_project for c, d in enumerate(dirs, start=1) if d != '__pycache__'}
            break

        if projects == {}:
            print("No projects found. Please add them and restart the program.")
            sys.exit()

        super().__init__(parent="EXIT_MENU", path="PROJECT_MENU", options=projects, title=_title,
                         description=_description)


class ExitMenu(Menu):
    """
    Exit confirmation menu
    """
    def __init__(self):
        self.most_recent_menu_key = ROOT_DIRECTORY
        _title = "Are you sure you want to exit?"
        yes_no = {(1, 'yes'): sys.exit, (2, 'no'): self.go_back_exit}

        super().__init__(parent="END", path="EXIT_MENU", options=yes_no, title=_title)

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def go_back_exit(self):
        change_current_menu(self.most_recent_menu_key)


class MenuStore:
    """
    Store all menus as path: Menu pairs
    """
    def __init__(self):
        self.menus = {}

    def __getitem__(self, item):
        try:
            return self.menus[item]
        except KeyError:
            print(item)
            print("Menu connection error")

    def __setitem__(self, key, value):
        self.menus[key] = value

    def print_all(self):
        for value in self.menus.values():
            print(value)


def scan(module):
    """
    Scan the file path for functions in a specific module

    Parameters
    ----------
    module : str
        Module name

    Returns
    -------
    contained_func : tuple
        (function string, function) pairs
    """
    options_dict = {name: value for (name, value) in inspect.getmembers(sys.modules[module],
            predicate=lambda obj: isinstance(obj, types.FunctionType))}

    return {(c, d[0]): d[1] for c, d in enumerate(options_dict.items(), start=1)}


def index_ignore_error(text, sub, is_start):
    """
    Find the index of a particular substring without raising a ValueError if the substring isn't found

    Parameters
    ----------
    text : str
        Text string to search
    sub : str
        Substring to search for
    is_start : bool
        Searching for the start (True) or end (False) of a string to crop

    Returns
    -------
    index : int
        Index of substring, returns np.nan if substring not found
    """
    try:
        return text.index(sub)
    except ValueError:
        if not is_start:
            return -1
        else:
            return np.nan


def extract_menu_text(docstring):
    """
    Return string from docstring or None if not found
    """
    search = {"Title:": None, "Subtitle:": None, "Description:": None}

    for search_string in search.keys():
        start_index = index_ignore_error(docstring, search_string, True) + len(search_string)

        if not np.isnan(start_index):
            end_index = index_ignore_error(docstring[start_index:], '\n', False)
            if end_index == -1:
                search[search_string] = docstring[start_index:].strip()
            else:
                search[search_string] = docstring[start_index:(end_index+start_index)].strip()

    return search


# initialize menu state
current_project_directory = PROJECT_DIRECTORY
current_menu = 'TBD'
menu_store = MenuStore()


def generate_menus():
    """
    Generates all menus based on project and utility files and directories
    """
    global menu_store
    menu_store['PROJECT_MENU'] = ProjectMenu()
    menu_store['EXIT_MENU'] = ExitMenu()

    for (root, dirs, files) in os.walk(ROOT_DIRECTORY):
        if '__pycache__' not in root and len(files) != 0:

            # print(root)
            # print(dirs)
            # print(files)

            # for folder arguments
            folder_options = {}
            folder_options_count = 1
            folder_search_results = {"Title:": None, "Subtitle:": None, "Description:": None}

            for f in files:
                # make python menus
                if f.endswith('.py'):

                    module_name = f[:-3]

                    # for folder options
                    folder_options[(folder_options_count, module_name)] = f
                    folder_options_count += 1

                    # print(scan(module_name))
                    module_docstring = sys.modules[module_name].__doc__
                    current_path = f"{root}/{f}"

                    if module_docstring is not None:
                        file_search_results = extract_menu_text(module_docstring)

                        menu_store[current_path] = Menu(parent=root, path=current_path, options=scan(module_name),
                                                   title=file_search_results["Title:"],
                                                   subtitle=file_search_results["Subtitle:"],
                                                   description=file_search_results["Description:"])
                    else:
                        menu_store[current_path] = Menu(parent=root, path=current_path, options=scan(module_name))

                # make folder text
                elif f.endswith('.txt'):
                    file_name = f[:-4]
                    if root != ROOT_DIRECTORY:
                        folder_name = root[root.rindex('/') + 1:]
                    else:
                        folder_name = ROOT_DIRECTORY

                    if file_name == folder_name:
                        with open(f"{root}/{f}", 'r') as file:
                            folder_string = file.read()
                        folder_search_results = extract_menu_text(folder_string)

            for d in dirs:
                if d != '__pycache__':
                    folder_options[(folder_options_count, d)] = d
                    folder_options_count += 1

            # make folder menus
            if root != ROOT_DIRECTORY:
                folder_parent = root[:root.rindex("/")]
            else:
                folder_parent = 'PROJECT_MENU'

            menu_store[root] = Menu(parent=folder_parent, path=root, options=folder_options,
                                        title=folder_search_results["Title:"],
                                        subtitle=folder_search_results["Subtitle:"],
                                        description=folder_search_results["Description:"])


if __name__ == "__main__":
    generate_menus()
    current_menu = menu_store['PROJECT_MENU']
    # menu_store.print_all()

    while current_menu != 'SHUT_DOWN':
        print(current_menu)

        try:
            choice = int(input("> "))
        except ValueError:
            print("Not a valid integer. Try again!")
            continue

        current_menu.selection(choice)
