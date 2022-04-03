from _thread import *
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import socket
import sys
from threading import Timer

# change the file name accordingly
UPLOAD_INTERVAL = 60
GDOCS_OAUTH_JSON = "iot-cw2-346112-27af4799a4dc.json"
# change the spreadsheet name accordingly
GDOCS_SPREADSHEET_NAME = "IoT-CW2-Dashboard"
# change the worksheet name accordingly
GDOCS_WORKSHEET_NAME = "Data"


def login_open_sheet(oauth_key_file, spreadsheet_name, worksheet_name):
    """Connect to Google Docs spreadsheet and return the first worksheet."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file, scope)
        gc = gspread.authorize(credentials)
        worksheet = gc.open(spreadsheet_name).worksheet(worksheet_name)
        return worksheet

    except Exception as e:
        print('Unable to login and get spreadsheet.', e)
        sys.exit(1)


ServerSocket = socket.socket()
ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = "0.0.0.0"
port = 8019
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print('Waiting for a Connection..')
ServerSocket.listen(5)
gate_zero_message_count = 0
gate_one_message_count = 0
gate_two_message_count = 0


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def threaded_client(connection):
    global gate_zero_message_count, gate_one_message_count, gate_two_message_count

    while True:
        data = connection.recv(2048)
        message = data.decode('utf-8').split('_')
        print(message[0])
        match message[0]:
            case "Gate 0":
                gate_zero_message_count += 1
            case "Gate 1":
                gate_one_message_count += 1
            case "Gate 2":
                gate_two_message_count += 1


def upload_to_spreadsheet(counts):
    sheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME, GDOCS_WORKSHEET_NAME)
    sheet.append_row(counts)


def upload_count():
    global gate_zero_message_count, gate_one_message_count, gate_two_message_count
    counts = [gate_zero_message_count, gate_one_message_count, gate_two_message_count]
    print('Uploading :')
    print(counts)
    upload_to_spreadsheet(counts)
    gate_zero_message_count = 0
    gate_one_message_count = 0
    gate_two_message_count = 0


upload_timer = RepeatTimer(UPLOAD_INTERVAL, upload_count)
upload_timer.start()

while True:
    Client, address = ServerSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(threaded_client, (Client, ))
ServerSocket.close()

