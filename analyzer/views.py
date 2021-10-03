from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse
from django.views import View

from .get_data import GetInfoByCoord
from .analyzer import Algoritm
from json import load, dump

class Analyze(View):
	def get(self, request, *args, **kvargs):

		POST = {}
		POST["lon"] = -93.9004
		POST["lat"] = 30.1335

		algo = Algoritm()

		data = None
		with open("analyzer/local_db.json") as j_file:
			data = load(j_file)

		# data = GetInfoByCoord.info(POST["lon"], POST["lat"])

		result = algo.count(data, {
			"mask":POST.get("mask", False),
			"vaccine":POST.get("vaccine", False),
			"distance":POST.get("distance", False),
		})

		return HttpResponse(f"Your Chance: {result}")

	def post(self, request, *args, **kvargs):
		POST = dict(request.POST)


		# simulate a USA location
		POST["lon"] = -93.9004
		POST["lat"] = 30.1335

		algo = Algoritm()

		data = None
		with open("analyzer/local_db.json") as j_file:
			data = load(j_file)

		# data = GetInfoByCoord.info(POST["lon"], POST["lat"])

		result = algo.count(data, {
			"mask":POST.get("mask", False),
			"vaccine":POST.get("vaccine", False),
			"distance":POST.get("distance", False),
		})
		return JsonResponse({"chance":result})
