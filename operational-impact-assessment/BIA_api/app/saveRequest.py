import json
import time

from BIA_api.app.config import BIA_GUI_PORT, BIA_GUI_ADDRESS, PREFIX_FILENAME, SUFFIX_FILENAME


def save_bia_request(data_to_save):
    bia_gui_address = BIA_GUI_ADDRESS
    request_uid = generate_uid()
    fileName = generateSaveFileName(request_uid)
    saveRequest(fileName, data_to_save)
    report_url = generateUrl(request_uid, bia_gui_address)
    return report_url


def generate_uid():
    timestamp = str(time.time_ns())
    return timestamp


def generateSaveFileName(request_uid):
    fileName = f'{PREFIX_FILENAME}{request_uid}{SUFFIX_FILENAME}'
    return fileName


def saveRequest(fileName, data_to_save):
    with open(fileName, 'w') as f:
        json.dump(data_to_save, f)


def generateUrl(request_uid, bia_gui_address):
    url = f'http://{bia_gui_address}:{BIA_GUI_PORT}/?request={request_uid}'
    return url
