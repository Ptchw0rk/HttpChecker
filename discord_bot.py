#!/usr/bin/env python3

import discord
from config import *
from http_checker import HttpChecker
from datetime import datetime

class DiscordBot(discord.Client):

	async def on_message(self, message):
		print(message)

	async def on_ready(self):	# Used as __init__ in our case
		print(f"Logged on as {self.user}")
		self.errors_to_display = []
		self.error_channel = None
		for channel in self.get_all_channels():
			if channel.name == ERROR_CHANNEL_NAME:
				self.error_channel = channel

		http_checker = HttpChecker(ADDRESSES_TO_RESOLVE)
		old_log_status = http_checker.get_log_status()
		new_log_status = http_checker.check_http()
		http_checker.write_log_status(new_log_status)

		site_differences = http_checker.check_differences(old_log_status, new_log_status)
		print("Actual site differences : " + str(site_differences))

		await self.send_new_status(site_differences)
		

		await self.send_errors()	
		await self.close()

	async def send_new_status(self, differences: dict, channel_name="sites-status"):
		channel = None
		for channel_in_list in self.get_all_channels():
			if channel_in_list.name == channel_name:
				channel = channel_in_list
		if not channel:
			self.errors_to_display.append(f"Channel '{channel_name}' not found")
			return None

		for site_key in differences.keys():
			if differences[site_key].get("new_status") and differences[site_key].get("old_status"):
				message = f"Site {site_key} state changed from '{differences[site_key]['old_status']}' to '{differences[site_key]['new_status']}'"
				
			elif differences[site_key].get("actual_status") is not None:
				if differences[site_key].get("actual_status") == "200":
					continue
				message = f"Incident on site {site_key} is always on status {differences[site_key].get('actual_status')}"

			if differences[site_key].get("incident_since") is not None:
					message += f", incident started at {differences[site_key].get('incident_since')}"
			await channel.send(message)



	async def send_errors(self):
		if self.error_channel:
			for error in self.errors_to_display:
				print("Error during execution : " + str(error))
				await self.error_channel.send(error)
			self.errors_to_display = []
		else:
			print("Error : Error channel don't exists")

if __name__ == "__main__":
	

	intents = discord.Intents.default()
	intents.message_content = True

	client = DiscordBot(intents=intents)
	client.run(DISCORD_BOT_TOKEN)

