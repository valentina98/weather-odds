"""Small samples in each source's file format, for tests without network.

The values are invented: downloaded weather data is never committed (N4).
"""

import gzip

METEOSTAT_HEADER = (
    "year,month,day,hour,temp,temp_source,rhum,rhum_source,prcp,prcp_source,wdir,wdir_source,"
    "wspd,wspd_source,wpgt,wpgt_source,pres,pres_source,cldc,cldc_source,coco,coco_source\n"
)
METEOSTAT_2020 = METEOSTAT_HEADER + (
    "2020,1,1,0,6.0,isd_lite,61,isd_lite,,,280,isd_lite,25.9,isd_lite,22.2,dwd_mosmix,1020.0,metar,0,isd_lite,4,dwd_mosmix\n"
    "2020,1,1,1,7.5,metar,46,isd_lite,,,290,isd_lite,35.3,isd_lite,22.2,dwd_mosmix,1020.0,metar,0,isd_lite,2,dwd_mosmix\n"
    "2020,1,1,2,9.9,dwd_mosmix,46,isd_lite,,,290,isd_lite,35.3,isd_lite,22.2,dwd_mosmix,1020.0,metar,0,isd_lite,2,dwd_mosmix\n"
    "2020,1,1,3,,,46,isd_lite,,,290,isd_lite,35.3,isd_lite,,,1020.0,metar,0,isd_lite,,\n"
    "2020,3,29,0,4.0,isd_lite,,,,,,,,,,,,,,,,\n"
    "2020,3,29,1,5.0,isd_lite,,,,,,,,,,,,,,,,\n"
    "2020,7,1,12,31.4,isd_lite,,,,,,,,,,,,,,,,\n"
)
METEOSTAT_2021 = METEOSTAT_HEADER + "2021,1,1,0,-2.5,isd_lite,,,,,,,,,,,,,,,,\n"

GSOD_HEADER = (
    '"STATION","DATE","LATITUDE","LONGITUDE","ELEVATION","NAME","TEMP","TEMP_ATTRIBUTES","DEWP","DEWP_ATTRIBUTES",'
    '"SLP","SLP_ATTRIBUTES","STP","STP_ATTRIBUTES","VISIB","VISIB_ATTRIBUTES","WDSP","WDSP_ATTRIBUTES","MXSPD",'
    '"GUST","MAX","MAX_ATTRIBUTES","MIN","MIN_ATTRIBUTES","PRCP","PRCP_ATTRIBUTES","SNDP","FRSHTT"\n'
)


def gsod_row(day: str, tmax: str, tmin: str, prcp: str, attribute: str, frshtt: str) -> str:
    return (
        f'"15625099999","{day}","42.07","24.85","181.96","PLOVDIV, BU","  42.1","24","  23.3","24","9999.9"," 0",'
        f'"999.9"," 0","  6.2","24"," 14.6","24"," 22.9","999.9","{tmax}","*","{tmin}","*","{prcp}","{attribute}",'
        f'"999.9","{frshtt}"\n'
    )


GSOD_1990 = GSOD_HEADER + (
    gsod_row("1990-06-01", "  86.0", "  59.0", " 0.50", "G", "010010")  # 30 C, 15 C, 12.7 mm, rain and thunder
    + gsod_row("1990-06-02", "9999.9", "  50.0", " 0.00", "I", "000000")  # no maximum; no rain report
    + gsod_row("1990-06-03", "  68.0", "  50.0", "99.99", " ", "001000")  # rain missing; snow seen
    + gsod_row("1990-06-04", "  68.0", "  50.0", " 0.00", "G", "")  # flags missing
)

AIRPORT_2020 = (
    "station,valid,wxcodes\n"
    "LBPD,2020-07-01 09:00,-RA\n"  # 12:00 local (UTC+3)
    "LBPD,2020-07-01 09:30,TSRA\n"
    "LBPD,2020-07-01 10:00,BR\n"
    "LBPD,2020-07-01 10:30,\n"
    "LBPD,2020-12-01 06:00,-SN\n"  # 08:00 local (UTC+2)
)
AIRPORT_EMPTY = "station,valid,wxcodes\n"

NIMH_HEADER = "     ,               ," + ",".join(f"{d:3d} " for d in range(1, 32)) + "\n"


def nimh_row(station: str, name: str, cells: dict[int, str], days: int = 31) -> str:
    values = ",".join(cells.get(d, "    ") for d in range(1, days + 1))
    return f"{station:>5},{name:<15},{values}\n"


NIMH_202202 = NIMH_HEADER + (
    nimh_row(" 1010", "NovoSelo", {1: "  9."})
    + nimh_row("46011", "Plovdiv", {2: "  2.", 3: " 12.", 4: " ?? ", 30: " 99."}, days=31)  # no 30 February
)
NIMH_INDEX = '<a href="/openData/static/csvs/mosv_prec_202202.csv">x</a> mosv_prec_202202.csv mosv_prec_202111.csv'


def gz(text: str) -> bytes:
    return gzip.compress(text.encode())
