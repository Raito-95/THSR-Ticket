class Endpoints:
    TRAINS_BY_DATE = (
        "https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/DailyTimetable/TrainDate/{}"
    )
    TRAINS_BY_ORI_DEST_STATION = "https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/DailyTimetable/OD/{OriginStationID}/to/{DestinationStationID}/{TrainDate}"
