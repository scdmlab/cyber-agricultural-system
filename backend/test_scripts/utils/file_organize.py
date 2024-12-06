import pandas as pd
from sklearn.preprocessing import MinMaxScaler, scale
import numpy as np
import random as random
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn import metrics

from joblib import dump, load
import pickle


def read_all_features(n_feature_files, feature_filenames):
    # of n_feature_files: the number of files
    all_feaures = []

    for i in range(n_feature_files):
        df = pd.read_csv(feature_filenames[i])
        all_feaures.append(df)
    print(all_feaures[0].shape)
    return all_feaures


def select_input_years(df, current_years):
    # select the input years
    selected_features = []
    for i in range(len(current_years)):
        val_year_df = df['year'] == current_years[i]
        df_cur_year = df[val_year_df]
        df_cur_year = df_cur_year.drop(['year'], axis=1)
        selected_features.append(df_cur_year)

    return selected_features


# join the input years by common attributes (e.g. 'FIPS')
def join_by_attributs(all_selected_features,
                      all_yields,
                      current_years,
                      n_feature_files,
                      common_attribute='FIPS'):
    dfy_all = []
    # all_selected_features is a list that contains or the features
    for i in range(len(current_years)):
        dfy_this_year = all_selected_features[0][i]  # [file][year]
        for j in range(n_feature_files - 1):
            selected_feature_j = all_selected_features[j + 1][i]
            #print(dfy_this_year.head(2))
            #print(selected_feature_j.head(2))

            dfy_this_year = pd.merge(dfy_this_year,
                                     selected_feature_j,
                                     on=['FIPS'])
        #print(all_yields[i].head(2))
        yield_this_year = all_yields[i]
        dfy_this_year = pd.merge(dfy_this_year, yield_this_year, on=['FIPS'])

        county_in = 1

        DATA_DIR = '/gcs/bnntraining-bucket/'

        path_header = DATA_DIR + 'Data/'

        county_info_filename = path_header + 'county_info.csv'
        county_info = pd.read_csv(county_info_filename)
        if county_in == 1:
            dfy_this_year = pd.merge(dfy_this_year, county_info, on=["FIPS"])

        dfy_all.append(dfy_this_year)

    return dfy_all


def prepare_all_data(crop, current_years):
    DATA_DIR = '/gcs/bnntraining-bucket/'

    path_header = DATA_DIR + 'Data/'

    yield_filename = path_header + 'corn_yield_US.csv'

    # filenames
    feature_filenames = []
    feature_filenames.append(path_header + 'USA_all_predictors.csv')
    n_feature_files = len(feature_filenames)

    # read data
    all_feaures = read_all_features(n_feature_files, feature_filenames)
    # read the yield data
    dy = pd.read_csv(yield_filename)
    # select the yields in current years:
    all_yields = []
    for i in range(len(current_years)):
        val_year_dy = dy['year'] == current_years[i]
        dy_cur_year = dy[val_year_dy]
        dy_cur_year = dy_cur_year[['FIPS', 'yield']]
        all_yields.append(dy_cur_year)

    # select the features in current years:
    for i in range(n_feature_files):
        all_feaures[i] = select_input_years(all_feaures[i], current_years)

    dfy_all = join_by_attributs(all_feaures,
                                all_yields,
                                current_years,
                                n_feature_files,
                                common_attribute='FIPS')

    return dfy_all


# prepare supervised learning data set with previous years
def prepare_supervised_learning_data(dfy_all, training_years):

    xy = dfy_all[0]

    xy['year'] = training_years[0]
    for i in range(len(training_years) - 2):
        dfy_current = dfy_all[i + 1]
        # add the "year"
        dfy_current['year'] = training_years[i + 1]
        xy = pd.concat([xy, dfy_current], sort=False)

    # test region
    print(len(training_years) - 1)
    xy_test = dfy_all[len(training_years) - 1]
    # add the "year"
    xy_test['year'] = training_years[len(training_years) - 1]

    return xy, xy_test


# prepare supervised learning data set with all years
def prepare_supervised_learning_data_all_year(dfy_all, training_years,
                                              target_year):

    xy = dfy_all[0]
    xy['year'] = training_years[0]
    for i in range(len(training_years) - 1):
        if training_years[i + 1] == target_year:
            target_year_position = i + 1
            continue
        dfy_current = dfy_all[i + 1]
        # add the "year"
        dfy_current['year'] = training_years[i + 1]
        xy = pd.concat([xy, dfy_current], sort=False)
        print("training year: ", training_years[i + 1])

    # test region
    xy_test = dfy_all[target_year_position]
    # add the "year"
    xy_test['year'] = training_years[target_year_position]

    return xy, xy_test


def preprocess_supervised_learning_data(dfy_all,
                                        current_years,
                                        num_years,
                                        drop_num=9,
                                        all_year=0):
    # df_all: the loaded feature variables and yield records
    # current_years: the total training and testing years
    # num_years: the number of testing years
    # drop_num: it defines the time window of yield prediction. When it is 9, it means keeping all features and made the yield prediction on Oct 4th. When it is 0, it means that we drop the features on the last 9 observation dates and make yield prediction on May 13rd.
    # all_year: not useful. Fixed it as 0.
    experiment_years = current_years[0:num_years]
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print("Experimenting on years: ", experiment_years)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    drop_days = ['145', '161', '177', '193', '209', '225', '241', '257', '273']
    drop_feature_name = [
        'ppt', 'tmax', 'tmean', 'tmin', 'vpdmax', 'vpdmean', 'vpdmin',
        'LSTday', 'LSTnight', 'EVI', 'GCI', 'NDWI'
    ]

    if all_year == 0:
        xy_train, xy_test = prepare_supervised_learning_data(
            dfy_all, experiment_years)
    else:
        xy_train, xy_test = prepare_supervised_learning_data_all_year(
            dfy_all, current_years, experiment_years[-1])

    states = [5, 17, 18, 19, 20, 26, 27, 29, 31, 38, 39, 46, 55]
    xy_train = xy_train[xy_train['STATE_FIPS'].isin(states)]
    xy_test = xy_test[xy_test['STATE_FIPS'].isin(states)]

    all_drop_features = ['lat', 'lon']
    for feature_name in drop_feature_name:
        for days in drop_days[drop_num:9]:
            cu_fea_day = feature_name + '_' + days
            all_drop_features.append(cu_fea_day)

    x_train = xy_train.drop([
        'yield', 'NAME', 'STATE_FIPS', 'FIPS', 'NA_L2CODE', 'NA_L1CODE',
        'DomainID'
    ],
                            axis=1)
    x_train = x_train.drop(all_drop_features, axis=1)
    y_train = xy_train[['yield']] * 0.0673

    x_test = xy_test.drop([
        'yield', 'NAME', 'STATE_FIPS', 'FIPS', 'NA_L2CODE', 'NA_L1CODE',
        'DomainID'
    ],
                          axis=1)
    x_test = x_test.drop(all_drop_features, axis=1)
    y_test = xy_test[['yield']] * 0.0673
    columns = x_test.columns

    # scale the data
    scaler = MinMaxScaler()

    x_all = pd.concat([x_train, x_test])
    x_all = scaler.fit_transform(x_all)
    # Normalize
    x_train = scaler.transform(x_train)
    x_train = np.float32(x_train)

    x_test = scaler.transform(x_test)
    x_test = np.float32(x_test)

    # Process the results
    y_train = np.float32(y_train)

    # y_train_target_domain = y_train_target_domain.to_numpy()
    y_test = np.float32(y_test)

    return x_train, x_test, y_train, y_test, columns


# prediction
def model_prediction(model, x_test):
    y_pred = model.predict(x_test)

    return y_pred


def model_dual_NN_prediction(model, x_test):
    y_hat = model.predict(x_test)

    mean = yhat.mean()
    stddev = yhat.stddev()

    return mean, stddev


def evaluate_regression_results(y_test, y_pred):
    # print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, y_pred))
    # print('Mean Squared Error:', metrics.mean_squared_error(y_test, y_pred))
    MAPE = np.mean(np.abs(y_test - y_pred) / y_test)
    RMSE = np.sqrt(metrics.mean_squared_error(y_test, y_pred))
    R2 = metrics.r2_score(y_test, y_pred)
    print('RMSE = %f, MAPE = %f, R2 = %f' % (RMSE, MAPE, R2))

    return RMSE, R2, MAPE
