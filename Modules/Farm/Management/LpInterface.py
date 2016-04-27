import pandas as pd
import numpy as np
import itertools

#Linear programming
from scipy.optimize import linprog as lp

class LpInterface(object):


    def genLogTemplates(self, field_combinations):

        """
        Generate Pandas DataFrames to store LP :math:`c` and right hand upper bound (b_ub) coefficients

        :param num_fields_water_sources: Number of fields for farm
        :param num_water_sources: Number of Water Sources
        :param num_field_combinations: Number of possible field configurations (all possible mixes of field components)

        :returns: Tuple of logging templates

        For a Farm with two fields and two water sources:

        c_log_template:

            Stores the :math:`c` left hand values for each field combination

            ========================  ========================  ========================  ========================
            Field 1, Water Source 1   Field 1, Water Source 2   Field 2, Water Source 1   Field 2, Water Source 2
            ========================  ========================  ========================  ========================
            Possible Profit per Ha    Possible Profit per Ha    Possible Profit per Ha    Possible Profit per Ha
            ========================  ========================  ========================  ========================

        b_ub_log_template:

            Stores the :math:`b_{ub}` right hand upper bound constraints for each field combination

            ========================  ========================  ========================  ========================
            Field 1, Water Source 1   Field 1, Water Source 2   Field 2, Water Source 1   Field 2, Water Source 2
            ========================  ========================  ========================  ========================
            Possible Irrigation Area  Possible Irrigation Area  Possible Irrigation Area  Possible Irrigation Area
            ========================  ========================  ========================  ========================

        b_eq_log_template:

            Stores the :math:`b_{eq}` right hand equality constraints for each field combination
            
            If a field system is not implemented, it is because the irrigation system is being up/down graded \\
            (note that this is different from a fallow field)

            In such a case, the Field Area is enforced to its maximum area to factor in irrigation upgrade cost across \\
            the entire field.

            If equality constraints do not apply, then the value is left as NaN

            ========  ========  ==========
            Field 1   Field 2   Total Area
            ========  ========  ==========
            Max Area  Max Area  Total Area
            ========  ========  ==========
            
        """

        num_field_combinations = len(field_combinations.index) 
        c_log_template = pd.DataFrame(columns=['max_area', 'bounds'], index=[i for i in xrange(num_field_combinations)])
        b_ub_log_template = pd.DataFrame(index=[0])
        b_eq_log_template = pd.DataFrame(index=xrange(len(field_combinations.columns)))
        return (c_log_template, b_ub_log_template, b_eq_log_template)

    #End genLogTemplates

    def setLogTemplates(self, field_combinations):

        self.c_log_template, self.b_ub_log_template, self.b_eq_log_template = self.genLogTemplates(field_combinations)

    #End setLogTemplates()

    def generateFieldAub(self, c_coefs, num_set):

        """
        For scipy linprog, generates the left hand side upper bound (A_ub) constraints for the given left hand side coefficients

        linprog function expects inputs in the form of

        * c = [List of Static values]

        * A_ub = [List of Lists, Upper bound constraints for the left hand side of equation]

        * b_ub = [Upper bound constraints for the right hand side of equation]

        A_ub has to be the same length as c_coefs, as does b_ub

        objective function may be:
        
        .. math::
            2x_{1} + 2x_{2} + 1x_{3}

        s.t.

        .. math::

            x_{1} + x_{2} + x_{3} \leqslant 100 \\\\
            x_{1}                 \leqslant 25 \\\\
                    x_{2}         \leqslant 20 \\\\
                            x_{3} \leqslant 10

        Then::

            c = [2, 2, 1]
            A_ub = [[1, 1, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
            b_ub = [100, 25, 20, 10]

        :param c_coefs: array-like representing :math:`c`
        :param num_set: Number of items in a grouping of :math:`c`

        :returns: A_ub constraints
        :return type: list

        """

        num_coefs = len(c_coefs)
        ret = []
        for i in xrange(0, num_coefs, num_set):
            temp_list = [y for y in xrange(i, i+(num_set))]

            ret.extend([[1 if x in temp_list else 0 for x, val in enumerate(c_coefs)]])
        #End for

        return ret
    #End generateFieldAub()

    def genAubs(self, c_log, water_sources):
        """
        Generate A upper bounds for SciPy LP function based on generated c values
        """

        temp_c = c_log.drop(['max_area', 'bounds'], axis=1)

        A_ub = [0, ] * len(temp_c.columns)

        #Generate Aubs for case in which a single field is used with a single water source
        A_ub = self.generateFieldAub(A_ub, 1)

        #Generate list of lists, '1' set for each Field-WaterSource combination
        A_ub.extend(self.generateFieldAub(A_ub[0], len(water_sources)))

        t = temp_c.copy()
        t_mask = ((np.isnan(t)) == False)
        t = t_mask.applymap(lambda x: 1 if x else 0).as_matrix()

        A_ub = np.append(A_ub, t, axis=0)

        #Fields are completely used
        # if len(t[0]) > len(water_sources):
        #     A_ub = np.append(A_ub, [[1, ]*len(t[0])], axis=0)
        # #End if

        return A_ub
    #End genAubs()

    def genAllAubs(self, fields_combinations, crops, water_sources):

        """
        Generate left-hand upper bound constraints for use with SciPy Linear Programming function

        :param fields_combinations: Pandas Dataframe of field combinations to consider
        :param crops: List of crops to consider for each field
        :param water_sources: List of water sources to consider

        """

        num_fields = len(fields_combinations.columns)
        num_crops = len(crops)
        num_water_sources = len(water_sources)

        num_fields_water_sources = (num_fields * num_crops) * num_water_sources

        #Temp c to generate A_ub as this only needs to be done once
        temp_c = [0 for f in xrange(num_fields_water_sources)]
        self.c_length = len(temp_c) #Store for later use

        #Generate list of lists, '1' set for each Field-Crop-WaterSource combination
        A_ub = self.generateFieldAub(temp_c, 1)
        A_ub.extend(self.generateFieldAub(temp_c, num_water_sources))

        #Set '1' for each active Field-Crop combination
        if num_crops > 1:
            for row in fields_combinations.itertuples():
                t = []
                for Field in row[1:]:
                    for f in crops:
                        for WS in water_sources:
                            t.append(1 if f == Field.name and Field.Crop.name in crops[f] else 0)
                        #End for
                    #end for
                #End for
                A_ub.append(t)    
            #End for

        #Set '1' for each field-WaterSource combination
        if num_fields > 1:
            A_ub.extend(self.generateFieldAub(temp_c, num_fields_water_sources))
        #End if

        return A_ub

    #End genAllAubs()



    def old_genAllAubs(self, num_fields, num_water_sources):

        """
        Generate left-hand upper bound constraints for use with SciPy Linear Programming function

        Does not consider combinations of crops as this is taken as part of the field configuration

        :param num_fields: Number of fields to consider
        :param num_water_sources: Number of water sources to consider

        """

        num_fields_water_sources = num_fields * num_water_sources

        #Temp c to generate A_ub as this only needs to be done once
        dummy_c = [0 for f in xrange(num_fields_water_sources) ]

        self.c_length = len(dummy_c)

        A_ub = self.generateFieldAub(dummy_c, 1)
        A_ub.extend(self.generateFieldAub(dummy_c, num_water_sources))

        #A_ub.extend(self.generateFieldAub(dummy_c, num_fields))

        # if num_crops > 1:
        #     A_ub.extend(self.generateFieldAub(dummy_c, (num_fields * num_fields)))
        # #End if

        if num_fields > 1:
            A_ub.extend(self.generateFieldAub(dummy_c, num_fields_water_sources))
        #End if

        self.A_ub = A_ub

        return A_ub

    #End genAllAubs()

    def runLP(self, results, c_bnds, A_ub, b_ub_log, b_eq_log, fields, water_sources):

        """
        :params results: Pandas Dataframe of possible field combinations, used to store LP results
        :params c_bnds: Pandas dataframe of c coefficients and bounds for each field and water source
        :param A_ub: left hand side upper bounds
        :param b_ub: right hand side upper bounds
        """

        f = []
        for field in fields:
            f += fields[field].tolist()
        #End for

        fields = f

        if (type(results) != pd.DataFrame) or results.empty:
            results = c_bnds.drop(["max_area", "bounds"], axis=1)
            results["profit"] = np.zeros
            results["farm_area"] = np.zeros
            results["area_breakdown"] = np.zeros

        #Build list of c, b_ub, and bounds for each combination of fields
        temp_df = c_bnds.drop("max_area", axis=1)

        c_length = len(A_ub[0])

        for row in c_bnds.itertuples():

            i = row.Index

            #Skip rows that are all NaNs
            if all( np.isnan(x) for x in row[1:] ):
                continue
            #End if

            c = []

            for j in temp_df.iloc[i]:
                if (type(j) is not list) and (type(j) is not tuple):
                    c.append(j if np.isnan(j) == False else 0)
                elif type(j) is list:
                    b_ub = j
                elif type(j) is tuple:
                    bounds = j
            #End for

            #Insert a list at an index as we
            #need to include bounds for each GW+SW combination

            #b_ub = b_ub_log.iloc[0].tolist()
            b_ub_list = b_ub_log.iloc[0].tolist()
            b_ub = map(lambda x: min(sum(x * b_ub_list), c_bnds['max_area'][0]), A_ub)

            assert len(A_ub) == len(b_ub), "Number of A ub rows must be equal to number of elements in b_ub"

            try:
                b_eq = b_eq_log.iloc[i].tolist()
            except IndexError:
                b_eq = []
            #End try

            #If there is only one equality constraint, ensure that it matches possible farm area
            #LP crashes out if this is not set
            if (len(b_eq) == 1):
                b_eq[0] = bounds[1]
            #End if

            if len(fields) > 1:
                #b_ub.append(c_bnds.iloc[i]['max_area'])
                A_eq = A_ub[c_length:-1]
            else:
                A_eq = A_ub[c_length:]
            #End if

            try:

                bounds = [(0, c_bnds['max_area'][0]) for b in b_ub_list ]
                #bounds = [(0, min(b, c_bnds['max_area'][0])) for b in b_ub_list]

                A_eq = [A_eq[j] for j in xrange(len(b_eq)) if np.isnan(b_eq[j]) == False]
                b_eq = [x for x in b_eq if str(x) != 'nan'] #Template is copied from b_ub which has extra elements; remove the unneeded entries

                if (len(A_eq) == 0) and (len(b_eq) == 0):
                    A_eq = None
                    b_eq = None
                #End if

                # assert len(A_eq) == len(b_eq), "Number of equality constraints do not match ({A} != {b}, A_eq != b_eq)".format(A=len(A_eq), b=len(b_eq))

                res = lp(c=c, A_ub=A_ub, A_eq=A_eq, b_ub=b_ub, b_eq=b_eq, bounds=bounds)
            except (ValueError, IndexError) as e:
                print "====================="
                print c_bnds
                print "c: ", c
                print "A_ub: ", A_ub
                print "b_ub: ", b_ub
                print "--------------"
                print "A_ub[c]: ", A_ub[c_length:]
                print "A_eq: ", A_eq
                print "b_eq: ", b_eq
                print "Bounds:", bounds

                print "b_eq_log: "
                print b_eq_log

                print len(c)
                print len(A_ub)
                print len(b_ub)

                print "===================\n"
                print e
                print e.args
                print "===================\n"

                import sys; sys.exit('Error occured during LP')
            #End try

            if res.success is False:
                print "-------------------"
                print res
                print "c: ", c
                print "A_ub: ", A_ub
                print "b_ub", b_ub
                print "A_eq", A_eq
                print "b_eq", b_eq
                print "bounds: ", bounds
                print "c_length: ", c_length
                # print Field.name, Field.Irrigation.name, Field.Crop.name, Field.area
                print "------------------\n\n"
                print "LP failed!"
                import sys; sys.exit()
            #End if

            #import sys; sys.exit('Exit inside LP run for debug')
            row = np.append(res.x, [res.fun, sum(res.x)]).tolist() + ['| '.join(str(e) for e in res.x.tolist())]

            results.loc[i] = row

        #End for

        return results

    #End runLP()




