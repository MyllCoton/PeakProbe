from __future__ import division
import sys,math,ast,copy
import numpy as np
class Selectors:
     """
     Class for organizing, selecting, and broadcasting data appropriately for all training/classifying functions
     Population (obss = observed sulfate or phostphate, obsw = observed water)
     by resolution cutoffs
     by omit, batch, etc
     raw data must have a data column defined as "ori" and another as "omit"
     """
     def __init__(self,raw_data):
          #Column names and formats for structured arrays, along with corresponding np dtypes
          #some defined types contain all data, others contain only feature data

          #std_view = raw 19 features, no info
          #pca_view = pca 19 features, no info
          #alldata_input = 19 raw features, 12 info columns (reso,batch,omit,map densities, etc.)
          #alldata_pca = same as alldata_input, but features are pca transformed
          #raw_dtype converts from structured array to 19 float columns
          self.std_view_col = ['ccSf','ccWf','ccS2','ccW2','ccSifi','ccSifo','ccSi2i','ccSi2o','ccSifr','ccSi2r',
                               'ccWif','ccWi2','ccSf60','sdSf60','ccS260','sdS260','vf','v2','2fofc_sigo']
          self.std_view_formats = (np.float32,np.float32,np.float32,np.float32,np.float32,np.float32,np.float32,
                                   np.float32,np.float32,np.float32,np.float32,np.float32,np.float32,np.float32,
                                   np.float32,np.float32,np.float32,np.float32,np.float32)
          self.std_view_dtype = np.dtype(zip(self.std_view_col,self.std_view_formats))

          #after pca transformation, data columns have new name, but format is unchanged
          self.pca_view_col = ['RX0','RX1','RX2','RX3','RX4','RX5','RX6','RX7','RX8','RX9','RX10',
                               'RX11','RX12','RX13','RX14','RX15','RX16','RX17','RX18']
          self.pca_view_dtype = np.dtype(zip(self.pca_view_col,self.std_view_formats))

          #array for normalized and pca transformed data
          self.proc_array_col = ['id','ori','res','ccSf','ccWf','ccS2','ccW2','ccSifi','ccSifo','ccSi2i','ccSi2o','ccSifr','ccSi2r',
                                 'ccWif','ccWi2','ccSf60','sdSf60','ccS260','sdS260','vf','v2','2fofc_sigo',
                                 'RX0','RX1','RX2','RX3','RX4','RX5','RX6','RX7','RX8','RX9','RX10',
                                 'RX11','RX12','RX13','RX14','RX15','RX16','RX17','RX18'] 
          self.proc_array_fmt = ['S16','S3','f2','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4',
                                 'f4','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4',
                                 'f4','f4','f4','f4','f4','f4','f4','f4','f4','f4','f4']


          self.proc_array_dtype = np.dtype(zip(self.proc_array_col,self.proc_array_fmt))

          #some numerical routines don't like structured arrays, give raw dtype
          self.raw_dtype = np.dtype(str(len(self.std_view_formats))+"f4")


          self.features_csv_format = ['%8g','%8g','%8g','%8g','%8g','%8g','%8g','%8g',
                                      '%8g','%8g','%8g','%8g','%8g','%8g','%8g','%8g',
                                      '%3s','%4g','%4g','%8g','%4g','%12s','%1d','%3d','%1d','%4g',
                                      '%4g','%4g','%4g','%4g','%4g','%4s']
          self.results_csv_format = ['%12s','%4g','%8g','%8g','%8g','%8g','%8g','%8g','%8g','%8g','%2g']
          self.results_csvin_dtype = [('id','S16'),('res','f8'),('score','f4'),('prob','f4'),
                                      ('llgS','f4'),('llgW','f4'),('chiS','f4'),('chiW','f4'),     
                                      ('fchi','f4'),('kchi','f4'),('rc','i1')]



          if raw_data is None: #allow for instantantiation without data, pass None for initializing without actual data
               pass
          else:
               self.setup_masks(raw_data)

     def setup_masks(self,raw_data):
          #selects all that is not XXX
          original_residue = np.core.defchararray.strip(raw_data['ori'])
          #selects sulfate, then phosphate, then combines
          self.obss_bool = np.logical_or(original_residue == "SO4",original_residue == "PO4")
          #selects water
          self.obsw_bool = original_residue == 'HOH'
          #selects data flagged for omit, bad structures, etc.
          if 'omit' in raw_data.dtype.names:
               if raw_data['omit'].dtype == '|S32':
                    self.omit_bool = np.array(raw_data['omit'] == 'True').astype(np.bool)
               if raw_data['omit'].dtype == 'bool':
                    self.omit_bool = raw_data['omit']
          else:
               self.omit_bool = np.zeros(raw_data.shape[0],dtype=np.bool_)

          #group data into populations
          self.included_data_bool = np.invert(self.omit_bool)
          self.inc_obss_bool = np.logical_and(self.included_data_bool,self.obss_bool)
          self.inc_obsw_bool = np.logical_and(self.included_data_bool,self.obsw_bool)
          self.inc_sw_bool = np.logical_or(self.inc_obss_bool,self.inc_obsw_bool)
