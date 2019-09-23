import json, random
from datetime import datetime, timedelta
from functools import reduce
import numpy as np, pandas as pd
from tqdm import tqdm

import util

DAY = timedelta(days=1)

start_date_hacky = None

def user_to_raw_df(user):
	dates = list(map(util.parsedate, user["dates"]))
	#ratings = [r/2-10 for r in user["ratings"]]
	ratings = user["ratings"]
	username = user["username"]
	df = pd.DataFrame({username: ratings}, index=dates)
	df.loc[start_date_hacky] = [0]
	return df

def reduce_dfs(dfs):
	return reduce(lambda a, b: pd.merge(a, b, left_index=True, right_index=True, how="outer"), dfs)

class Generator:
	def __init__(self, users, start_date, end_date):
		self.users = users
		self.start_date = start_date
		self.end_date = end_date
	
	def generate(self):
		global start_date_hacky
		start_date_hacky = self.start_date
		
		users = list(filter(lambda u: u["ratings"][-1] > 23, self.users))
		#users = users[:10]
		iterator = util.POOL.map(user_to_raw_df, users)
		dfs = list(tqdm(iterator, total=len(users), desc="Generate dataframes"))
		
		iterator = util.POOL.map(reduce_dfs, util.chunks(dfs, 100))
		dfs = tqdm(iterator, total=len(dfs) // 100, desc="Merge dataframes")
		df = reduce_dfs(dfs)
		
		print("Process..")
		r = pd.date_range(start=self.start_date, end=self.end_date)
		df = df.reindex(r).ffill().iloc[::10]
		df.index = df.index.strftime("%m/%Y")
		print(df)
		df = df.T
		df.insert(0, "id", np.random.random(len(df)))
		print("Write..")
		df.to_csv("flourish.csv")
		print("Done")

def generate_flourish_csv():
	start_date = datetime(year=2017, month=1, day=1)
	end_date = datetime(year=2019, month=9, day=1)
	users = json.load(open("ratings.json"))
	generator = Generator(users, start_date, end_date)
	return generator.generate()
