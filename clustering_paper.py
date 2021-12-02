# -*- coding: utf-8 -*-
"""
Created on Tue Nov 23 13:46:50 2021

@author: USER
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


#missing_cond = 'interpolate' # {mean, drop, interpolate}

fn_dir = 'C:/GIT/industrial_AI'
data_dir = 'C:/BaseData/Class/2021-2/Industrial AI/Progress'
file_name = 'data_10min.csv'

os.chdir(fn_dir)

from data_function import *




for del_depth in ['non_depth', 'depth']:
    for missing_cond in ['mean', 'drop', 'interpolate']:
        
        df_clustering = load_preprocessing(data_dir, file_name, del_depth, missing_cond)
        
        # 4. Modeling function
        def modeling(model_name, n_features):
            if model_name == 'KNN':
                from pyod.models.knn import KNN as pyod_model
                model = pyod_model()
            
            elif model_name == 'ABOD':
                from pyod.models.abod import ABOD as pyod_model
                model = pyod_model()
            
            elif model_name == 'LOF':
                from pyod.models.lof import LOF as pyod_model
                model = pyod_model()
                
            elif model_name == 'CBLOF':
                from pyod.models.cblof import CBLOF as pyod_model
                model = pyod_model()    
            elif model_name == 'LODA':
                from pyod.models.loda import LODA as pyod_model
                model = pyod_model()
                
            elif model_name == 'IF': # Isolation Forest
                from pyod.models.iforest import IForest as pyod_model
                model = pyod_model()
                
            elif model_name == 'OCSVM':
                from pyod.models.ocsvm import OCSVM as pyod_model
                model = pyod_model()
                
            elif model_name == 'auto_encoder': # torch ..? 현재 실행 안됨
                from pyod.models.auto_encoder import AutoEncoder as pyod_model
                model = pyod_model(epochs=100, contamination=0.1,hidden_neurons=[int(n_features/2)])
        
        
            return model
        
        # 5. Get outlier result from outlier score
        
        def determine_outlier(rlt): # top 1% outlier score
            tmp = rlt.copy()
            tmp.sort()
            target_idx = len(tmp) - int(0.01 / (1/len(tmp)))
            target_val = tmp[target_idx]
            
            
            rlt_tf = np.array([0 for _ in range(len(rlt))])
            rlt_tf[rlt > target_val] = 1
        
            return rlt_tf
            
        
        
        # 6. Training each model and save detection result
        
        model_list = ['ABOD','LOF','CBLOF','LODA','IF','auto_encoder','OCSVM']
        
        rlt_df = pd.DataFrame({'TIME_STAMP': df['TIME_STAMP'][clustering_idx],
                               'Result':[np.nan for _ in range(np.shape(df_clustering.iloc[:,1:])[0])]})
        
        
        n_features = len(df_clustering.iloc[:,1:].to_numpy()[0])
        
        for model_name in model_list:
            model = modeling(model_name,n_features)
            model.fit(df_clustering.iloc[:,1:])
            
            rlt = model.decision_scores_
            rlt_df[model_name] = determine_outlier(rlt)
            
            
        # 7. Calculate final result
        
        tmp = [0 for _ in range(np.shape(rlt_df)[0])]
        idx = np.where(rlt_df.iloc[:,1:].sum(axis=1) >= 4)[0]
        
        for i in idx:
            tmp[i] = 1
        
        rlt_df['Result'] =  tmp
        
        rlt_df.to_csv(f'clustering_results_paper-{del_depth}-{missing_cond}.csv',index = False)
        
        # 8. Svae the result
        
        # rlt_df.to_csv('clustering_paper.csv', index = False)
        
        # 9. Result join
        
        rlt_join = pd.DataFrame({'TIME_STAMP': df_clustering['TIME_STAMP'],
                                 'Cluster': rlt_df['Result']})
        
        rlt_final = df[['TIME_STAMP', rpm]]
        
        rlt_final = pd.merge(left = rlt_final, right=rlt_join, how='left', on='TIME_STAMP')
        
        
        # 10. Plot
        
        
        l = 15000
        
        for i in range(int(np.shape(rlt_final)[0]/l)+1):
            try:
                tmp = rlt_final.iloc[(i*l):((i+1)*l),:]
            except:
                tmp = rlt_final.iloc[(i*l):,:]
            
            fig_name = f'./1125/fig/{del_depth}/{missing_cond}/outlier_{str(tmp["TIME_STAMP"].tolist()[0])[:10]}-{str(tmp["TIME_STAMP"].tolist()[-1])[:10]}.png'
            
            tmp['Cluster'] = tmp['Cluster'] * tmp[rpm]
            tmp['Cluster'][tmp['Cluster']==0] = np.nan
            
            plt.rcParams['axes.grid'] = True
            plt.figure(figsize=(30,5))
            plt.plot(tmp[rpm])
            plt.plot(tmp['Cluster'], 'r^')
            plt.title(f'{tmp["TIME_STAMP"].tolist()[0]} - {tmp["TIME_STAMP"].tolist()[-1]}')
            plt.margins(x=0)
            
            plt.savefig(fig_name, dpi=200,transparent=True,bbox_inches='tight')
            plt.show()
