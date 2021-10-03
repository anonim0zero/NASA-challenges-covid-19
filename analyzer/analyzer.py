from json import load

class Algoritm:

	def __init__(self):
		with open("analyzer/coefficients.json") as j_file:
			self._coefficients = load(j_file)

	def count(self, data, user_data):

		_mask = user_data.get("mask", False)
		_vaccine = user_data.get("vaccine", False)
		_distance = user_data.get("distance", False)

		city, area, _ = data["SEDACMAPINFO"]["CITY"]["AgeDistributions"][0]["Area"].split(", ")
		local_git_data = None
		for ldata in data["GIT"]:
			if ldata["Province_State"] == area:
				local_git_data = ldata

		area_P0 = 0
		for ldata in data["SEDACMAPINFO"]["AREA"]["AgeDistributions"]:
			area_P0 += int(ldata["Population"])

		city_P0 = 0
		for ldata in data["SEDACMAPINFO"]["CITY"]["AgeDistributions"]:
			city_P0 += int(ldata["Population"])

		cases = int(local_git_data["Confirmed"])
		recovered = 0
		if local_git_data["Recovered"] != "":
			recovered = int(local_git_data["Recovered"])
		
		deads = int(local_git_data["Deaths"])

		chance = 0.34 * round(1 - (int(not _distance) + 0.01) * 0.89, 4) * (cases-recovered) * (((area_P0-deads) - cases)/(area_P0-deads))
		chance = abs((chance - cases) / (area_P0 - cases))
		human_on_km2 = int(area_P0/data["SQUARE"]["area"]/1000) - 1
		cases_human_on_km2 = int(cases/data["SQUARE"]["area"]/1000)

		temp = float(data["WEATHER"]["main"]["temp"])
		temp_min = float(data["WEATHER"]["main"]["temp_min"])
		temp_max = float(data["WEATHER"]["main"]["temp_max"])
		temp = (temp - temp_min) / (temp_max - temp_min)

		wind = data["WEATHER"]["wind"]["speed"]/30

		cases_human_on_km2 = cases_human_on_km2/human_on_km2
		human_on_km2 = human_on_km2/300


		human_on_km2 = self._coefficients["human_on_km2"] * human_on_km2
		cases_human_on_km2 = self._coefficients["cases_human_on_km2"] * cases_human_on_km2

		chance = self._coefficients["chance"] * chance

		temp = self._coefficients["temp"] * temp
		wind = self._coefficients["wind"] * wind

		_mask = int(not _mask) * self._coefficients["mask"]
		_vaccine = int(_vaccine) * self._coefficients["vaccine"]
		print(_vaccine)

		total_risk = human_on_km2 + cases_human_on_km2 + chance + temp + wind + _mask - _vaccine
		total_risk += 0.09

		return round(total_risk, 2)
