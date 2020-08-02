import eel
import wx
import random
import sys
import os
import pprint
from datetime import datetime
import pyautogui

state = 'stop'
values = []

settings = {}

APPDATA_PATH = os.getenv('APPDATA') + '\\VolnovoeSoprotivlenie\\'
SETTINGS_PATH = APPDATA_PATH + 'settings.vsst'

@eel.expose
def start():
    global state
    state = 'start'
    eel.cl()
    global values
    values = []

@eel.expose
def stop():
    global state
    state = 'stop'

@eel.expose
def clear():
    global values
    values = []

def add_zero(val):
    return '0'+str(val)

@eel.expose
def save_chart(template):
    if (day := datetime.now().day) < 10:
        day = add_zero(day)
    if (month := datetime.now().month) < 10:
        month = add_zero(month)
    if (hour := datetime.now().hour) < 10:
        hour = add_zero(hour)
    if (minute := datetime.now().minute) < 10:
        minute = add_zero(minute)
    filename = template.format(d=day, m=month, Y=datetime.now().year, y=datetime.now().year-2000, h=hour, min=minute)
    settings['chart_name_temp'] = template
    save_settings()

    global values
    if len(values) == 0:
        return

    style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    dialog = wx.FileDialog(None, 'Сохранить график', defaultFile=filename, wildcard='VLSP files (*.vlsp)|*.vlsp', style=style)

    if dialog.ShowModal() == wx.ID_CANCEL:
        return

    path = dialog.GetPath()

    with open(path, 'w') as f:
        for x, y in values:
            print(x, y, file=f, sep=':')


@eel.expose
def open_chart():
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    dialog = wx.FileDialog(None, 'Открыть график', wildcard='VLSP files (*.vlsp)|*.vlsp', style=style)
    if dialog.ShowModal() == wx.ID_CANCEL:
        return

    path = dialog.GetPath()

    eel.cl()
    global values
    values = []
    with open(path, 'r') as f:
        for line in f.readlines():
            x, y = line.strip().split(':')
            values.append((x, y))
            eel.addData(values[-1][0], values[-1][1])

    filename = '.'.join(path.split('\\')[-1].split('.')[:-1])
    eel.chart_opened(filename)


def save_settings():
    global settings
    if not os.path.exists(APPDATA_PATH):
        os.makedirs(APPDATA_PATH)
    with open(SETTINGS_PATH, 'w') as f:
        pprint.pprint(settings, stream=f)

def load_settings():
    global settings
    if not os.path.exists(SETTINGS_PATH):
        return
    with open(SETTINGS_PATH, 'r') as f:
        settings = eval(f.read())


if __name__ == '__main__':



    load_settings()

    app = wx.App(None)
    eel.init('web')

    try:
        eel.start('main.html', block=False)
    except:
        pyautogui.alert("Для работы приложения необходим браузер Chrome", "Ошибка")
        sys.exit()

    eel.set_chart_template(settings.get('chart_name_temp', ''))

    i=0
    while True:
        if state == 'start':
            values.append((f'{i}s', random.randrange(0, 9)))
            eel.addData(values[-1][0], values[-1][1])
            i += 1
        eel.sleep(0.1)

""" assoc .vlsp=VolnSopr
    ftype VolnSopr=perl.exe %1 %* """

