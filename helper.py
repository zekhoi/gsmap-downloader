from datetime import datetime
import pandas as pd
import calendar
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)


def create_date_range(start, end):
    try:
        temp = pd.date_range(start, end, freq="2M")
        final = [date.strftime("%Y%m%d") for date in temp]

        time = end.split("-")
        end_year = int(time[0])
        end_month = int(time[1])
        end_date = calendar.monthrange(end_year, end_month)[-1]
        end_time = datetime(end_year, end_month, end_date).strftime("%Y%m%d")
        if not end_time in final:
            final.append(end_time)
        return final
    except:
        logging.error("Invalid date format!")
        exit()


def create_folder(folder):
    if not os.path.isdir(folder):
        os.mkdir(folder)
        logging.info("Folder created!")
    else:
        logging.info("Folder already exist!")
