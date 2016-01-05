"""
f(x) = c[1]*x[1] + c[2]*x[2] + c[3]*x[3] + c[4]*x[4] + c[5]*x[5] + c[6]*x[6]

x[1] + x[2] + x[3] + x[4] + x[5] + x[6] <= Total Area

x[1] + x[2] <= Field Area 1
x[3] + x[4] <= Field Area 2
x[5] + x[6] <= Field Area 3

0 <= x <= Total Area


c represents crop, field, water source combination
"""

if __name__ == '__main__':

	water_sources = ['Ground', 'Surface']
	crops = ['Wheat', 'Canola', 'Tomato']
	fields = ['Loam', 'Light Clay', 'Clay']

	for field in fields:
		for crop in crops:
			for water_source in water_sources:
				print "{f}-{c}-{w} \n".format(f=field, c=crop, w=water_source)
			#End for
		#End for
	#End for
	
#End main