import numpy as np
from osgeo import gdal
import sys

class GWModelBuilder(object):

	"""
	The GWModelBuilder class contains a number of useful tools for building numerical 
	groundwater models in packages such as MODFLOW. 
	"""
	mesh_types = ['structured', 'unstructured']

    def __init__(self, name=name, model_type=model_type, mesh_type=mesh_type, GCS=GCS, VCS=VCS, data_folder=data_folder, **kwargs):

        """
        :param name: Model name
        :param model_type: Type of model, e.g. MODFLOW (makes use of flopy), HGS (uses pyHGS ... which is not developed yet ;) ) 
        :param mesh_type: type of mesh to be used in the model, i.e. sturctured or unstructured
        :param GCS: geographical coordinate system, e.g. GDA_1994_Lambert_Conformal_Conic
        :param VCS: vertical coordinate system, e.g. Australian Height Datum (AHD)
        :param data_folder: Folder to get model data from
        :param model_mesh: Mesh for the model.
        """

        self.name = name
        self.model_type = model_type  
        self.mesh_type = mesh_type
        self.geographical_coordinate_system = GCS
        self.vertical_coordinate_system = VCS
        self.data_folder = data_folder

        # OTHER variables

        self.model_mesh = None

    def set_model_grid_boundary(self, model_boundary):
        """
        Function to set the model boundary for use in defining model structure and parameters.
        """
        if self.mesh_type == 'structured':
            
            pass

        elif self.mesh_type == 'unstructured':
            print 'Mesh type unstructured unsupported at the moment'
            sys.exit(1) 

        return self.model_mesh

    def read_rasters(self, files, path=None):
    	"""
    	Reads in raster files, e.g. for hydrostratigraphy.
    	
    	:param files: List of file names for the rasters that are to be read in.
    	:param path: Path of the files, which is optional, default path is working directory
    	"""
        rasters = {}

        for raster in files:
            ds = gdal.Open(path + raster)

            if ds is None:
                print 'Could not open ' + path + raster
                sys.exit(1)    

            raster_details  = [ds.RasterXSize]
            raster_details += [ds.RasterYSize]       
            raster_details += [ds.GetRasterBand(1).GetNoDataValue()]       
            raster_details += [ds.GetGeoTransform()]
            raster_details += [ds.GetProjection()] 
            raster_details += [np.array(ds.ReadAsArray())]
            rasters[raster] = raster_details    

        return rasters



    def read_polyline(self, filename, path=None):     
    	"""
    	Read in polyline data, e.g. for stream definition
    	
    	:param filename: filename for the polyline that is to be read in.
    	:param path: Path of the files, which is optional, default path is working directory
    	"""

    def read_points_data(self, filename, path=None):     
    	"""
    	Read csv files containing points data, e.g. well locations, screening depths.
    	
    	:param filename: filename for the point data that is to be read in.
    	:param path: Path of the files, which is optional, default path is working directory
    	"""
