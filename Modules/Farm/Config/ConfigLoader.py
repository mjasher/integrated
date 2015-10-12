#ConfigLoader

import os
import json

class ConfigLoader():

	def __init__(self):
		
		try:
			self.paths = json.load(open('config/paths.json'))

			#Check that working directory exists and ends with slash
			try:
				print "Working Directory set to: "+str(self.paths["working_dir"])

				if self.paths["working_dir"].endswith("/") == False:
					#Add missing ending slash if not provided
					self.paths["working_dir"] = self.paths["working_dir"] + "/"
				#End if

				#Change to defined working directory
				os.chdir(self.paths["working_dir"])

			except KeyError:
				sys.exit("ERROR: Invalid working directory or working directory is not set")
				pass
			except WindowsError: 
				print("WARNING: Invalid working directory, defaulting to current directory")
				#If any error occurs, default to old behaviour
				self.paths["working_dir"] = os.path.dirname('__file__') #+ '/'
		except:
			#If any other error occurs, default to old behaviour
			self.paths["working_dir"] = os.path.dirname('__file__') #+ '/'
		#End try

		if 'relative_paths' in self.paths:
			#Build paths
			for name, path in self.paths['relative_paths'].iteritems():

				self.paths[name] = self.paths["working_dir"] + path

				if self.paths[name].endswith("/") == False:
					self.paths[name] = self.paths[name] + "/"
				#End if
			#End for
		#End if

	#End __init__()

#End ConfigLoader()

#Create global variable for use
CONFIG = ConfigLoader()