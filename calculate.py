from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor
import math, os, json
import pyqtgraph as pg
import numpy as np
import orjson
from tqdm import tqdm

import util
from util import parsedate, find_skillset_rating, find_ratings

"""def calc_ratings(user):
	INTERVAL = timedelta(days=7)
	LOWER_LIMIT = datetime(year=2000, month=1, day=1)
	UPPER_LIMIT = datetime.now()
	
	# Scores, sorted by datetime
	scores = sorted(user["scores"], key=lambda s: s["datetime"])
	
	#skillsets = np.empty([7, len(scores)], dtype="float64")
	skillsets = np.full([7, len(scores)], 1000, dtype="float64")
	ss_len = 0
	
	# Datetime of last data point shown
	interval_end = parsedate(scores[0]["datetime"]) + INTERVAL
	years = []
	ratings = []
	i = 0
	previous_i = 0
	interval_i = 0
	def add():
		year = 2000 + (interval_end - LOWER_LIMIT).total_seconds() /60/60/24/365
		years.append(year)
		skillset_view = skillsets[:,:ss_len]
		ratings.append(find_ratings(skillset_view)[0])
	while i < len(scores):
		date = parsedate(scores[i]["datetime"])
		if date < interval_end:
			overall = scores[i]["overall"]
			if date > LOWER_LIMIT and date < UPPER_LIMIT and overall < 40 \
					and scores[i]["wifescore"] >= 99.97 \
					and scores[i]["wifescore"] < 100: # REMEMBER
				nerf = overall - scores[i]["nerf"]
				for j in range(7):
					skillsets[j][ss_len] = scores[i]["skillsets"][j] - nerf
				ss_len += 1
			i += 1
		else:
			interval_end += INTERVAL
			interval_i += 1
			if previous_i == i: continue
			previous_i = i
			add()
	add()
	
	return years, ratings"""

def calc_ratings_2(user):
	from itertools import groupby
	
	# Prepare scores
	scores = [s for s in user["scores"] if s["nerf"] != 0] # Filter invalid
	scores = zip(scores, [util.parsedate(s["datetime"]) for s in scores]) # Zip with parsed dates
	scores = sorted(scores, key=lambda pair: pair[1]) # Sort by date
	
	skillsets = np.empty([7, len(scores)], dtype="float64")
	ss_len = 0
	
	years = []
	ratings = []
	
	for date, pairs in groupby(scores, lambda s: s[1]):
		# Extract nerfed skillset values into `skillsets`
		for score in (pair[0] for pair in pairs):
			# Skip score if it's invalid
			if (score["overall"] == 0 # EO says it's invalid
					or date < datetime(year=2000, month=1, day=1) # Too old
					or date > datetime.today() # In the future
					or score["overall"] > 40 # Unreasonably high wife
					or score["wifescore"] > 100): # Impossible accuracy
				print("Skipped score")
				continue
			
			nerf = score["overall"] - score["nerf"] # Get nerf delta
			for ss in range(7): # Iterate skillsets
				skillsets[ss][ss_len] = score["skillsets"][ss] - nerf
			ss_len += 1
		
		# Append year and overall ([0]) rating
		years.append(util.date_to_year_float(date))
		ratings.append(find_ratings(skillsets[:,:ss_len])[0])
	
	return years, ratings


def generate_ratings_file():
	print("Loading scores from json..")
	users = orjson.loads(open("misc/scores.json").read())

	print("Setting up process pool..")
	pool = ProcessPoolExecutor(os.cpu_count())

	print(f"Calculating ratings (total {len(users)} users)..")
	entries = []
	#data_iterator = pool.map(calc_ratings, users, chunksize=5)
	data_iterator = pool.map(calc_ratings_2, users, chunksize=5)
	for ((years, ratings), user) in tqdm(zip(data_iterator, users)):
		entry = {}
		entry["username"] = str(user["username"])
		entry["years"] = years
		entry["ratings"] = ratings
		entries.append(entry)

	print(f"Dumping data into json file..")
	json.dump(entries, open("ratings.json", "w"), indent=4)

	print("Done, shutting down process pool..")
	pool.shutdown()
