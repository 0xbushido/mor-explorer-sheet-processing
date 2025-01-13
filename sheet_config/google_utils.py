import csv
import json
import os
import sys
import time
import gspread
import pandas as pd
import requests
from oauth2client.service_account import ServiceAccountCredentials
from configuration.config import SHEET_UTILS_JSON_PATH, SPREADSHEET_ID, SLACK_URL, NOTIFICATION_CHANNEL

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(SHEET_UTILS_JSON_PATH, scope)

gc = gspread.authorize(credentials)

spreadsheetId = SPREADSHEET_ID
sh = gc.open_by_key(spreadsheetId)


def get_worksheet(sheet_name):
    return sh.worksheet(sheet_name)


def slack_notification(message):
    slack_url = SLACK_URL
    slack_data = {
        "username": "cron-job-processor",
        "icon_emoji": ":satellite_antenna:",
        "channel": NOTIFICATION_CHANNEL,
        "attachments": [
            {
                "color": "#9733EE",
                "fields": [
                    {
                        "value": message,
                        "short": "false",
                    }
                ]
            }
        ]
    }
    byte_length = str(sys.getsizeof(slack_data))
    headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
    response = requests.post(slack_url, data=json.dumps(slack_data), headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)


def download_sheet(sheet_name):
    worksheet = get_worksheet(sheet_name)
    print(f"Downloading current uploaded sheet for {sheet_name}...")
    filename = f'downloaded_{sheet_name}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(worksheet.get_all_values())
    print(f"Downloaded data as CSV: {filename}")
    return filename


def append_new_data(existing_csv, new_data, output_csv):
    if os.stat(existing_csv).st_size == 0:
        print(f"{existing_csv} is empty. Using new data directly.")
        new_df = pd.DataFrame(new_data)
        new_df.to_csv(output_csv, index=False)
        return output_csv
    try:
        existing_df = pd.read_csv(existing_csv)
        new_df = pd.DataFrame(new_data)
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        updated_df.to_csv(output_csv, index=False)
        print(f"New unique data appended. Updated CSV: {output_csv}")
        return output_csv
    except pd.errors.EmptyDataError:
        print("Error: The downloaded CSV file is empty.")
        new_df = pd.DataFrame(new_data)
        new_df.to_csv(output_csv, index=False)
        return output_csv


def clear_and_upload_new_records(sheet_name, csv_file):
    worksheet = get_worksheet(sheet_name)
    worksheet.clear()
    print(f"Updating new records for {sheet_name}...")

    sh.values_update(
        sheet_name,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csv_file)))}
    )
    print("Dataframe uploaded to Google Sheet.")
    slack_notification(f"Data Updated for {sheet_name}!"
                       f" Link to file: "
                       f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    time.sleep(5)
