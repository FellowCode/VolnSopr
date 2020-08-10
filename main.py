import eel
import wx
import random
import sys
import os
import pprint
from datetime import datetime
import pyautogui
import requests
from os import listdir
from os.path import isfile, join

state = 'stop'
values = []

settings = {'load_multiply': 1}

APPDATA_PATH = os.getenv('APPDATA') + '\\VolnovoeSoprotivlenie\\'
BACKUP_CHARTS_DIR = APPDATA_PATH + '\\backup_charts\\'
SETTINGS_PATH = APPDATA_PATH + 'settings.vsst'
SENSOR_IP = "192.168.43.50"

start_time = 0
m_offset = 0


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
    if len(values) > 0:
        filename = '{d}.{m}.{Y}; {h}_{min}_{sec}.vlsp'.format(**reformat_datetime())
        save_chart(BACKUP_CHARTS_DIR + filename)
        onlyfiles = [BACKUP_CHARTS_DIR + '\\' + f for f in listdir(BACKUP_CHARTS_DIR) if isfile(join(BACKUP_CHARTS_DIR, f))]
        while len(onlyfiles) > 20:
            os.remove(onlyfiles[0])
            onlyfiles.pop(0)


def add_zero(val):
    return '0' + str(val)

def reformat_datetime():
    if (day := datetime.now().day) < 10:
        day = add_zero(day)
    if (month := datetime.now().month) < 10:
        month = add_zero(month)
    if (hour := datetime.now().hour) < 10:
        hour = add_zero(hour)
    if (minute := datetime.now().minute) < 10:
        minute = add_zero(minute)
    if (sec := datetime.now().second) < 10:
        sec = add_zero(sec)
    return {'d': day, 'm': month, 'Y': datetime.now().year, 'y': datetime.now().year - 2000, 'h': hour, 'min': minute, 'sec': sec}


@eel.expose
def clear():
    global values
    values = []


def save_chart(path):
    dr = '\\'.join(path.split('\\')[0:-1])
    if not os.path.exists(dr):
        os.makedirs(dr)
    with open(path, 'w') as f:
        print(f'm_offset={round(m_offset, 3)}', file=f)
        for x, y in values:
            print(x, y, file=f, sep=':')


@eel.expose
def save_chart_dialog(template):
    filename = template.format(**reformat_datetime())
    settings['chart_name_temp'] = template
    save_settings()

    global values
    if len(values) == 0:
        return

    style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    dialog = wx.FileDialog(None, 'Сохранить график', defaultFile=filename, wildcard='VLSP files (*.vlsp)|*.vlsp',
                           style=style)

    if dialog.ShowModal() == wx.ID_CANCEL:
        return

    path = dialog.GetPath()

    save_chart(path)


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
        for i, line in enumerate(f.readlines()):
            if i == 0:
                try:
                    name, value = line.strip().split('=')
                    if name == 'm_offset':
                        eel.set_moffset(value)
                    continue
                except:
                    eel.set_moffset('None')
            x, y = line.strip().split(':')
            values.append((x, y))
            eel.addData(values[-1][0], values[-1][1])
        eel.updateChart(0)

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


@eel.expose
def set_multiply(multiply):
    global settings
    try:
        settings['load_multiply'] = float(multiply)
        save_settings()
    except:
        pass


@eel.expose
def start_from_zero(value):
    global settings
    try:
        settings['start_from_zero'] = value
        save_settings()
    except:
        pass


if __name__ == '__main__':
    load_settings()

    app = wx.App(None)
    eel.init('web')

    try:
        eel.start('main.html', mode='chrome', block=False)
    except:
        pyautogui.alert("Для работы приложения необходим браузер Chrome", "Ошибка")
        sys.exit()

    eel.set_chart_template(settings.get('chart_name_temp', ''))
    eel.set_multiply(settings.get('load_multiply', 1))
    eel.set_start_zero(settings.get('start_from_zero', False))

    while True:
        if state == 'start':
            try:
                r = requests.get('http://' + SENSOR_IP + '/get-load/', timeout=0.4)
                t, m = r.text.split(':')
                mult = settings.get('load_multiply', 1)
                m = float(m) * mult / 1000
                if len(values) == 0:
                    start_time = int(t)
                    eel.set_moffset(str(round(m, 3)))
                    if settings.get('start_from_zero', False):
                        m_offset = m
                    else:
                        m_offset = 0
                time_s = round((int(t) - start_time) / 1000, 2)
                values.append((f'{time_s}s', m - m_offset))
                eel.addData(values[-1][0], values[-1][1])
                eel.updateChart(500)
            except:
                eel.error('Нет ответа')
        eel.sleep(0.01)

""" assoc .vlsp=VolnSopr
    ftype VolnSopr=perl.exe %1 %* """
