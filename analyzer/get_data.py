import logging, re
from requests import get as rget
from csv import DictReader
from datetime import datetime, timezone, timedelta
from io import BytesIO, StringIO
from zipfile import ZipFile
from typing import List, Dict
from json import load, loads
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get(url):
	responce = rget(url)
	return responce


class GlobalStatisticsFromGitHub:
	root_link = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/{}/{}"

	@classmethod
	def _get(cls, folder):
		link = cls.root_link.format(folder, cls.getFile())
		logger.debug(link)
		file = get(link)
		return file

	@classmethod
	def getUSADailyReports(cls) -> List[dict]:
		folder = "csse_covid_19_daily_reports_us"
		file = cls._get(folder)
		data = None
		with StringIO(file.text) as csv_file:
			csv_data = DictReader(csv_file)
			data = list(csv_data)
		return data

	@classmethod
	def getDailyReports(cls) -> List[dict]:
		folder = "csse_covid_19_daily_reports"
		file = cls._get(folder)
		data = None
		with StringIO(file.text) as csv_file:
			csv_data = DictReader(csv_file)
			data = list(csv_data)
		return data

	@staticmethod
	def getFile():
		curent_date = datetime.now()
		zero_date = curent_date.replace(tzinfo=timezone.utc).astimezone(tz=None)
		if curent_date.hour > 5 and zero_date.hour > 5:
			last_availebel_date = curent_date - timedelta(days=1)
		else:
			last_availebel_date = zero_date - timedelta(days=2)
		file = datetime.strftime(last_availebel_date, "%m-%d-%Y.csv")
		logger.debug(file)
		return file


class GetAdminAndAreaByLocationForSEDAC:

	def __init__(self):
		with open("analyzer/db_us.json") as j_file:
			self._us_data = load(j_file)
		with open("analyzer/db_ukraine.json") as j_file:
			self._ukraine_data = load(j_file)

	def getAllCities(self, city, country):
		return {k: v for k, v in self._us_data.items() if f"{city}, " in k and k != f"{city}, {country}"}

	@staticmethod
	def _filterByCity(data, city, area, country):
		data = {k: v for k, v in data.items() if f"{city}, {area}" in k}
		if data == {}:
			return {
				"error": "City not found!"
			}
		return data

	@staticmethod
	def _filterByArea(data, area, country):
		data = {k: v for k, v in data.items() if f"{area}, {country}" in k and "," not in k.replace(f"{area}, {country}", "")}
		if data == {}:
			return {
				"error": "Area not found!"
			}
		return data

	def getCitiesInArea(self, location:dict) -> Dict[str, List[int]]:
		country = location.get("country", None)
		area = location.get("area", None)
		if country is None or country == "Ukraine":
			return {
				"error": "Bad Request!"
			}
		lcountry = country.lower()
		data = getattr(self, f"_{lcountry}_data")
		return {k: v for k, v in data.items() if f", {area}, {country}" in k}

	def getAdminAndArea(self, location:dict) -> Dict[str, List[int]]:
		country = location.get("country", None)
		area = location.get("area", None)
		city = location.get("city", None)
		if country is None or (country == "Ukraine" and city is not None):
			return {
				"error": "Bad Request!"
			}
		lcountry = country.lower()
		data = getattr(self, f"_{lcountry}_data")
		if area is not None and city is not None:
			return self._filterByCity(data, city, area, country)
		elif area is not None:
			return self._filterByArea(data, area, country)
		else:
			return data[country]


class SEDACMapInfo:
	root_link = "https://sedac.ciesin.columbia.edu/repository/covid19/zips/{}"

	@classmethod
	def _get(cls, filename):
		link = cls.root_link.format(filename)
		logger.debug(link)
		file = get(link)
		return file

	@staticmethod
	def _normalizeUSAAdmin(admin):
		if admin > 3 or admin < 0:
			admin = 0
		return admin

	@staticmethod
	def _normalizeUKRAdmin(admin):
		if admin > 2 or admin < 0:
			admin = 0
		return admin

	@classmethod
	def _getStatistics(cls, country="UKR", admin=0, statistics="age_distributions", area=None) -> List[dict]:
		if area is not None:
			admin = f"{admin}_{area}"
		filename = f"{country}_admin{admin}_{statistics}.zip"
		file = cls._get(filename)

		if not isinstance(filename, str) and filename.status_code != 200:
			return []

		data = None
		with ZipFile(BytesIO(file.content)) as zip_file:
			with zip_file.open(zip_file.namelist()[0]) as csv_file:
				with StringIO(csv_file.read().decode("ASCII")) as csv_file:
					csv_data = DictReader(csv_file, delimiter=',')
					data = list(csv_data)
		return data


	@classmethod
	def getUSAAgeDistributions(cls, admin=0, area=None) -> List[dict]:
		return cls._getStatistics("USA", cls._normalizeUSAAdmin(admin), "age_distributions", area)

	@classmethod
	def getUSAAgePyramids(cls, admin=0, area=None) -> List[dict]:
		return cls._getStatistics("USA", cls._normalizeUSAAdmin(admin), "age_pyramids", area)

	@classmethod
	def getUSAGhssmodDensities(cls, admin=0, area=None) -> List[dict]:
		return cls._getStatistics("USA", cls._normalizeUSAAdmin(admin), "ghssmod_densities", area)


	@classmethod
	def getUKRAgeDistributions(cls, admin=0, area=None) -> List[dict]:
		return cls._getStatistics("UKR", cls._normalizeUKRAdmin(admin), "age_distributions", area)

	@classmethod
	def getUKRAgePyramids(cls, admin=0, area=None) -> List[dict]:
		return cls._getStatistics("UKR", cls._normalizeUKRAdmin(admin), "age_pyramids", area)

	@classmethod
	def getUKRGhssmodDensities(cls, admin=0, area=None) -> List[dict]:
		return cls._getStatistics("UKR", cls._normalizeUKRAdmin(admin), "ghssmod_densities", area)


class GetWeather:
	root_us_link = "https://api.openweathermap.org/data/2.5/weather?q={},{},{}&appid=f366db9790936c4189f99662f21fda93"
	root_link = "https://api.openweathermap.org/data/2.5/weather?q={},{}&appid=f366db9790936c4189f99662f21fda93"
	
	root_us_link_by_lon_lat = "https://api.openweathermap.org/data/2.5/find?lon={}&lat={}&cnt=1&appid=f366db9790936c4189f99662f21fda93"

	def __init__(self):
		with open("analyzer/state.json") as j_file:
			self._states = load(j_file)

	def getByCity(self, location:dict):
		country = location.get("country", None)
		if country not in ["US", "UA"]:
			return {
				"error": "Bad country name!"
			}
		area = location.get("area", None)
		city = location.get("city", None)
		if country == "US" and area not in self._states.keys():
			return {
				"error": "Bad Request!"
			}
		if country == "US":
			data = loads(get(self.root_us_link.format(city, self._states[area], country)).text)
		else:
			data = loads(get(self.root_link.format(city, "", country)).text)
		if int(data["cod"]) != 200:
			return {
				"error": "Bad city name!"
			}
		return data

	def getByLonLat(self, lon, lat):
		return loads(get(self.root_us_link_by_lon_lat.format(lon, lat)).text)


class GetArea:
	root_us_link = "https://en.wikipedia.org/wiki/{},_{}"
	root_us_area_link = "https://en.wikipedia.org/wiki/{}"

	@classmethod
	def US(cls, location:dict):
		area = location.get("area", None)
		city = location.get("city", None)
		full_data = {}
		if area is not None:
			if city is not None:
				html = get(cls.root_us_link.format(city.replace(" ", "_"), area.replace(" ", "_"))).text
				soup = BeautifulSoup(html, 'html.parser')
				for tr in soup.find_all("tr", {"class": "mergedrow"}):
					th = tr.find("th", {"scope":"row", "class":"infobox-label"})
					if th is not None:
						if "Land" in th.contents[0]:
							data = str(tr.find("td", {"class":"infobox-data"}))
							data = data.replace('<td class="infobox-data">', "").replace('</td>', "")
							data = data.replace("km<sup>2</sup>", "")
							data = data.split("(")[-1].replace(" ", "")
							data = data.replace(")", "").replace("\xa0", "")
							data = data.replace(",", ".")
							full_data["city"] = float(data)

			html = get(cls.root_us_area_link.format(area.replace(" ", "_"))).text
			soup = BeautifulSoup(html, 'html.parser')
			for tr in soup.find_all("tr", {"class": "mergedrow"}):
				th = tr.find("th", {"scope":"row", "class":"infobox-label"})
				if th is not None:
					if "Land" in th.contents[0]:
						data = str(tr.find("td", {"class":"infobox-data"}))
						data = data.replace('<td class="infobox-data">', "").replace('</td>', "")
						data = data.replace("km<sup>2</sup>", "")
						data = data.split("(")[-1].replace(" ", "")
						data = data.replace(")", "").replace("\xa0", "")
						data = data.replace(",", ".")
						full_data["area"] = float(data)
		return full_data


API = GetAdminAndAreaByLocationForSEDAC()
Weather = GetWeather()

class GetInfoByCoord:
	@staticmethod
	def info(lon, lat):
		data = Weather.getByLonLat(lon, lat)["list"][0]
		city = data["name"]
		country = data["sys"]["country"]
		area = None
		for localarea in API.getAllCities(city, country).keys():
			localarea = localarea.split(", ")[1]
			localdata = Weather.getByCity({
				"city": city,
				"country": country,
				"area": localarea
			})
			llon, llat = localdata["coord"].values()
			if round(abs(lon - llon), 4) < 0.0005 and round(abs(lat - llat), 4) < 0.0005:
				area = localarea

		DATA = {
			"WEATHER": data,
			"GIT": GlobalStatisticsFromGitHub.getUSADailyReports(),
			"SEDACMAPINFO":{
				"US":{
					"AgeDistributions":SEDACMapInfo.getUSAAgeDistributions(),
					"AgePyramids":SEDACMapInfo.getUSAAgePyramids(),
					"GhssmodDensities":SEDACMapInfo.getUSAGhssmodDensities()
				},
				"AREA":{},
				"CITY":{}
			}
		}


		admin, numarea = list(API.getAdminAndArea({
			"country":country,
			"area":area
		}).values())[0]

		DATA["SEDACMAPINFO"]["AREA"] = {
			"AgeDistributions":SEDACMapInfo.getUSAAgeDistributions(admin, numarea),
			"AgePyramids":SEDACMapInfo.getUSAAgePyramids(admin, numarea),
			"GhssmodDensities":SEDACMapInfo.getUSAGhssmodDensities(admin, numarea)
		}

		admin, numarea = list(API.getAdminAndArea({
			"country":country,
			"area":area,
			"city":city
		}).values())[0]

		DATA["SEDACMAPINFO"]["CITY"] = {
			"AgeDistributions":SEDACMapInfo.getUSAAgeDistributions(admin, numarea),
			"AgePyramids":SEDACMapInfo.getUSAAgePyramids(admin, numarea),
			"GhssmodDensities":SEDACMapInfo.getUSAGhssmodDensities(admin, numarea)
		}

		DATA["SQUARE"] = GetArea.US({
			"area":area,
			"city":city
		})

		return DATA

# coord = [-93.9004, 30.1335]
# GetInfoByCoord.info(*coord)