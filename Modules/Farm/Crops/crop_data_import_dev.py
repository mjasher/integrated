
if __name__ == '__main__':
    import pandas as pd
    import simplejson as json

    # t = pd.read_json('data/variables/wheat.json')

    data_file = 'data/variables/wheat.json'

    with open(data_file, 'rb') as json_data:
        d = json.load(json_data)
        json_data.close()

        plant_info = d['planting_info']

        crop_coefs = pd.DataFrame(plant_info)

        crop_coefs = pd.DataFrame(dict(Kc=crop_coefs.loc[1].values), index=crop_coefs[0:].loc[0]).sort_index()

        d['planting_info'] = None

        print d

        #TODO: Extract best guess values and convert to ParameterSet()
