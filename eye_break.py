import math
import os
import tkinter
import tkinter.ttk
import json
import subprocess as sp
"""
This is a program to tell you when to take a break from looking at the computer screen.
Copyright (C) 2019 Maciej Marciniak

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>."""
if os.name == 'nt':
    import ctypes
elif os.name == 'posix':
    import shlex
else:
    force_disable_screensaver = True
    print('[WARN] Cannot enable screensaver compatibility: os.name == {}'.format(os.name))

try:
    import playsound
except ImportError:
    playsound = False
    print('[INFO] Disabling playing sounds. `playsound` is not installed.')
if __name__ != '__main__':
    raise ImportError

CONFIG_DEFAULT = {
    'text_break_in': 'Next eye break in {0: >2}:{1:0>2}',
    'text_break_now': 'Take an eye-break.',
    'text_title': '{}EyeBreak',
    'text_title_paused': '[PAUSED]',
    'text_button_pause': 'Pause',
    'text_button_unpase': 'Unpause',

    'time_break_after': 3600,
    'time_break_time': 60,

    'option_always_on_top': True,
    'option_on_top_paused': False,
    'option_popup_offset': (0, 0),
    'option_lock_screen': False,
    'option_lock_screen_command': 'gnome-screensaver-command --lock',
    'option_lock_screen__comment': 'This is only used on linux, since there is a lot of screensavers.',
    'option_lock_screen_command_unlock': 'gnome-screensaver-command --unlock',
    'option_minimize_counting_down': True,

    'sound_break_start': 'break_start.wav',
    'sound_break_end': 'break_end.wav'
}
CONFIG_FILENAME = 'eyebreak_config.json'
try:
    config = CONFIG_DEFAULT.copy()
    with open(CONFIG_FILENAME, 'r') as f:
        config_from_file = json.load(f)
    save_config = False
    for k in config:
        if k not in config_from_file:
            save_config = True
    config.update(config_from_file)
    if save_config:
        with open(CONFIG_FILENAME, 'w') as f:
            json.dump(config, f, sort_keys=True, indent=2)
            print('**config saved**')

except FileNotFoundError:
    with open(CONFIG_FILENAME, 'w') as f:
        json.dump(CONFIG_DEFAULT, f, sort_keys=True, indent=2)
    config = CONFIG_DEFAULT.copy()


def lock_screen():
    if not config['option_lock_screen']:
        return
    if os.name == 'posix':
        proc = sp.Popen(shlex.split(config['option_lock_screen_command']))
        proc.wait()
    elif os.name == 'nt':
        ctypes.windll.user32.LockWorkStation()


break_in = 0
screen_size = (0, 0)


class App(tkinter.Frame):
    def __init__(self, *args, **kwargs):
        global break_in
        super().__init__(*args, **kwargs)
        break_in = config['time_break_after']
        self.paused = False
        self.progress_bar = tkinter.ttk.Progressbar(self)
        # self.progress_bar.pack({'side': 'top'})
        self.label = tkinter.Label(self, font='TkFixedFont')
        self.pause_button = tkinter.Button(self, text='Pause', command=self.pause)
        # self.label.pack()
        self.screen_size = (self.master.winfo_screenwidth(), self.master.winfo_screenheight())
        print(self.screen_size)
        break_in += 1
        self.repack()
        # self.wait_for_break()
        self.update()
        self.after(5, lambda *a: self.master.wm_minsize(self.winfo_width(), self.winfo_height()))
        self.after(5, lambda *a: self.master.wm_maxsize(self.winfo_width(), self.winfo_height()))
        if config['option_always_on_top']:
            self.master.attributes('-topmost', True)
        self.pause_button.focus()
        self.after(10, lambda *a: (self.master.wm_state('iconic') if config['option_minimize_counting_down'] else
                                   self.master.wm_state('normal')))

    def pause(self):
        self.paused = True
        self.master.title(config['text_title'].format(CONFIG_DEFAULT['text_title_paused']))
        self.pause_button['text'] = 'Unpause'
        self.pause_button['command'] = self.unpause
        self.master.attributes('-topmost', config['option_on_top_paused'])
        self.pause_button.focus()

    def unpause(self):
        self.paused = False
        self.master.title(config['text_title'].format(''))
        self.pause_button['text'] = 'Pause'
        self.pause_button['command'] = self.pause
        if config['option_always_on_top']:
            self.master.attributes('-topmost', True)
        self.pause_button.focus()

    def wait_for_break(self):
        global break_in
        if self.paused:
            self.after(1000, self.wait_for_break)
            return
        break_in -= 1
        if break_in <= 0:
            break_in = config['time_break_after']
            self.eyebreak()
            return
        self.progress_bar['value'] = (config['time_break_after'] - break_in) / config['time_break_after'] * 100
        self.label['text'] = config['text_break_in'].format(math.floor(break_in / 60), break_in % 60)
        self.after(1000, self.wait_for_break)

    def repack(self):
        if not config['option_always_on_top']:
            self.master.attributes('-topmost', False)
        self.label.pack_forget()
        self.pause_button.pack_forget()
        self.pause_button['state'] = tkinter.NORMAL
        self.progress_bar.pack({'side': 'top'})
        self.label.pack()
        self.pause_button.pack()
        self.master.geometry('+{x:.0f}+{y:.0f}'.format(x=0, y=0))
        self.wait_for_break()

    def eyebreak(self):
        if config['option_minimize_counting_down']:
            self.master.wm_state('normal')
        self.progress_bar['value'] = 100
        self.pause_button['state'] = tkinter.DISABLED
        self.label['text'] = config['text_break_now']
        self.master.geometry('+{x:.0f}+{y:.0f}'.format(x=(self.screen_size[0] / 2
                                                          - self.winfo_width() / 2
                                                          + config['option_popup_offset'][0]),
                                                       y=(self.screen_size[1] / 2
                                                          - self.winfo_height() / 2
                                                          + config['option_popup_offset'][1])))
        self.master.lift()
        if not config['option_always_on_top']:
            self.master.attributes('-topmost', True)
        self.label.focus()
        # self.master.after_idle(self.master.call, 'wm', 'attributes', '.', '-topmost', False)
        self.after(1000, lock_screen)
        self.after(config['time_break_time'] * 1000, self.break_end)
        if playsound:
            playsound.playsound(config['sound_break_start'])

    def break_end(self):
        if playsound:
            playsound.playsound(config['sound_break_end'])
        self.repack()
        if config['option_minimize_counting_down']:
            self.master.wm_state('iconic')


root = tkinter.Tk()
# root.state('iconic')

main = App(root)
root.title(config['text_title'].format(''))
main.pack()
# root.wm_minsize(100, 100)
root.mainloop()
