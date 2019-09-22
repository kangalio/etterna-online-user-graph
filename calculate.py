from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor
import math, os, json
import pyqtgraph as pg
import numpy as np
import orjson
from tqdm import tqdm

import util
from util import parsedate, find_skillset_rating, find_ratings

def calc_ratings(user):
	from itertools import groupby
	
	# Prepare scores
	scores = [s for s in user["scores"] if s["nerf"] != 0] # Filter invalid
	scores = zip(scores, [util.parsedate(s["datetime"]) for s in scores]) # Zip with parsed dates
	scores = sorted(scores, key=lambda pair: pair[1]) # Sort by date
	
	skillsets = np.empty([7, len(scores)], dtype="float64")
	ss_len = 0
	
	dates = []
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
				continue
			
			nerf_multiplier = score["nerf"] / score["overall"]
			for ss in range(7): # Iterate skillsets
				skillsets[ss][ss_len] = score["skillsets"][ss] * nerf_multiplier
			ss_len += 1
		
		# Overall rating
		rating = find_ratings(skillsets[:,:ss_len])[0]
		
		# If rating changed from previous play-day (or if there's are
		# no entries yet in thet ratings list)..
		if len(ratings) == 0 or rating != ratings[-1]:
			# ..append year and overall ([0]) rating
			dates.append(util.formatdate(date))
			ratings.append(rating)
	
	return dates, ratings


def generate_ratings_file():
	print("Loading scores from json..")
	users = orjson.loads(open("misc/scores.json").read())

	print("Setting up process pool..")
	pool = ProcessPoolExecutor(os.cpu_count())

	print(f"Calculating ratings (total {len(users)} users)..")
	entries = []
	data_iterator = pool.map(calc_ratings, users, chunksize=5)
	for ((years, ratings), user) in tqdm(zip(data_iterator, users)):
		entry = {}
		entry["username"] = str(user["username"])
		entry["dates"] = years
		entry["ratings"] = ratings
		entries.append(entry)

	print(f"Dumping data into json file..")
	json.dump(entries, open("ratings.json", "w"), indent=2)

	print("Done, shutting down process pool..")
	pool.shutdown()
