import os
import pandas as pd

class FileHandler(object):

	"""
	Handles files for all modules
	"""

	def __init__(self):
		"""
		TODO: 
			Load input/output folder paths from config
			Define file loader functions (load irrigation files, load storage files, etc.)
		"""
		pass

	#End init()

	def getFileList(self, folder, ext=".csv", walk=True):

		"""
		Get a list of files with the matching extension in the given folder.

		:param folder: Path of folder to search
		:param ext: File extension to look for
		:param walk: (True | False) Search subfolders found within :folder:
		:returns: A list of files

		"""

		file_list = []

		if walk is True:
			for root, dirs, files in os.walk(folder):
				for f in files:
					if f.endswith(ext):
						file_list.append(os.path.join(root, f))
					#End if
				#End for
			#End for
		else:
			for f in os.listdir(folder):
				if f.endswith(ext):
					file_list.append(f)
				#End if
			#End for

		return file_list

		#self.file_list[folder] = file_list

	#End getFileList()

	def importFiles(self, folder, ext=".csv", walk=True):

		"""
		Import files found within a given folder into Pandas DataFrame

		WARNING: Files with matching names will override each other

		:param folder: Folder to search
		:param ext: File extension to search for
		:param walk: (True | False) search subfolders in the given folder
		:returns: Dict of Pandas DataFrame for each file found

		"""

		imported = {}

		files = self.getFileList(folder, ext, walk)

		for f in files:
			fname = os.path.splitext(f)[0] #Get filename without extension
			path, fname = os.path.split(fname) #Get filename by itself

			try:
				imported[fname] = pd.read_csv(f, skiprows=1, skipinitialspace=True)
			except IndexError:
				try:
					imported[fname] = pd.read_csv(f, skiprows=0, skipinitialspace=True, index_col=0, header=0)
				except Exception:
					return False
				#End try
			#End try

		#End for

		return imported

	#End importFile()

	def loadCSV(self, filepath, columns=None):

		"""
		Load data from CSV file

		:param filepath: name of file to import
		:param columns:  a list of column headers (as found in the file) to return. Returns all if None 
		:returns: Pandas DataFrame

		"""

		data = pd.read_csv(filepath, usecols=columns)

		return data
		
	#End loadData()

	def writeCSV(self, df, filepath=None):

		"""
		Write out a DataFrame to CSV

		:param df: DataFrame to export
		:param filepath: name and location of where to export the csv file to
		:returns: CSV string (if no filepath provided) or true | false depending on success
		"""

		return df.to_csv(path_or_buf=filepath)
	#End writeCSV()