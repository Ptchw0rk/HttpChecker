#!/usr/bin/env bash
import requests
from datetime import datetime
import json

'''
{
	"site": {
		"actual_status": xxx
		"current_incident_begin": "0/0/0 00:00:00"
		"0/0/0 00:00:00": {
			"status": xxx
			"last_date": "0/0/0 00:00:00"
		}
	}
}
'''


class HttpChecker:
	def __init__(self, addresses_to_resolve):
		self.addresses_to_resolve = addresses_to_resolve

	def get_log_status(self):
		log_status = {}
		try:
			with open("status.log", 'r') as log_file:
				log_status = json.loads(log_file.read())
		except Exception:
			return log_status
		return log_status

	def check_http(self):
		log_status = self.get_log_status()
		for site_key in self.addresses_to_resolve.keys():

			if site_key not in log_status.keys():
				log_status[site_key] = {}

			try:
				res = requests.get(self.addresses_to_resolve[site_key])
				status = str(res.status_code)
			except requests.exceptions.ConnectionError:
				status = "ConnectionError"
			except requests.exceptions.HTTPError:
				status = "HTTPError"
			except requests.exceptions.SSLError:
				status = "SSLError"
			except requests.exceptions.ConnectTimeout:
				status = "ConnectTimeout"
			except requests.exceptions.TooManyRedirects:
				status = "TooManyRedirects"
			except requests.exceptions.RetryError:
				status = "RetryError"

			now_date = datetime.strftime(datetime.now(), "%D %T")

			current_incident_begin = log_status[site_key].get("current_incident_begin")
			log_status[site_key]["actual_status"] = status
			if status == "200":															# No incident
				log_status[site_key]["current_incident_begin"] = None
			elif current_incident_begin is not None:										# Incident current and already set
				if log_status[site_key][current_incident_begin]["status"] == status:	# Incident last date update
					log_status[site_key][current_incident_begin]["last_date"] = now_date
				else:																	# New incident status
					log_status[site_key]["current_incident_begin"] = now_date
					log_status[site_key][now_date]["status"] = status
					log_status[site_key][now_date]["last_date"] = now_date
			else:																		# status not ok but no incident already set
				log_status[site_key]["current_incident_begin"] = now_date
				log_status[site_key][now_date] = {}
				log_status[site_key][now_date]["status"] = status
				log_status[site_key][now_date]["last_date"] = now_date
		return log_status

	def write_log_status(self, log_status):
		str_log_status = json.dumps(log_status, indent=4, sort_keys=True)
		with open("status.log", 'w') as log_file:
			log_file.write(str_log_status)

	def check_differences(self, old_log_status, new_log_status):
		site_differences = {}	# {site: {old_status: x, new_status: x, incident_since: x}}
		for site_key in old_log_status.keys():
			site_differences[site_key] = {}
			if site_key in new_log_status.keys():
				if old_log_status[site_key]["actual_status"] != new_log_status[site_key]["actual_status"]:
					site_differences[site_key]["old_status"] = old_log_status[site_key]["actual_status"]
					site_differences[site_key]["new_status"] = new_log_status[site_key]["actual_status"]
				else:
					site_differences[site_key]["actual_status"] = new_log_status[site_key]["actual_status"]

				site_differences[site_key]["incident_since"] = new_log_status[site_key]["current_incident_begin"]
		return site_differences


if __name__ == "__main__":
	http_checker = HttpChecker(ADDRESSES_TO_RESOLVE)
	old_log_status = http_checker.get_log_status()
	new_log_status = http_checker.check_http()
	site_differences = http_checker.check_differences(old_log_status, new_log_status)
	http_checker.write_log_status(new_log_status)

	print(site_differences)