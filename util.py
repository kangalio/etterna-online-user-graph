#import pyqtgraph as pg
from datetime import datetime
import math
from numba import jit
import numpy as np

# Parses date in EO format
def parsedate(s): return datetime.strptime(s, "%Y-%m-%d")

# Takes a potential rating, and a list of skillset ratings (one for each
# score). Returns a boolean, whether the given potential rating is
# 'okay', as I call it.
# 'values' must be given as numpy array (for numba compatibility)
@jit(nopython=True)
def is_rating_okay(rating, values):
	max_power_sum = 2 ** (0.1 * rating)
	power_sum = 0
	for value in values:
		erfc = math.erfc(0.1 * (value - rating))
		#if erfc == 0:
		#	print(value, rating)
		#	erfc = 1e-300
		power_sum += max(0, 2 / erfc - 2)
	return power_sum < max_power_sum


"""
The idea is the following: we try out potential skillset rating values
until we've found the lowest rating that still fits (I've called that
property 'okay'-ness in the code).
How do we know whether a potential skillset rating fits? We give each
score a "power level", which is larger when the skillset rating of the
specific score is high. Therefore, the user's best scores get the 
highest power levels.
Now, we sum the power levels of each score and check whether that sum
is below a certain limit. If it is still under the limit, the rating
fits (is 'okay'), and we can try a higher rating. If the sum is above
the limit, the rating doesn't fit, and we need to try out a lower
rating.
"""
def find_skillset_rating(values):
	rating = 0
	resolution = 10.24
	
	# Repeatedly approximate the final rating, with better resolution
	# each time
	while resolution > 0.01:
		# Find lowest 'okay' rating with certain resolution
		while not is_rating_okay(rating + resolution, values):
			rating += resolution
		
		# Now, repeat with smaller resolution for better approximation
		resolution /= 2
	
	# Round to accommodate floating point errors
	return round(rating * 1.04, 2)


# `skillsets_values` should be a list with 7 sublists, one for each
# skillset containing all values from that skillset.
# Returns list with 8 elements: first is the Overall rating, following
# are the skillset ratings.
def find_ratings(skillsets_values):
	ratings = []
	for values in skillsets_values:
		#if not values is np.ndarray: values = np.array(values)
		ratings.append(find_skillset_rating(values))
	
	overall = (sum(ratings) - min(ratings)) / 6
	if overall > 100: print([max(a) for a in skillsets_values])
	ratings.insert(0, overall)
	return ratings
