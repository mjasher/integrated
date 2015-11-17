 
class Ecological():
    fdafda
    fdas
    """
    fda
    """
    
	"""
	flow sequence

	flood attributes

	weightings

	for each

	duration

	time

	inter_flood dry period

		calculate an index

		and weighting based on preferences

	Range of CTF

	SW:

		gw level
		salinity

		calculate curves and index for gw and salinity

		calculate suitability of gw factoring in salinity (adjustment factor)

	Flow methodology:
		Rules based on environmental flow definitions (low flow, freshes, etc.) frequency based on percentage

		Calculate # of days 

	"""

	def threshold_func1(self, z1, w1, z2, w2):

		return z1 * w1 + z2 * w2

	def other_threshold(self, z1, w1, z2, w2):
		return min(z1 * w1, z2 * w2)

	# if(study_area == 'x'):
	# 	threshold_func()
	# else:
	# 	other_threshold()

	# def i(i, gw, salinity):
	# 	return i * salinity

class Example(object):

	def threshold_func(self, z1, w1, z2, w2):
		return z1 * w1 + z2 * w2

	def determineEcologicalHealth(self, list_of_species, ecological_data):
		pass

	def speciesHealth(self, list_of_species, ecological_data):

		for s in species:
			pass

	def calcCurves(x, y, z):
		pass


class NewStudyArea(Example):

	def threshold_func(self, z1, w1, z2, w2):
		return min(z1 * w1, z2 * w2)

	def calcDurationCurves(self, x, y, z):

		self.calcCurves(x, y, z)


if __name__ == '__main__':
	Ex = Example()

	

	# StudyArea = Example()
	# StudyArea.threshold_func()




	