from requests.structures import CaseInsensitiveDict
from bs4 import BeautifulSoup as bs
from tqdm import tqdm
from datetime import datetime
from requests.auth import HTTPBasicAuth
from helper import logging, create_date_range, create_folder
import requests as req
import pandas as pd
import csv
import os
import re
import getpass


class GSMapDownloader:
    def __init__(self) -> None:
        self.session_file = "session.txt"
        self.file_format = ".csv"
        self.session = ""
        self.username = ""
        self.password = ""
        self.login_type = "session"
        self.dates = []

    def set_location(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def set_range(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.dates = create_date_range(start_date, end_date)

    def init_folder(self):
        current_time = datetime.now().strftime("%H:%M")
        folder_data = os.getcwd() + "/data/"
        folder_today = folder_data + datetime.today().strftime("%Y-%m-%d") + "/"
        folder_result = folder_today + "Latitude:" + self.latitude + \
            "Longitude:" + self.longitude + " at " + current_time + "/"
        folder_processed = folder_result + "processed/"
        folder_unprocessed = folder_result + "unprocessed/"
        create_folder(folder_data)
        create_folder(folder_today)
        create_folder(folder_result)
        create_folder(folder_processed)
        create_folder(folder_unprocessed)
        return folder_processed, folder_unprocessed, folder_result

    def load_session(self):
        isSessionFileExists = os.path.isfile(self.session_file)
        if (isSessionFileExists):
            file = open(self.session_file, "r")
            session = file.read()
            file.close()

            isSessionValid = session != "" or session != None or re.match(
                r"^Basic [a-zA-Z0-9=]+$", session)
            if (isSessionValid):
                logging.info("Session found!")
                self.session = session
                self.login_type = "session"
                return
            self.login_type = "auth"
            logging.info("Session contains nothing!")
        else:
            logging.info("Session not found or expired!")
            logging.info("Please login to your account!")
            self.username = input("Username: ")
            self.password = getpass.getpass("Password: ")
            self.login_type = "auth"

    def save_session(self, session):
        logging.info("Saving session...")
        self.session = session
        open(self.session_file, "w").write(session)
        self.login_type = "session"
        logging.info("Session saved!")

    def get_content(self, date):
        return req.get("https://sharaku.eorc.jaxa.jp/cgi-bin/trmm/GSMaP_CLM/show_graph_CLM_v1.cgi?term=DLY&seldate=" + date + "&lat0=" + self.latitude + "&lon0=" + self.longitude + "&lang=en").text

    def download(self, url):
        headers = CaseInsensitiveDict()
        headers["Authorization"] = self.session
        if (self.login_type != 'auth'):
            response = req.get(url, headers=headers)
        else:
            response = req.get(url, auth=HTTPBasicAuth(
                self.username, self.password))

        if (response.status_code == 200):
            if (self.login_type == "auth"):
                session = response.request.headers.get("Authorization")
                self.save_session(session)
            csv = response.content.decode('utf-8')
            return csv

        logging.info("Download failed!")
        self.login_type = "auth" if response.status_code == 401 and self.login_type == "session" else "session"
        if self.login_type == "auth":
            if os.path.exists(self.session_file):
                os.remove(self.session_file)

        self.load_session()
        return self.download(url)

    def merge_csv(self, path_merged, path_unmerged):
        merged_name = self.start_date + " to " + self.end_date
        csvs = [path_unmerged + file_name +
                self.file_format for file_name in self.dates]
        csv_union = pd.concat(map(pd.read_csv, csvs), ignore_index=True)

        duplicate_total = csv_union["Date(yyyymmdd)"].duplicated().sum()

        if duplicate_total > 0:
            logging.info(str(duplicate_total) + " duplicate records found!")
            csv_union = csv_union[~csv_union["Date(yyyymmdd)"].duplicated()]
            logging.info(str(duplicate_total) +
                         " duplicate records have been removed!")
        else:
            logging.info("No duplicate record found!")

        start_year = self.dates[0][:4]
        start_month = self.dates[0][4:6]
        start_date = "00"
        date_start = start_year + start_month + start_date
        data_used = csv_union[csv_union["Date(yyyymmdd)"] > int(date_start)]
        data_used.to_csv(path_merged + merged_name +
                         self.file_format, index=False)

    def save_to_csv(self, path, data):
        rows = csv.reader(data.splitlines(), delimiter=",")
        file = open(path, "w")
        writer = csv.writer(file)
        for row in list(rows):
            writer.writerow([row[0], row[1]])
        file.close()

    def start(self):
        try:
            path_processed, path_unprocessed, path_result = self.init_folder()
            self.load_session()
            logging.info("Downloading data from " +
                         self.start_date + " to " + self.end_date)
            for date in tqdm(self.dates, desc="Downloading"):
                file_path = path_unprocessed + date + self.file_format
                content = self.get_content(date)
                parsed_html = bs(content, "html.parser")
                download_link = parsed_html.find("a").get("href")
                data = self.download(download_link)
                self.save_to_csv(file_path, data)
            logging.info("Downloaded!")
            logging.info("Merging CSVs...")
            self.merge_csv(path_processed, path_unprocessed)
            logging.info("Merged!")
            logging.info("You can find the result in " + path_result)
        except Exception as e:
            logging.error("Error occured!")
            logging.error(e)
