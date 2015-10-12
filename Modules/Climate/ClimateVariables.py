class Climate:

	def __init__(self, **kwargs):

		#Set all key word arguments as attributes
		for key, value in kwargs.items():
			setattr(self, key, value)
		#End For
	#End init()

#End ClimateVariables
