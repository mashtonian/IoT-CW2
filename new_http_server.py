import requests
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


API_URL = "https://api.tfl.gov.uk/line/mode/tube,overground/status"


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
        if message[0] == "Gate 0":
            gate_zero_message_count += 1
        elif message[0] ==  "Gate 1":
            gate_one_message_count += 1
        elif message[0] == "Gate 2":
            gate_two_message_count += 1


def upload_to_spreadsheet(data):
    sheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME, GDOCS_WORKSHEET_NAME)
    sheet.insert_row(data, index=2)


def upload_data():
    global gate_zero_message_count, gate_one_message_count, gate_two_message_count
    
    data = [gate_zero_message_count, gate_one_message_count, gate_two_message_count]
    tube_data.update()

    lines = ["Piccadilly", "Victoria", "London Overground"]

    for line in lines:
       data.append(tube_data.data[line]["State"])
    print('Uploading :')
    print(data)
    upload_to_spreadsheet(data)
    gate_zero_message_count = 0
    gate_one_message_count = 0
    gate_two_message_count = 0


def parse_api_response(response):
    """Parse the TFL API json response."""
    lines = [line["name"] for line in response]
    data_dict = dict.fromkeys(lines)

    for line in response:
        try:
            statuses = [
                status["statusSeverityDescription"] for status in line["lineStatuses"]
            ]
            state = " + ".join(sorted(set(statuses)))

            if (
                state == "Good Service"
            ):  # if good status, this is the only status returned
                reason = "Nothing to report"
            else:
                reason = " *** ".join(
                    [status["reason"] for status in line["lineStatuses"]]
                )

            data_dict[line["name"]] = {"State": state, "Description": reason}

        except:
            data_dict[line["name"]] = {
                "State": None,
                "Description": "Error parsing API data",
            }

    return data_dict


class TubeData:
    """Get the latest tube data from TFL."""

    def __init__(self):
        """Initialize the TubeData object."""
        self._data = {}

    def update(self):
        """Get the latest data from TFL."""
        response = requests.get(API_URL)
        if response.status_code != 200:
            return
        self._data = parse_api_response(response.json())

    @property
    def data(self):
        """Return the data."""
        return self._data
  
    
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

tube_data = TubeData()

upload_data()
upload_timer = RepeatTimer(UPLOAD_INTERVAL, upload_data)
upload_timer.start()

while True:
    Client, address = ServerSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(threaded_client, (Client, ))
    
ServerSocket.close()
