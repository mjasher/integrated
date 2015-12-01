#BOMHandler

from integrated.Modules.Core.Handlers.FileHandler import FileHandler
import pandas as pd
import numpy as np

class BOMHandler(FileHandler):

	# def __init__(self):
	# 	super(DataHandler, self).__init__(self)
	# #End

	def loadBOMCSVData(self, filepath, data_cols=None, replace_missing=None, date_range=None):

		"""
		Load CSV data from BOM. Concatenating dates from Year, Month, Day columns.

		:param filepath: Path to file including filename and extension
		:param data_cols: (List) Data columns to import.
		:param replace_missing: If numeric, replace all with given value. If string ('ffill' or 'bfill'), replace with previous or next value
								 See http://pandas.pydata.org/pandas-docs/stable/missing_data.html
		:param date_range: array-like with two string values. Represents date range to extract. First value represents a start datetime, second value represents end datetime

		"""

		temp = ["Year", "Month", "Day"]

		if data_cols is not None and type(data_cols) is list:
			request_cols = temp[:] #Remember, python is pass-by-reference, to [:] is necessary to copy the values to new variable
			request_cols.extend(data_cols)
		else:
			request_cols = data_cols

		data = super(BOMHandler, self).loadCSV(filepath, request_cols)

		#Join date columns together
		data["Date"] = data.apply(lambda x:'%d-%02d-%02d' % (x['Year'],x['Month'], x['Day']), axis=1)

		#Remove date columns from dataframe
		for i in temp:
			data.pop(i)

		#Parse dates into datetime
		data["Date"] = pd.to_datetime(data["Date"])

		if date_range is not None:
			start = date_range[0]
			end = date_range[1]

		if start is not None:
			data = data[data["Date"] >= pd.to_datetime(start)]

		if end is not None:
			data = data[data["Date"] <= pd.to_datetime(end)]

		#remove date columns from request list
		request_cols = [item for item in request_cols if item not in temp]

		#is a number
		if isinstance(replace_missing, (int, long, float, complex)):
			#data[np.isnan(data)] = replace_missing
			data[request_cols] = data[request_cols].fillna(replace_missing)
		elif type(replace_missing) is str:
			#Forward fill missing data (replace missing with previous known value)
			data[request_cols] = data[request_cols].fillna(method=replace_missing)
		#End if

		return data

	#End loadBOMCSVData()

	def loadAllBOMData(self):

		"""
		Load all BOM data

		  This is adapted from Namoi model. 
		  TODO: Separate data source (filepaths and column names)
		"""

		#Load all BOM data
		min_temps_df = self.loadBOMCSVData("test_data/climate/IDCJAC0011_055023_1800/IDCJAC0011_055023_1800_Data.csv", ["Minimum temperature (Degree C)"], date_range=["1899-01-01", "2011-12-27"], replace_missing=0.0)
		max_temps_df = self.loadBOMCSVData("test_data/climate/IDCJAC0010_055023_1800/IDCJAC0010_055023_1800_Data.csv", ["Maximum temperature (Degree C)"], date_range=["1899-01-01", "2011-12-27"], replace_missing=0.0)
		rain_df = self.loadBOMCSVData("test_data/climate/IDCJAC0009_055076_1800/IDCJAC0009_055076_1800_Data.csv", ["Rainfall amount (millimetres)"], date_range=["1899-01-01", "2011-12-27"], replace_missing=0.0)

		mean_temp = pd.Series((min_temps_df['Minimum temperature (Degree C)'] + max_temps_df['Maximum temperature (Degree C)']) / 2)
		mean_temp = mean_temp.reset_index() #Returns dataframe

		rain_temp_df = pd.DataFrame({"Date": min_temps_df["Date"]})
		rain_temp_df = rain_temp_df.merge(rain_df, how="right", on="Date")

		rain_temp_df["Mean Temperature"] = mean_temp[0]
		rain_temp_df.index = rain_temp_df["Date"]

		return rain_temp_df
	#End loadAllBOMData()

#End BOMHandler()