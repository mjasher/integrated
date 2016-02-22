#Management
from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Farm.Management.Manager import FarmManager
from integrated.Modules.Farm.Fields.Field import FarmField
from integrated.Modules.Farm.Fields.Soil import SoilType
from integrated.Modules.Farm.Irrigations.IrrigationPractice import IrrigationPractice

#Linear programming
from scipy.optimize import linprog as lp

#remove this when ready
from random import randint

import pandas as pd
import numpy as np

class PlasticManager(FarmManager):

    """
    Plastic Farm Manager - Highly opportunistic management style

    # .. inheritance-diagram:: integrated.Modules.Farm.Farms.Management.FarmManager
    #    :parts: 2

    """

    def __init__(self, Farm, water_sources, storages, irrigations, crops):

        """
        :param Farm: Farm Object representing the Farm to manage
        """

        #Call parent constructor
        FarmManager.__init__(self, Farm, water_sources, storages, irrigations, crops)
        #Python 3 version of the above
        #super().__init__(Farm, water_sources, irrigations, crops)

    #End __init__()

    # def determineFieldCombinations(self, years_ahead):

    #     import copy

    #     #TEST PURPOSES ONLY
    #     current_area = 40
    #     water_licence = 300

    #     state = {}

    #     storages = self.storages
    #     irrigations = self.irrigations
    #     water_sources = self.water_sources
    #     crops = self.crops

    #     for Storage_obj in storages:

    #         Storage = copy.deepcopy(Storage_obj)

    #         if Storage.implemented is not True:
    #             Storage.implemented = True
    #         #End if

    #         for Irrigation_obj in irrigations:

    #             Irrigation = copy.deepcopy(Irrigation_obj)

    #             # for water_source in water_sources:1

    #                 # flow_rate_Lps = Field.calcFlowRate(Irrigation.flow_ML_day)
    #                 # pumping_cost_per_Ha = water_source.calcGrossPumpingCostsPerHa(flow_rate_Lps, est_irrigation_water_ML_per_Ha)



    #             for n in xrange(years_ahead):

    #                 #Use Linear Programming to determine best crop and water source combination to use for this field
    #                 #"best" is determined by the lowest negated crop profit

    #                 if Irrigation.implemented is False:
    #                     Irrigation.implemented = True

    #                 c = [ crop.variable_cost_per_Ha - (crop.yield_per_Ha * crop.price_per_yield) for crop in crops]

    #                 #Condition for each crop (must choose 1 crop)
    #                 #[1, 0, 0], [0, 1, 0], ... represents 1*x[1] + 0*x[2] + 0*[x3] is bounded by the corresponding row in b_ub
    #                 #[1, 1, 1] for each crop: 1*x[1] + 1*x[2] + 1*x[3] <= current_area
    #                 A_ub = [[1 if i == j else 0 for j, v in enumerate(crops)] for i in xrange(0, len(crops))]

    #                 #If choosing multiple crops, the sum of the crop area must not exceed max area
    #                 A_ub.extend([[1 for i in c]])

    #                 #Constraints to producing negated profit
    #                 #Crop choice(s) cannot exceed the maximum possible area
    #                 b_ub = [min(water_licence/crop.water_use_ML_per_Ha, current_area) for crop in crops]
    #                 b_ub.extend([current_area])

    #                 bounds = ((0, current_area), ) * len(crops)

    #                 res = lp(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, options={"disp": False})

    #                 crop_indexes = [i for i, x in enumerate(res.x) if x > 0.0]
    #                 state_name = "{s}_{i}".format(s=Storage.name, i=Irrigation.name)

    #                 farm_area = sum(res.x)

    #                 irrig_imp = Irrigation.calcCapitalCost(farm_area)
    #                 irrig_cost_per_Ha = Irrigation.calcTotalCostsPerHa()
    #                 storage_cost = Storage.calcTotalCostsPerHa(farm_area) #((storage_imp + Storage.maintenance)*Storage.capacity)

    #                 crop_choices = []
    #                 for i in crop_indexes:
    #                     crop_choices.append(crops[i])
    #                     state_name = "{cn}_{nc}".format(cn=state_name, nc=crops[i].name)
    #                 #End for

    #                 if state_name not in state:

    #                     state[state_name] = pd.DataFrame({
    #                         'farm_area': 0,
    #                         'crop_profit': 0,
    #                         'net_profit': 0,
    #                         'storage_cost': 0,
    #                         'irrig_cost': 0,
    #                         'crop_cost': 0,
    #                         'total_costs': 0,
    #                         'total_profit': 0}, 
    #                         index=[i for i in xrange(years_ahead)]
    #                     )
    #                 #End if

    #                 if irrig_imp > 0:

    #                     costs = ((storage_imp + storage.maintenance)*storage.capacity) + (irrig_imp * farm_area)
    #                     values = {
    #                         'farm_area': farm_area,
    #                         'crop_profit': 0,
    #                         'net_profit': 0 - costs,
    #                         'storage_cost': (storage_imp + storage.maintenance)*storage.capacity,
    #                         'irrig_cost': (irrig_imp + irrigation.maintenance)*farm_area,
    #                         'crop_cost': 0,
    #                         'total_costs': 0,
    #                         'total_profit': 0
    #                     }

    #                 else:

    #                     crop_costs = 0
    #                     for i in crop_choices:
    #                         crop_costs += i.variable_cost_per_Ha
    #                     #End for

    #                     crop_costs = crop_costs * farm_area

    #                     values = {
    #                         'farm_area': farm_area,
    #                         'crop_profit': -res.fun,
    #                         'net_profit': (-res.fun) - (irrig_cost_per_Ha * farm_area) + storage_cost, #Crop costs already factored in
    #                         'storage_cost': storage_cost,
    #                         'irrig_cost': irrig_cost_per_Ha,
    #                         'crop_cost': crop_costs,
    #                         'total_costs': 0,
    #                         'total_profit': 0
    #                     }

    #                 #End if

    #                 state[state_name].update( pd.DataFrame(values, index=[n]))

    #             #End for
    #         #End for
    #     #End for

    #     for i, df in state.iteritems():

    #         df['total_profit'] = df['net_profit'].cumsum()
    #         df['total_costs'] = df['crop_cost'] + df['irrig_cost'] + df['storage_cost']

    #         print i
    #         print df
    #     #End for
    # #End determineFieldCombinations

    def dp_dev_all_fields(self):

        names = []
        c = [] #Initial values of coefficients

        #Should be list of lists, each list representing an constraining equation
        #e.g. [[1, 0], [0, 1], [1, 1]]
        A_ub = [] 

        #List of upper bounds of the equations represented in A_ub
        #e.g. [50, 50, 100]
        b_ub = []

        #Using the examples above
        # 1x_{1} + 0x_{2} <= 50
        # 0x_{1} + 1x_{2} <= 50
        # 1x_{1} + 1x_{2} <= 100

        bounds = [] #Bounds for any answer

        water_sources = self.water_sources

        pos_in_c = []

        num_combinations = len(self.Farm.fields) * len(self.storages) * len(self.irrigations) * len(self.crops) * len(self.water_sources)
        total_farm_area = 0

        #Generate the equations for each field-crop-storage-water_source-irrigation combination
        for Field in self.Farm.fields:

            for Storage in self.storages:
                for Irrigation in self.irrigations:

                    for Crop in self.crops:

                        temp_counter = 0

                        est_irrigation_water_ML_per_Ha = self.estIrrigationWaterUse(Crop.water_use_ML_per_Ha, Irrigation.irrigation_efficiency)

                        for water_source in self.water_sources:
                            #total costs - total margin
                            #Storage costs added later for entire farm
                            total_costs = Crop.variable_cost_per_Ha + \
                                            water_source.calcTotalCostsPerHa(est_irrigation_water_ML_per_Ha) + \
                                            Irrigation.calcTotalCostsPerHa() 
                            
                            c.extend([total_costs - Crop.calcTotalCropGrossMarginsPerHa()])
                            pos_in_c.append(len(c))

                            names.append("{F}_{S}_{I}_{C}_{ws}".format(F=Field.name, S=Storage.name, I=Irrigation.name, C=Crop.name, ws=water_source.name))

                            #Needs to constrain this...
                            # bounds.append((0, min(possible_irrigation_area, available_water_per_Ha)))

                            max_possible_area_for_field = water_source.entitlement / est_irrigation_water_ML_per_Ha

                            #Keep track of how many water sources 
                            temp_counter += 1
                            
                            #Unbounded
                            bounds.append((0, None))

                            b_ub.extend([min(max_possible_area_for_field, Field.area)])

                        #End water_source

                        # b_ub.extend([Field.area])
                        # A_ub.extend(self.generateFieldAub([0]*num_combinations, len(self.water_sources)))

                    #End crop

                    # b_ub.extend([Field.area])
                    # A_ub.extend(self.generateFieldAub([0]*num_combinations, len(self.crops))) 

                #End irrigation

                # b_ub.extend([Field.area])
                # A_ub.extend(self.generateFieldAub([0]*num_combinations, len(self.irrigations))) 

            #End storage

            b_ub.extend([Field.area]*(len(self.irrigations)+len(self.crops)))

            total_farm_area += Field.area

            #Field area cannot exceed physical size of field
            # b_ub.extend([Field.area]*len(self.storages)*len(self.irrigations)*len(self.water_sources*len(self.crops)))

        #End field

        
        # A_ub.extend(self.generateFieldAub(c, len(self.crops)))
        # A_ub.extend(self.generateFieldAub(c, len(self.water_sources)))

        # A_ub.extend(self.generateFieldAub(c, len(self.irrigations)*len(self.crops) ))
        # A_ub.extend(self.generateFieldAub(c, len(self.irrigations)*len(self.crops)*len(self.water_sources) ))

        # A_ub.extend(self.generateFieldAub(c, len(self.storages)*len(self.irrigations)*len(self.crops)*len(self.water_sources) ))

        A_ub.extend(self.generateFieldAub([0]*num_combinations, 1))
        A_ub.extend(self.generateFieldAub([0]*num_combinations, len(self.water_sources)))
        
        A_ub.extend(self.generateFieldAub(c, num_combinations))

        print len(A_ub)
        print len(b_ub)

        # b_ub.extend([Field.area]*((len(A_ub) - len(b_ub)) - 1) )

        #Total area cannot exceed total farm area
        b_ub.extend([total_farm_area])

        print len(self.Farm.fields)*len(self.storages)*len(self.irrigations)*len(self.crops)*len(self.water_sources)

        for i in A_ub:
            print i

        print b_ub

        import pandas as pd

        name_map = pd.DataFrame(dict(names=names, vals=c))

        with pd.option_context('display.max_rows', 999, 'display.max_columns', 10):
            print name_map

        res = lp(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, options={"disp": False})

        

        print res.x
        print res.fun

        combi_indexes = [i for i, v in enumerate(res.x) if v > 0.0]

        print combi_indexes

        import pprint
        pprint.pprint([name_map.loc[v, 'names'] for v in combi_indexes])
        pprint.pprint([v for v in res.x if v > 0.0])

        # print name_map

        # print c
        # print A_ub
        # print b_ub
        # print bounds
    #End dp_dev_all_fields()

    def dpDetFieldCombi(self, years_ahead):

        #For each field
        #Get current state

        #Other possible states (other combinations of irrigations, storages)

        #For each state (current and possible), determine best crop-water source combination

        #Return results

        import itertools

        for Field in self.Farm.fields:

            #For debug purposes, see the names within each combination
            # possible_states = {
            #     'irrigations': [i.name for i in self.irrigations],
            #     'storages': [i.name for i in self.storages],
            #     'soil': [Field.Soil.name],
            #     'area': [Field.area]
            # }
            # df = pd.DataFrame(list(itertools.product(*possible_states.values())), columns=possible_states.keys() )
            # print df

            # current_state = {
            #     'irrigation': Field.Irrigation.name,
            #     'storages': Field.Storage.name
            #     'soil': [Field.Soil.name]
            # }
            # print current_state

            possible_states = {
                'irrigations': self.irrigations,
                'storages': self.storages,
                'soil': [Field.Soil],
                'area': [Field.area]
            }

            #Create a dataframe of all the possible combinations
            df = pd.DataFrame(list(itertools.product(*possible_states.values())), columns=possible_states.keys() )

            #For each possible state, calculate results; i.e. run Linear Programming

            def runLP(row):

                irrig = row['irrigations']
                store = row['storages']
                area = row['area']
                soil = row['soil']

                TempField = FarmField(name='Temp Field', storage=store, irrigation=irrig, area=area, soil=soil)

                name = "{s}_{i}".format(s=store.name, i=irrig.name)

                if name not in field_results:
                    field_results[name] = {} 
                #End if

                #790 is the estimated yearly rainfall
                for n in xrange(years_ahead):
                    temp_results, lp_res = self.determineFieldCombinations(TempField, 790)

                    for crop_type, results in temp_results:

                        if crop_type not in field_results[name]:
                            field_results[name][crop_type] = pd.DataFrame({'total_profit': 0}, index=[i for i in xrange(years_ahead)])

                        field_results[name].update(pd.DataFrame({'total_profit':temp_results['total_profit']}, index=[n]))    

                    print temp_results
                    

                # return self.determineFieldCombinations(TempField, 790)
            #End runLP()

            
            field_results = {}
            #state[state_name].update( pd.DataFrame(values, index=[n]))

            field_results

            #This apply call adds to field results
            df.apply(runLP, axis=1)

            for f, crop_results in field_results.iteritems():
                print f
                print "----------------"

                for crop_type, results in crop_results.iteritems():
                    print crop_type

                    print "---- Total Profit ----"
                    print results['total_profit']

                    # print "---- Groundwater ----"
                    # print pd.DataFrame(results['groundwater'], index=[0])
                    # print "---- Surface Water ----"
                    # print pd.DataFrame(results['surface_water'], index=[0])
                    print "======================="





#End FarmManagement()