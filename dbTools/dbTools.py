from postgisUtil import postgisUtil
from datetime import date
import numpy as np

topo_table_name = {"Merced": "Merced",
                   "Tuolumne": "Tuolumne",
                   "Tuolumne_survey": "Tuolumne",
                   "Tuolumne_survey_plus": "MBTB"}

class dbTools:
    def __init__(self, database, username):
        self.db = postgisUtil(database=database, username=username)

    # Load topographic features from the database
    def load_features(self, basin, sensor=False, exclude_null=True):
        # Please note that the indices here are indices of python, starting from 0
        features = ['DEM', 'SLP', 'ASP', 'VEG']

        if not sensor:
            if basin == "Tuolumne_survey_plus":
                basin = "Tuolumne"
            for i, feature in enumerate(features):
                feature_array = self.db.query_map(feature, 'topo', topo_table_name[basin].lower())
                if i == 0:
                    grid_y, grid_x = np.meshgrid(range(feature_array.shape[0]), range(feature_array.shape[1]), indexing='ij')
                    grid_y_array, grid_x_array = grid_y.flatten(), grid_x.flatten()
                    feature_space = np.column_stack((grid_y_array, np.column_stack((grid_x_array, feature_array.flatten()))))
                else:
                    feature_space = np.column_stack((feature_space, feature_array.flatten()))
            if exclude_null:
                feature_space = feature_space[feature_space[:, 2] >= 0]
            feature_space[feature_space < 0] = np.nan
        else:
            feature_array = self.db.geoms_table_to_map_pixel_values(features,
                                                                    'sensors',
                                                                    basin.lower(),
                                                                    'site_coords',
                                                                    'topo',
                                                                    topo_table_name[basin].lower())

            spatial_feature = self.db.geoms_table_to_map_pixel_indices(features[0],
                                                                       'sensors',
                                                                       basin.lower(),
                                                                       'site_coords',
                                                                       'topo',
                                                                       topo_table_name[basin].lower())

            feature_space = np.column_stack((spatial_feature, feature_array))
        return feature_space


    def load_swe(self, date_obj, basin, schema_name, sensor=False):
        if type(date_obj)==str:
            date_str = date_obj
        elif type(date_obj)==date:
            date_str = date_obj.strftime("%Y%m%d")
        else:
            print "The input date_obj dtype is not supported"
            return
        if not sensor:
            if basin == "Tuolumne_survey_plus":
                basin = "Tuolumne"
            DEM = self.db.query_map("DEM", 'topo', topo_table_name[basin].lower())
            swe = self.db.query_map(date_str, schema_name, basin.lower())
            data_array = np.column_stack((DEM.flatten(), swe.flatten()))
            data_array = data_array[data_array[:, 0] >= 0]
            data_array = data_array[:, 1]
        else:
            data_array = self.db.geoms_table_to_map_pixel_values(date_str,
                                                                'sensors',
                                                                basin.lower(),
                                                                'site_coords',
                                                                schema_name,
                                                                basin.lower())
        return data_array

    def insert_sensor_locations(self, basin, location_idx):
        srid = self.db.get_srid('DEM', 'topo', topo_table_name[basin].lower())
        self.db.create_table(basin.lower(), 'sensors', ['site_id'], ['SERIAL'])
        self.db.add_geometry_column('sensors', basin.lower(), 'site_coords', srid, 'POINT', 2, use_typemod='false')
        location_coords = self.db.convert_idx_to_coords('DEM', location_idx[1], location_idx[0], 'topo',
                                                        topo_table_name[basin].lower())
        self.db.add_geoms_to_table(location_coords[0], location_coords[1], srid, 'sensors', 'site_locs', 'site_coords')

    def insert_swe(self, raster_fn, date_obj, basin, schema_name, schema_exist=True, table_exist=True):
        # if schema_exists == false, which means that you have to set table_exist to False
        if type(date_obj) != str:
            date_str = date_obj.strftime("%Y%m%d")
        else:
            date_str = date_obj
        if not schema_exist:
            self.db.create_schema(schema_name)
        if not table_exist:
            self.db.load_map_to_db(raster_fn, date_str, schema_name, basin.lower(), table_exist=table_exist)
        else:
            self.db.load_map_to_db(raster_fn, date_str, schema_name, basin.lower())



