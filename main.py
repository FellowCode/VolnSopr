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
import sys

state = 'stop'
values = []

settings = {'load_multiply': 1}

APPDATA_PATH = os.getenv('APPDATA') + '\\VolnovoeSoprotivlenie\\'
BACKUP_CHARTS_DIR = APPDATA_PATH + '\\backup_charts\\'
SETTINGS_PATH = APPDATA_PATH + 'settings.vsst'
SENSOR_IP = "192.168.43.50"

start_time = 0
first_value = 0
select = (0, 0)
chart_is_open = False
current_chart_filename = ''


@eel.expose
def start():
    try:
        r = requests.get('http://' + SENSOR_IP + '/start/', timeout=1)
        global state
        state = 'start'
        eel.cl()
        global values
        global chart_is_open
        chart_is_open = False
        values = []
        return True
    except:
        print(sys.exc_info())
        return False


@eel.expose
def stop():
    is_stoped = get_values(stop_measure=True)
    if is_stoped:
        global state
        state = 'stop'
        if len(values) > 0:
            filename = '{d}.{m}.{Y}; {h}_{min}_{sec}.vlsp'.format(**reformat_datetime())
            save_chart(BACKUP_CHARTS_DIR + filename)
            backup_charts = [BACKUP_CHARTS_DIR + '\\' + f for f in listdir(BACKUP_CHARTS_DIR) if
                             isfile(join(BACKUP_CHARTS_DIR, f))]
            while len(backup_charts) > 20:
                os.remove(backup_charts.pop(0))
        return True
    return False


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
    return {'d': day, 'm': month, 'Y': datetime.now().year, 'y': datetime.now().year - 2000, 'h': hour, 'min': minute,
            'sec': sec}


@eel.expose
def clear():
    global values
    values = []
    global chart_is_open
    chart_is_open = False


def save_chart(path):
    dr = '\\'.join(path.split('\\')[0:-1])
    if not os.path.exists(dr):
        os.makedirs(dr)
    with open(path, 'w') as f:
        print(f'm_offset={round(first_value, 3)}', file=f)
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
    if chart_is_open:
        global current_chart_filename
        dialog = wx.FileDialog(None, 'Сохранить график', defaultFile=current_chart_filename,
                               wildcard='VLSP files (*.vlsp)|*.vlsp',
                               style=style)
    else:
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
    global current_chart_filename
    current_chart_filename = path.split('\\')[-1]
    with open(path, 'r') as f:
        for i, line in enumerate(f.readlines()):
            if i == 0:
                try:
                    name, value = line.strip().split('=')
                except:
                    eel.set_offset('None')
                if name == 'm_offset':
                    eel.set_offset(value)
                continue
            x, y = line.strip().split(':')
            values.append((x, y))
            eel.addData(values[-1][0], values[-1][1])
        eel.updateChart(0)
    filename = '.'.join(path.split('\\')[-1].split('.')[:-1])
    eel.chart_opened(filename)

    global chart_is_open
    chart_is_open = True


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
def set_offset(offset):
    global settings
    try:
        settings['offset'] = float(offset)
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


@eel.expose
def set_select_range(start, end):
    global select
    select = (start, end)


@eel.expose
def cut_values():
    global values
    global select
    values = values[select[0]: select[1]]


def get_values(stop_measure=False):
    global start_time
    global first_value
    try:
        if stop_measure:
            r = requests.get('http://' + SENSOR_IP + '/stop/', timeout=1)
        else:
            r = requests.get('http://' + SENSOR_IP + '/get-load/', timeout=1)
    except:
        print(sys.exc_info())
        eel.error('Нет ответа')
        return False

    lines = r.text[:-1].split('\n')
    for line in lines:
        if not ':' in line:
            break
        t, m = line.split(':')
        mult = settings.get('load_multiply', 1)
        offset = settings.get('offset', 0)
        m = (float(m)/1000 - offset/mult) * mult
        if len(values) == 0:
            start_time = int(t)
            eel.set_first_value(str(round(m, 3)))
            if settings.get('start_from_zero', False):
                first_value = m
            else:
                first_value = 0
        time_s = round((int(t) - start_time) / 1000, 2)
        values.append((f'{time_s}s', m - first_value))
        eel.addData(values[-1][0], values[-1][1])
    eel.updateChart(500)
    return True


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
    eel.set_multiply(settings.get('load_multiply', 1))
    eel.set_offset(settings.get('offset', 0))
    eel.set_start_zero(settings.get('start_from_zero', False))

    while True:
        if state == 'start':
            get_values()
        eel.sleep(0.2)
