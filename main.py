from gsmap import GSMapDownloader

if __name__ == "__main__":
    print(
        """
    ,--.           ,--.           
    |  |    ,--,--.|  |-.  ,---.  
    |  |   ' ,-.  || .-. '(  .-'  
    |  '--.\ '-'  || `-' |.-'  `) 
    `-----' `--`--' `---' `----'  
    by @zekhoi
        """)

    start_date = input("Start date (YYYY-MM): ")
    end_date = input("End date (YYYY-MM): ")

    latitude = input("Latitude: ")
    longitude = input("Longitude: ")

    downloader = GSMapDownloader()
    downloader.set_location(latitude, longitude)
    downloader.set_range(start_date, end_date)
    downloader.start()
