if __name__ == '__main__':
	from scipy.optimize import linprog as lp

	A = [6.0, 3.0, 6.0, 6.0, 3.0, 6.0, 6.0, 3.0, 6.0]

	A_ub = []

	num_set = 2

	for i, v in enumerate(A[0::num_set]):

		t = A[i::num_set]

		temp = [1 for index, value in enumerate(A)]
		temp[i::num_set] = t

		print "---------------"
		print temp
		print "---------------"

		A_ub.append(temp)
	#End for

	print A_ub
			
	print "-----------------------"

	#Create list of 24 items, value does not matter
	A = [5 for i in xrange(0, 24)]

	print [index for index, value in enumerate(A)]

	for i in xrange(0, len(A), num_set):

		temp_list = [y for y in xrange(i, i+(num_set))]

		A_ub_element = [1 if x in temp_list else 0 for x, val in enumerate(A)]
		print A_ub_element



# for i in xrange(0, len(A), num_set):

# 	print i

# 	A_ub.append([])

# 	temp = A[i::i+num_set]

# 	print "Temp"
# 	print temp

# 	t = []
# 	for i, v in enumerate(temp):

# 		for n in xrange(num_set):
# 			if n != i:
# 				t.extend([0.0])
# 			else:
# 				t.extend([temp[n]])
# 			#End if
# 		#End for
# 	#End for

# 	print t

# #End for