import numpy as np
from moneyed import Money, AUD


class FarmFinance(object):
    

    def __init__(self, currency=AUD):
        self.currency = currency
    #End init()

    def calcPumpingCostsPerML(self, fuel_per_Hour, hours_per_ML, fuel_price_per_Litre='1.25'):

        fuel_price_per_Litre = Money(fuel_price_per_Litre, self.currency)

        return (fuel_price_per_Litre * fuel_per_Hour) * hours_per_ML

    #End calcPumpingCostsPerML()

    def convertFloatToMoney(self, val):
        return Money(val, self.currency)
    #End convertFloatToMoney()

    def annualizeCapital(self, capital, discount_rate=0.07, num_years=20):

        """
        Calculates capital value per year over a given number of years

        :param capital: Amount of money in dollars ($)
        :param discount_rate: The percentage to discount future value to get present-day value; Arshad et al. (2013) used 7%
        :param num_years: Number of years for the scenario
        :returns: Annualised capital cost discounted to present day value 
        :return type: numeric
        
        """

        annuity_factor = (1 - 1/(1 + discount_rate)**num_years)/discount_rate

        if (type(capital) != str) and (type(capital) != np.number):
            return capital.apply(lambda value: Money(value/annuity_factor, self.currency))
        #End if
        
        return Money(capital/annuity_factor, self.currency)

    #End calcCapitalCostPerYear()


#End class