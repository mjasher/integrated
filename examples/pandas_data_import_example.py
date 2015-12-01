import pandas as pd

data_file = 'test_data.csv'

#Test data contents
# x, y1, y2, y3
# 0, 1, 2, 3
# 1, 4, 5, 3
# 2, , , 2
# 3, 5, , 3

#NOTE: Python uses 0-based indexes, meaning counting starts at 0!

#Import data from CSV file
#skipinitialspace:
#  Each cell has a space for formatting reasons, this tells Pandas to ignore it
#  Otherwise data will be imported as string, e.g. " 10" instead of 10
data = pd.read_csv(data_file, skipinitialspace=True)
print "Imported Data"
print data
print "------------------\n"

#Alternatively, import specific columns (0-based index, import X and y3)
data_spec_cols = pd.read_csv(data_file, skipinitialspace=True, usecols=[0, 3])

print "Data from X and Y3"
print "data_spec_cols = pd.read_csv(data_file, skipinitialspace=True, usecols=[0, 3])\n"
print data_spec_cols
print "------------------\n"

#Import specific columns by header name
data_spec_cols = pd.read_csv(data_file, skipinitialspace=True, usecols=["x", "y2"])

print "Data from X and Y2"
print "data_spec_cols = pd.read_csv(data_file, skipinitialspace=True, usecols=['x', 'y2'])\n"
print data_spec_cols
print "------------------\n"

#Drop NA values
dropped_NAs = data_spec_cols.dropna()
print "Data from X and Y2, with NAs dropped"
print "dropped_NAs = data_spec_cols.dropna()\n"
print dropped_NAs
print "------------------\n"

#Slice existing dataframe by column
print "Slicing existing dataframe and dropping NAs"
print "Data for X and Y1"
print "data[['x', 'y1']].dropna()\n"
print data[['x', 'y1']].dropna()
print "------------------\n"

#Slice dataframe by row
print "Getting rows"
print "Row 1 to 3"
print "data[0:3]\n"
print data[0:3] # [Start Row Number : End Row Number]
print "------------------\n"

print "Note that getting data by index label works as well"

print "#Renaming index with text"
print 'data.index = ["one", "two", "three", "four"]'
print "Slicing by rows:"
print 'data["one": "three"]\n'

#Set index to text
data.index = ["one", "two", "three", "four"]

print data["one": "three"]

print "------------------\n"

print "Conditional slicing"

print "data[data['y1'] > 1]\n"
print data[data['y1'] > 1]
print "\n"

print "data[ (data['y1'] == 4) and (data['y3'] == 3) ]"
print data[ (data['y1'] == 4) & (data['y3'] == 3)]
print "\n"











