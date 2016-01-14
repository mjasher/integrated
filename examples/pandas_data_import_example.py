import pandas as pd

print "Python Pandas DataFrame examples"
print "--------------------------------\n\n"

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
print "Imported Data from {df}".format(df=data_file)
print "data = pd.read_csv(data_file, skipinitialspace=True)"
print data
print "------------------\n"

#Alternatively, import specific columns (0-based index, import X and y3)
data_spec_cols = pd.read_csv(data_file, skipinitialspace=True, usecols=[0, 3])

print "Importing data from specific columns only"
print "------------------\n"

print "Import data only from columns X and Y3 using their index positions"
print "data_spec_cols = pd.read_csv(data_file, skipinitialspace=True, usecols=[0, 3])\n"
print data_spec_cols
print "------------------\n"

#Import specific columns by header name
data_spec_cols = pd.read_csv(data_file, skipinitialspace=True, usecols=["x", "y2"])

print "Importing data from columns X and Y2 using their column names"
print "data_spec_cols = pd.read_csv(data_file, skipinitialspace=True, usecols=['x', 'y2'])\n"
print data_spec_cols
print "------------------\n"

#Drop NA values
dropped_NAs = data_spec_cols.dropna()
print "Removing NAs from a dataframe is simple as dropna()"
print "dropped_NAs = data_spec_cols.dropna()\n"
print dropped_NAs
print "------------------\n"

#Slice existing dataframe by column
print "You can chain commands as well."
print "Here, we slice the original dataframe, pulling out only columns X and Y1 and drop any NA values"
print "Data for X and Y1 with NAs dropped"
print "data[['x', 'y1']].dropna()\n"
print data[['x', 'y1']].dropna()
print "------------------\n"

#Slice dataframe by row
print "Extracting (slicing) data"
print "------------------\n"
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
print "------------------\n"

print "data[ (data['y1'] == 4) and (data['y3'] == 3) ]"
print data[ (data['y1'] == 4) & (data['y3'] == 3)]
print "------------------\n"

print "If you want the value for a specific row/column and only the value, use loc[row, column]"
print "data.loc['two', 'y1']"
print data.loc["two", "y1"]
print "------------------\n"

print "If you want to get a value from a specific row/column, but you don't know the index value (just its 0-indexed position), use iloc"
print "data['y1'].iloc[1]"
print data['y1'].iloc[1]
print "------------------\n"

print "Using the implied index also works in this use case (the value below should be identical to the one above)"
print "data['y1'][1]"
print data['y1'][1]

print "But this often fails if the given index was removed. e.g. Row '1' was filtered out"
print "So it is safer to rely on iloc"














