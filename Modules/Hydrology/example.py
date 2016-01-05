

example_list = ["1", 1, 2, 5.0, "10"]

#example_list2 = [1, 5, 6, 7]

list2 = example_list

list2.append("5")

print example_list
print list2


class Lists():

	def add_to_list(a_list, value):
		return a_list.append(value)


class Furniture():

	def __init__(self, legs):

		self.legs = legs
	#End

	def sit(self):
		print "Something"
#End

class Chair(Furniture):

	def __init__(self, legs):

		Furniture.__init__(self, legs)
	#End

	def sit(self):
		print "Something else"

#End

class Stool(Furniture):

	def __init__(self, legs):

		Furniture.__init__(self, legs)
	#End

	def sit(self):
		print "This is a stool"

#End

Stool = Chair(legs=1)
Stool2 = Chair(legs=1)
Stool3 = Stool(legs=1)

Stool.sit()
Stool3.sit()









