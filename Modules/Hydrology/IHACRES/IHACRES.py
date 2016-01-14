

class IHACRES():

	def __init__(self, Climate):
		
		self.Climate = Climate

	#End init()

	def calcCMD(self, d, e, f):

		"""
		:math:`g = f * d`

		:sup:`a`:math:`E_{k}` if :math:`M_{k} < g`

		:math:`eE_{k}e^-2(M_{k}-g)` if :math:`M_{k} > g`

		"""

		g = f * d

	#End calcCMD()

	def useUnitHydrograph(self):

		pass
	#End useUnitHydrograph()



