import pandas as pd

#Linear programming
from scipy.optimize import linprog as lp

class LpInterface(object):


    def genLogTemplates(self, num_field_water_sources, num_field_combinations):

        """
        Generate Pandas DataFrames to store LP :math:`c` and right hand upper bound (b_ub) coefficients

        :param num_field_water_sources: Number of field and water source combinations (num fields * num water sources)
        :param num_field_combinations: Number of possible field configurations (all possible mixes of field components)

        """

        lp_log_template = pd.DataFrame(columns=['max_area', 'bounds'], index=[i for i in xrange(num_field_combinations)])
        b_ub_log_template = pd.DataFrame(columns=[i for i in xrange(0, num_field_water_sources )])

        return (lp_log_template, b_ub_log_template, b_ub_log_template.copy())

    #End genLogTemplates

    def setLogTemplates(self, num_field_water_sources, num_field_combinations):

        lp_log, b_ub_log, b_eq_log = self.genLogTemplates(num_field_water_sources, num_field_combinations)

        self.lp_log_template = lp_log
        self.b_ub_log_template = b_ub_log
        self.b_eq_log_template = b_eq_log

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

    def genAllAubs(self, num_fields, num_water_sources):

        num_fields_water_sources = num_fields * num_water_sources

        #Temp c to generate A_ub as this only needs to be done once
        dummy_c = [0 for f in xrange(num_fields_water_sources) ]

        self.c_length = len(dummy_c)

        A_ub = self.generateFieldAub(dummy_c, 1)
        A_ub.extend(self.generateFieldAub(dummy_c, num_water_sources))
        A_ub.extend(self.generateFieldAub(dummy_c, num_fields_water_sources))

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

        #Build list of c, b_ub, and bounds for each combination of fields
        temp_df = c_bnds.drop("max_area", axis=1)
        c_length = self.c_length

        for i, row in c_bnds.iterrows():
            c = []

            for j in temp_df.iloc[i]:
                if (type(j) is not list) and (type(j) is not tuple):
                    c.append(j)
                elif type(j) is list:
                    b_ub = j
                elif type(j) is tuple:
                    bounds = j
            #End for
            # del temp_df

            #Insert a list at an index as we
            #need to include bounds for each GW+SW combination
            b_ub = b_ub_log.iloc[i].tolist()
            b_ub = [x for x in b_ub if str(x) != 'nan'] #Template is copied from b_ub which has extra elements; remove the unneeded entries
            b_ub = b_ub[0:c_length] + [f.area for f in fields] + b_ub[c_length: ]
            b_ub.append(c_bnds.iloc[i]['max_area'])

            b_eq = b_eq_log.iloc[i].tolist()
            b_eq = [x for x in b_eq if str(x) != 'nan'] #Template is copied from b_ub which has extra elements; remove the unneeded entries
            b_eq.append(sum(b_eq)) #Use of all fields is bounded by total possible irrigation area as constrained by water availability

            try:
                bounds = (bounds, )*c_length
                res = lp(c=c, A_ub=A_ub, A_eq=A_ub[c_length:], b_ub=b_ub, b_eq=b_eq, bounds=bounds)
            except ValueError as e:
                print "====================="
                print c_bnds
                print c
                print A_ub
                print b_ub
                print A_ub[c_length:]
                print b_eq
                print bounds

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
                print res
                print c
                print A_ub
                print b_ub
                print A_ub[c_length:]
                print b_eq
                print bounds
                print c_length
                print "------------------\n\n"
                import sys; sys.exit('LP Failed!')

            k = 0
            for Field in fields:
                for WS in water_sources:
                    results.loc[i, Field.name+" "+WS.name+" Area"] = res.x[k]
                    k += 1
                #End for
            #End for


            results.loc[i, 'profit'] = res.fun
            results.loc[i, 'farm_area'] = sum(res.x)
            results.loc[i, 'area_breakdown'] = '| '.join(str(e) for e in res.x.tolist())

        #End for

        return results

    #End runLP()




