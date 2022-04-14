#! /usr/bin/env python

"""
   Program:   EQ Alert
   File Name: eqa/lib/curses.py
   Copyright (C) 2022 Michael Geitz

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   You should have received a copy of the GNU General Public License along
   with this program; if not, write to the Free Software Foundation, Inc.,
   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import curses
import os
import sys
import time
import math
import pkg_resources

import eqa.lib.struct as eqa_struct
import eqa.lib.state as eqa_state
import eqa.lib.settings as eqa_settings


def display(stdscr, display_q, state, exit_flag):
    """
    Process: display_q
    Produce: display event
    """
    events = []
    debug_events = []
    page = "events"
    setting = "character"
    selected_char = 0

    try:
        while not exit_flag.is_set():
            time.sleep(0.01)
            if not display_q.empty():
                display_event = display_q.get()
                display_q.task_done()

                # Display Var Update
                if display_event.type == "update":
                    if display_event.screen == "setting":
                        setting = display_event.payload
                    elif display_event.screen == "selected_char":
                        selected_char = display_event.payload
                    elif display_event.screen == "select_char":
                        selected_char = display_event.payload
                        state.char = state.chars[selected_char]
                    elif display_event.screen == "zone":
                        zone = display_event.payload
                    elif display_event.screen == "char":
                        state.char = display_event.payload
                    draw_page(
                        stdscr,
                        page,
                        events,
                        debug_events,
                        state,
                        setting,
                        selected_char,
                    )

                # Display Draw
                elif display_event.type == "draw":
                    if display_event.screen != "redraw":
                        page = display_event.screen
                    draw_page(
                        stdscr,
                        page,
                        events,
                        debug_events,
                        state,
                        setting,
                        selected_char,
                    )

                # Draw Update
                elif display_event.type == "event":
                    if display_event.screen == "events":
                        events.append(display_event)
                        if page == "events":
                            draw_page(
                                stdscr,
                                page,
                                events,
                                debug_events,
                                state,
                                setting,
                                selected_char,
                            )
                    elif display_event.screen == "debug":
                        debug_events.append(display_event)
                        draw_page(
                            stdscr,
                            page,
                            events,
                            debug_events,
                            state,
                            setting,
                            selected_char,
                        )
                    elif display_event.screen == "clear":
                        events = []
                        debug_events = []
                        draw_page(
                            stdscr,
                            page,
                            events,
                            debug_events,
                            state,
                            setting,
                            selected_char,
                        )

    except Exception as e:
        eqa_settings.log(
            "display: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )

    sys.exit()


def draw_page(stdscr, page, events, debug_events, state, setting, selected_char):
    y, x = stdscr.getmaxyx()
    try:
        if x >= 80 and y >= 40:
            if page == "events":
                draw_events_frame(stdscr, state, events, debug_events)
            elif page == "state":
                draw_state(stdscr, state)
            elif page == "settings":
                draw_settings(stdscr, state, setting, selected_char)
            elif page == "help":
                draw_help(stdscr)
        else:
            draw_toosmall(stdscr)
    except Exception as e:
        eqa_settings.log(
            "draw_page: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def init(state):

    try:
        """Create new stdscr in terminal"""
        stdscr = curses.initscr()
        os.system("setterm -cursor off")
        curses.start_color()
        curses.use_default_colors()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(1)
        stdscr.timeout(100)
        curses.init_pair(1, curses.COLOR_WHITE, -1)  # Title
        curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Header
        curses.init_pair(3, curses.COLOR_CYAN, -1)  # Subtext
        curses.init_pair(4, curses.COLOR_MAGENTA, -1)  # Highlight
        curses.init_pair(5, curses.COLOR_GREEN, -1)  # Dunno
        draw_events_frame(stdscr, state, [], [])
        return stdscr

    except Exception as e:
        eqa_settings.log(
            "draw init: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def close_screens(stdscr):
    """Terminate stdscr"""
    os.system("setterm -cursor on")
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()


def draw_tabs(stdscr, tab):
    """Draw top row tab selection"""

    try:
        y, x = stdscr.getmaxyx()
        center_y = int(y / 2)
        center_x = int(x / 2)

        # Bottom of tabs
        stdscr.addch(2, 0, curses.ACS_LTEE)
        stdscr.addch(2, x - 1, curses.ACS_RTEE)
        for c in range(x - 2):
            stdscr.addch(2, c + 1, curses.ACS_HLINE)

        # Events tab
        stdscr.addstr(1, 2, "1", curses.color_pair(3))
        stdscr.addstr(1, 3, ":", curses.color_pair(1))
        if tab == "events":
            stdscr.addstr(1, 5, "events", curses.color_pair(4))
        else:
            stdscr.addstr(1, 5, "events", curses.color_pair(2))
        stdscr.addch(0, 12, curses.ACS_TTEE)
        stdscr.addch(1, 12, curses.ACS_VLINE)
        stdscr.addch(2, 12, curses.ACS_BTEE)

        # State tab
        stdscr.addstr(1, 14, "2", curses.color_pair(3))
        stdscr.addstr(1, 15, ":", curses.color_pair(1))
        if tab == "state":
            stdscr.addstr(1, 17, "state", curses.color_pair(4))
        else:
            stdscr.addstr(1, 17, "state", curses.color_pair(2))
        stdscr.addch(0, 23, curses.ACS_TTEE)
        stdscr.addch(1, 23, curses.ACS_VLINE)
        stdscr.addch(2, 23, curses.ACS_BTEE)

        # Settings tab
        stdscr.addstr(1, x - 23, "3", curses.color_pair(3))
        stdscr.addstr(1, x - 22, ":", curses.color_pair(1))
        if tab == "settings":
            stdscr.addstr(1, x - 20, "settings", curses.color_pair(4))
        else:
            stdscr.addstr(1, x - 20, "settings", curses.color_pair(2))
        stdscr.addch(0, x - 25, curses.ACS_TTEE)
        stdscr.addch(1, x - 25, curses.ACS_VLINE)
        stdscr.addch(2, x - 25, curses.ACS_BTEE)

        # Help tab
        stdscr.addstr(1, x - 9, "4", curses.color_pair(3))
        stdscr.addstr(1, x - 8, ":", curses.color_pair(1))
        if tab == "help":
            stdscr.addstr(1, x - 6, "help", curses.color_pair(4))
        else:
            stdscr.addstr(1, x - 6, "help", curses.color_pair(2))
        stdscr.addch(0, x - 11, curses.ACS_TTEE)
        stdscr.addch(1, x - 11, curses.ACS_VLINE)
        stdscr.addch(2, x - 11, curses.ACS_BTEE)

        # Center title
        version = str(pkg_resources.get_distribution("eqalert").version)
        offset = math.ceil(len(version) / 2)
        stdscr.addstr(
            1, center_x - 4 - offset, "EQ ALERT " + version, curses.color_pair(2)
        )

    except Exception as e:
        eqa_settings.log(
            "draw tabs: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_events_frame(stdscr, state, events, debug_events):
    """Draw events"""

    try:
        # Clear and box
        stdscr.clear()
        stdscr.box()

        # Draw tabs
        draw_tabs(stdscr, "events")

        # Draw status
        draw_events_status_bar(stdscr, state)

        # Draw events panel
        draw_events(stdscr, events)

        # Draw lower panel
        if state.debug == "true":
            draw_events_debug(stdscr, debug_events)

    except Exception as e:
        eqa_settings.log(
            "draw events frame: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_events_status_bar(stdscr, state):
    """Draw events status bar"""

    try:
        y, x = stdscr.getmaxyx()
        center_y = int(y / 2)
        center_x = int(x / 2)

        # Draw status bar
        ## Top of stats bar
        stdscr.addch(center_y - 1, 0, curses.ACS_LTEE)
        stdscr.addch(center_y - 1, x - 1, curses.ACS_RTEE)
        for c in range(x - 2):
            stdscr.addch(center_y - 1, c + 1, curses.ACS_HLINE)

        ## Character
        stdscr.addstr(center_y, 2, state.char.title(), curses.color_pair(2))

        ## Guild
        if state.char_guild != "unavailable":
            stdscr.addstr(
                center_y,
                3 + len(state.char),
                state.char_guild.title(),
                curses.color_pair(2),
            )

        ## Level
        if state.char_level != "unavailable":
            stdscr.addstr(center_y + 1, 2, state.char_level, curses.color_pair(2))

        ## Class
        if state.char_class != "unavailable":
            stdscr.addstr(
                center_y + 1,
                3 + len(state.char_level),
                state.char_class.title(),
                curses.color_pair(2),
            )

        ## Zone
        if state.zone != "unavailable":
            stdscr.addstr(
                center_y,
                x - len(state.zone) - 2,
                state.zone.title(),
                curses.color_pair(2),
            )

        ## Direction
        if state.direction != "unavailable":
            stdscr.addstr(
                center_y + 1,
                x - len(state.direction) - 2,
                state.direction.title(),
                curses.color_pair(2),
            )

        ## Location
        if state.loc != ["0.00", "0.00", "0.00"]:
            offset = (
                len(state.direction)
                + len(str(state.loc[0]))
                + len(str(state.loc[1]))
                + len(str(state.loc[2]))
            )
            stdscr.addstr(
                center_y + 1,
                x - offset - 7,
                str(state.loc[0]) + ", " + str(state.loc[1]) + ", " + str(state.loc[2]),
                curses.color_pair(2),
            )

        ## Server
        offset = math.ceil(len(str(state.server)) / 2)
        stdscr.addstr(center_y, center_x - offset, state.server, curses.color_pair(2))

        ## Context
        if state.afk == "true":
            stdscr.addstr(center_y + 1, center_x - 1, "AFK", curses.color_pair(2))
        elif state.group == "false" and state.raid == "false":
            stdscr.addstr(center_y + 1, center_x - 2, "Solo", curses.color_pair(2))
        elif state.group == "true" and state.raid == "false":
            stdscr.addstr(center_y + 1, center_x - 3, "Group", curses.color_pair(2))
        elif state.raid == "true":
            stdscr.addstr(center_y + 1, center_x - 2, "Raid", curses.color_pair(2))

        ## Bottom of stats bar
        stdscr.addch(center_y + 2, 0, curses.ACS_LTEE)
        stdscr.addch(center_y + 2, x - 1, curses.ACS_RTEE)
        for c in range(x - 2):
            stdscr.addch(center_y + 2, c + 1, curses.ACS_HLINE)

    except Exception as e:
        eqa_settings.log(
            "draw events status bar: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_events(stdscr, events):
    """Draw events window component of events"""

    try:
        y, x = stdscr.getmaxyx()
        center_y = int(y / 2)
        event_win_y = center_y - 4
        event_win_x = x - 4
        eventscr = stdscr.derwin(event_win_y, event_win_x, 3, 2)
        eventscr.clear()

        count = 1
        max_event_string_x = event_win_x - 17
        while (count - 1) < event_win_y and count < len(events):
            event = events[-count]
            draw_ftime(eventscr, event.timestamp, event_win_y - count)
            eventscr.addch(event_win_y - count, 14, curses.ACS_VLINE)
            eventscr.addstr(
                event_win_y - count,
                16,
                str(event.payload)[:max_event_string_x],
                curses.color_pair(1),
            )
            count += 1

    except Exception as e:
        eqa_settings.log(
            "draw events: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_events_debug(stdscr, debug_events):
    """Draw events window component of events"""

    try:
        y, x = stdscr.getmaxyx()
        center_y = int(y / 2)
        debug_win_y = center_y - 4
        debug_win_x = x - 4
        debugscr = stdscr.derwin(debug_win_y, debug_win_x, center_y + 3, 2)
        debugscr.clear()

        count = 1
        max_debug_string_x = debug_win_x - 34
        while (count - 1) < debug_win_y and count < len(debug_events):
            event = debug_events[-count]
            line_type = event.payload[0]
            line = event.payload[1]
            debugscr.addstr(
                debug_win_y - count, 1, line_type[:29], curses.color_pair(3)
            )
            debugscr.addch(debug_win_y - count, 31, curses.ACS_VLINE)
            debugscr.addstr(
                debug_win_y - count,
                33,
                str(line)[:max_debug_string_x],
                curses.color_pair(1),
            )
            count += 1

    except Exception as e:
        eqa_settings.log(
            "draw debug events: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_ftime(stdscr, timestamp, y):
    """Draw formatted time for events"""
    try:
        h, m, second = timestamp.split(":")
        s, ms = second.split(".")

        stdscr.addstr(y, 1, h, curses.color_pair(3))
        stdscr.addstr(y, 3, ":", curses.color_pair(2))
        stdscr.addstr(y, 4, m, curses.color_pair(3))
        stdscr.addstr(y, 6, ":", curses.color_pair(2))
        stdscr.addstr(y, 7, s, curses.color_pair(3))
        stdscr.addstr(y, 9, ".", curses.color_pair(2))
        stdscr.addstr(y, 10, ms, curses.color_pair(3))

    except Exception as e:
        eqa_settings.log(
            "draw ftime: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_state(stdscr, state):
    """Draw state"""
    y, x = stdscr.getmaxyx()
    center_y = int(y / 2)
    center_x = int(x / 2)

    # Clear and box
    stdscr.clear()
    stdscr.box()

    # Draw tabs
    draw_tabs(stdscr, "state")

    # Show some state
    try:
        # server state
        stdscr.addstr(5, 5, "Server", curses.color_pair(2))
        stdscr.addstr(5, 16, ": ", curses.color_pair(1))
        stdscr.addstr(5, 18, state.server.title(), curses.color_pair(3))

        # char
        stdscr.addstr(6, 5, "Character", curses.color_pair(2))
        stdscr.addstr(6, 16, ": ", curses.color_pair(1))
        stdscr.addstr(6, 18, state.char.title(), curses.color_pair(3))

        # class
        stdscr.addstr(8, 5, "Class", curses.color_pair(2))
        stdscr.addstr(8, 16, ": ", curses.color_pair(1))
        stdscr.addstr(8, 18, state.char_class.title(), curses.color_pair(3))

        # level
        stdscr.addstr(9, 5, "Level", curses.color_pair(2))
        stdscr.addstr(9, 16, ": ", curses.color_pair(1))
        stdscr.addstr(9, 18, state.char_level.title(), curses.color_pair(3))

        # guild
        stdscr.addstr(10, 5, "Guild", curses.color_pair(2))
        stdscr.addstr(10, 16, ": ", curses.color_pair(1))
        stdscr.addstr(10, 18, state.char_guild.title(), curses.color_pair(3))

        # bind state
        stdscr.addstr(12, 5, "Bind", curses.color_pair(2))
        stdscr.addstr(12, 16, ": ", curses.color_pair(1))
        stdscr.addstr(12, 18, state.bind.title(), curses.color_pair(3))

        # encumbered state
        stdscr.addstr(13, 5, "Encumbered", curses.color_pair(2))
        stdscr.addstr(13, 16, ": ", curses.color_pair(1))
        stdscr.addstr(13, 18, state.encumbered.title(), curses.color_pair(3))

        # afk state
        stdscr.addstr(14, 5, "AFK", curses.color_pair(2))
        stdscr.addstr(14, 16, ": ", curses.color_pair(1))
        stdscr.addstr(14, 18, state.afk.title(), curses.color_pair(3))

        # group state
        stdscr.addstr(16, 5, "Group", curses.color_pair(2))
        stdscr.addstr(16, 16, ": ", curses.color_pair(1))
        stdscr.addstr(16, 18, state.group.title(), curses.color_pair(3))

        # leader state
        if state.group == "true":
            stdscr.addstr(16, 25, "Leader", curses.color_pair(2))
            stdscr.addstr(16, 32, ": ", curses.color_pair(1))
            stdscr.addstr(16, 34, state.leader.title(), curses.color_pair(3))

        # raid state
        stdscr.addstr(17, 5, "Raid", curses.color_pair(2))
        stdscr.addstr(17, 16, ": ", curses.color_pair(1))
        stdscr.addstr(17, 18, state.raid.title(), curses.color_pair(3))

        # zone
        stdscr.addstr(19, 5, "Zone", curses.color_pair(2))
        stdscr.addstr(19, 16, ": ", curses.color_pair(1))
        stdscr.addstr(19, 18, state.zone.title(), curses.color_pair(3))

        # loc
        stdscr.addstr(20, 5, "Location", curses.color_pair(2))
        stdscr.addstr(20, 16, ": ", curses.color_pair(1))
        stdscr.addstr(20, 18, str(state.loc[0]), curses.color_pair(3))
        stdscr.addstr(20, 24, " : ", curses.color_pair(2))
        stdscr.addstr(20, 26, str(state.loc[1]), curses.color_pair(3))
        stdscr.addstr(20, 32, " : ", curses.color_pair(2))
        stdscr.addstr(20, 34, str(state.loc[2]), curses.color_pair(3))

        # direction
        stdscr.addstr(21, 5, "Direction", curses.color_pair(2))
        stdscr.addstr(21, 16, ": ", curses.color_pair(1))
        stdscr.addstr(21, 18, state.direction.title(), curses.color_pair(3))

        # debug state
        stdscr.addstr(23, 5, "Debug", curses.color_pair(2))
        stdscr.addstr(23, 16, ": ", curses.color_pair(1))
        stdscr.addstr(23, 18, state.debug.title(), curses.color_pair(3))

        # mute state
        stdscr.addstr(24, 5, "Mute", curses.color_pair(2))
        stdscr.addstr(24, 16, ": ", curses.color_pair(1))
        stdscr.addstr(24, 18, state.mute.title(), curses.color_pair(3))

        # eqalert version
        version = str(pkg_resources.get_distribution("eqalert").version)
        stdscr.addstr(26, 5, "Version", curses.color_pair(2))
        stdscr.addstr(26, 16, ": ", curses.color_pair(1))
        stdscr.addstr(26, 18, version, curses.color_pair(3))

    except Exception as e:
        eqa_settings.log(
            "draw state: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_settings(stdscr, state, selected_setting, selected_char):
    """Draw settings"""

    try:
        # Clear and box
        stdscr.clear()
        stdscr.box()

        # Draw tabs
        draw_tabs(stdscr, "settings")

        # Draw chars
        if selected_setting == "character":
            stdscr.addstr(
                4, 3, "Character Selection", curses.A_UNDERLINE | curses.color_pair(2)
            )
        else:
            stdscr.addstr(4, 5, "Character Selection", curses.color_pair(3))
        stdscr.addstr(7 + len(state.chars), 5, "Active Character", curses.color_pair(3))
        stdscr.addstr(7 + len(state.chars), 21, ":", curses.color_pair(1))
        stdscr.addstr(
            7 + len(state.chars),
            23,
            state.char + " on " + state.server,
            curses.color_pair(2),
        )

        draw_chars(stdscr, state.chars, state.char, selected_char)

    except Exception as e:
        eqa_settings.log(
            "draw settings: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_chars(stdscr, chars, char, selected):
    """Draw character selection component for settings"""
    try:
        y, x = stdscr.getmaxyx()
        charscr_width = int(x / 3)
        # Pending general scrolling method
        charscr_height = len(chars) + 2

        charscr = stdscr.derwin(charscr_height, charscr_width, 5, 3)
        charscr.clear()
        charscr.box()

        count = 0
        while count < len(chars):
            char_name, char_server = chars[count].split("_")
            if selected == count:
                charscr.addstr(
                    len(chars) - count,
                    2,
                    char_name + " " + char_server,
                    curses.color_pair(1),
                )
            else:
                charscr.addstr(
                    len(chars) - count,
                    2,
                    char_name + " " + char_server,
                    curses.color_pair(2),
                )
            count += 1

    except Exception as e:
        eqa_settings.log(
            "draw chars: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_help(stdscr):
    """Draw help"""

    try:
        # Clear and box
        stdscr.clear()
        stdscr.box()

        # Draw tabs
        draw_tabs(stdscr, "help")

        # Commands
        stdscr.addstr(5, 5, "Commands:", curses.color_pair(1))

        # Global commands
        stdscr.addstr(7, 7, "Global", curses.color_pair(1))

        stdscr.addstr(8, 9, "1", curses.color_pair(2))
        stdscr.addstr(8, 15, ":", curses.color_pair(1))
        stdscr.addstr(8, 17, "Events", curses.color_pair(3))

        stdscr.addstr(9, 9, "2", curses.color_pair(2))
        stdscr.addstr(9, 15, ":", curses.color_pair(1))
        stdscr.addstr(9, 17, "State", curses.color_pair(3))

        stdscr.addstr(10, 9, "3", curses.color_pair(2))
        stdscr.addstr(10, 15, ":", curses.color_pair(1))
        stdscr.addstr(10, 17, "Settings", curses.color_pair(3))

        stdscr.addstr(11, 9, "4", curses.color_pair(2))
        stdscr.addstr(11, 15, ":", curses.color_pair(1))
        stdscr.addstr(11, 17, "Help", curses.color_pair(3))

        stdscr.addstr(12, 9, "q", curses.color_pair(2))
        stdscr.addstr(12, 15, ":", curses.color_pair(1))
        stdscr.addstr(12, 17, "Quit", curses.color_pair(3))

        stdscr.addstr(13, 9, "0", curses.color_pair(2))
        stdscr.addstr(13, 15, ":", curses.color_pair(1))
        stdscr.addstr(13, 17, "Reload config", curses.color_pair(3))

        # Events commands
        stdscr.addstr(15, 7, "Events", curses.color_pair(1))

        stdscr.addstr(16, 9, "c", curses.color_pair(2))
        stdscr.addstr(16, 15, ":", curses.color_pair(1))
        stdscr.addstr(16, 17, "Clear events", curses.color_pair(3))

        stdscr.addstr(17, 9, "r", curses.color_pair(2))
        stdscr.addstr(17, 15, ":", curses.color_pair(1))
        stdscr.addstr(17, 17, "Toggle raid mode", curses.color_pair(3))

        stdscr.addstr(18, 9, "d", curses.color_pair(2))
        stdscr.addstr(18, 15, ":", curses.color_pair(1))
        stdscr.addstr(18, 17, "Toggle debug modes", curses.color_pair(3))

        stdscr.addstr(19, 9, "m", curses.color_pair(2))
        stdscr.addstr(19, 15, ":", curses.color_pair(1))
        stdscr.addstr(19, 17, "Toggle mute", curses.color_pair(3))

        # Settings commands
        stdscr.addstr(21, 7, "Settings", curses.color_pair(1))

        stdscr.addstr(22, 9, "up", curses.color_pair(2))
        stdscr.addstr(22, 15, ":", curses.color_pair(1))
        stdscr.addstr(22, 17, "Cycle up in selection", curses.color_pair(3))

        stdscr.addstr(23, 9, "down", curses.color_pair(2))
        stdscr.addstr(23, 15, ":", curses.color_pair(1))
        stdscr.addstr(23, 17, "Cycle down in selection", curses.color_pair(3))

        stdscr.addstr(24, 9, "right", curses.color_pair(2))
        stdscr.addstr(24, 15, ":", curses.color_pair(1))
        stdscr.addstr(24, 17, "Toggle selection on", curses.color_pair(3))

        stdscr.addstr(25, 9, "left", curses.color_pair(2))
        stdscr.addstr(25, 15, ":", curses.color_pair(1))
        stdscr.addstr(25, 17, "Toggle selection off", curses.color_pair(3))

        stdscr.addstr(26, 9, "space", curses.color_pair(2))
        stdscr.addstr(26, 15, ":", curses.color_pair(1))
        stdscr.addstr(26, 17, "Cycle selection", curses.color_pair(3))

    except Exception as e:
        eqa_settings.log(
            "draw help: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


def draw_toosmall(stdscr):
    """Draw too small warning"""

    try:
        stdscr.clear()
        stdscr.box()
        y, x = stdscr.getmaxyx()
        center_y = int(y / 2)
        center_x = int(x / 2)

        stdscr.addstr(
            center_y, center_x - 10, "Terminal too small.", curses.color_pair(1)
        )

    except Exception as e:
        eqa_settings.log(
            "draw too small: Error on line "
            + str(sys.exc_info()[-1].tb_lineno)
            + ": "
            + str(e)
        )


if __name__ == "__main__":
    main()
