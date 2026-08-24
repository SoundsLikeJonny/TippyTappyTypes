#      Tippy Tappy Types is a minimal typing test software that sits in the corner of your screen while you work!
#      Copyright (C) 2026 Jon Evans
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

import dataclasses
import os
import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """Return the absolute path to a resource.

    Works both in development (project root) and in a PyInstaller frozen build
    (where resources are extracted to sys._MEIPASS).
    """
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = str(Path(__file__).parent.resolve())
    return os.path.join(base, relative_path)


@dataclasses.dataclass
class Info:
    NOTIFICATION_TIME: int = 50
    PROJECT_TITLE: str = 'TippyTappyTypes'
    COMPANY: str = 'Jon Evans. Art by Cafefaevans'
    COPYRIGHT: str = 'Copyright (c) Jon Evans 2026'
    NOTICE: str = 'Tiny but powerful!'
    RESOURCES_PATH: str = 'resources'
    ICON_PATH: str = f'{RESOURCES_PATH}/favicon.ico'
    SPLASH_PATH: str = f'{RESOURCES_PATH}/splash.PNG'
    DOCS_LINK: str = ''
    VERSION: str = '0.1.0-beta.23'
    GITHUB_REPO: str = 'SoundsLikeJonny/TippyTappyTypes'



@dataclasses.dataclass
class FileTypes:
    PROJECT: str = '.tiny'
    DATA: str = '.tinydata'
    PREFS: str = '.tinyprefs'

    ALL_TYPES: tuple = (
        PROJECT,
        DATA,
        PREFS
    )

    @staticmethod
    def is_type_in_file(file: str):
        for extension in FileTypes.ALL_TYPES:
            if file.endswith(extension):
                return True
        return False
