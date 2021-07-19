import pandas as pd
import numpy as np
import time
import os
import functions
import eval
import Training
from sklearn.model_selection import train_test_split


def fit(df, config={}, target_label='Decision', validation_df=None):
    time_start_fit = time.time()
    """
    Parameters:
        df (pandas data frame): Training data frame. The target column must be named as 'Decision' and it has to be in the last column

        config (dictionary):

            config = {
                'algorithm' (string): ID3, 'C4.5, CART, CHAID or Regression
                'enableParallelism' (boolean): False
                # rule.py 저장 on/off
            }

        validation_df (pandas data frame): if nothing is passed to validation data frame, then the function validates built trees for training data frame

    Returns:
        chefboost model
    """
    # ------------------------

    process_id = os.getpid()

    # ------------------------
    # rename target column name
    if target_label != 'Decision':
        df = df.rename(columns={target_label: 'Decision'})

    # if target is not the last column
    if df.columns[-1] != 'Decision':
        new_column_order = df.columns.drop('Decision').tolist() + ['Decision']
        print(new_column_order)
        df = df[new_column_order]
    # ------------------------

    base_df = df.copy()

    # ------------------------

    target_label = df.columns[len(df.columns) - 1]
    if target_label != 'Decision':
        print("Expected: Decision, Existing: ", target_label)
        raise ValueError(
            'Please confirm that name of the target column is "Decision" and it is put to the right in pandas data frame')

    # ------------------------
    # handle NaN values

    nan_values = []

    for column in df.columns:
        if df[column].dtypes != 'object':
            min_value = df[column].min()
            idx = df[df[column].isna()].index

            nan_value = []
            nan_value.append(column)

            if idx.shape[0] > 0:
                df.loc[idx, column] = min_value - 1
                nan_value.append(min_value - 1)
            # print("NaN values are replaced to ", min_value - 1, " in column ", column)
            else:
                nan_value.append(None)

            # min_value - 1을 넣는 이유? ( fillna(min_value-1) )

            nan_values.append(nan_value)

    # ------------------------

    # initialize params and folders

    print('Time of fit: ', time.time() - time_start_fit)
    config = functions.initializeParams(config)
    functions.initializeFolders()

    # ------------------------
    algorithm = config['algorithm']

    valid_algorithms = ['ID3', 'C4.5']

    if algorithm not in valid_algorithms:
        raise ValueError('Invalid algorithm passed. You passed ', algorithm, " but valid algorithms are ",
                         valid_algorithms)

    # ------------------------

    enableParallelism = config['enableParallelism']
    # ------------------------
    if enableParallelism:
        print("[INFO]: ", config["num_cores"], "CPU cores will be allocated in parallel running")

        from multiprocessing import set_start_method, freeze_support
        set_start_method("spawn", force=True)
        freeze_support()
    # ------------------------

    if algorithm == 'Regression':
        if df['Decision'].dtypes == 'object':
            raise ValueError(
                'Regression trees cannot be applied for nominal target values! You can either change the algorithm or data set.')

    if df['Decision'].dtypes != 'object':  # this must be regression tree even if it is not mentioned in algorithm

        if algorithm != 'Regression':
            print("WARNING: You set the algorithm to ", algorithm,
                  " but the Decision column of your data set has non-object type.")
            print("That's why, the algorithm is set to Regression to handle the data set.")

        algorithm = 'Regression'
        config['algorithm'] = 'Regression'
        global_stdev = df['Decision'].std(ddof=0)

    # -------------------------

    print(algorithm, " tree is going to be built...")

    dataset_features = dict()  # initialize a dictionary. this is going to be used to check features numeric or nominal. numeric features should be transformed to nominal values based on scales.

    header = "def findDecision(obj): #"

    num_of_columns = df.shape[1] - 1
    for i in range(0, num_of_columns):
        column_name = df.columns[i]
        dataset_features[column_name] = df[column_name].dtypes
        header = header + "obj[" + str(i) + "]: " + column_name
        if i != num_of_columns - 1:
            header = header + ", "

    header = header + "\n"

    # ------------------------
    begin = time.time()

    trees = []
    alphas = []

    root = 1
    file = "outputs/rules/rules.py"
    functions.createFile(file, header)

    if enableParallelism == True:
        json_file = "outputs/rules/rules.json"
        functions.createFile(json_file, "[\n")

    trees = Training.buildDecisionTree(df, root=root, file=file, config=config
                                       , dataset_features=dataset_features
                                       , parent_level=0, leaf_id=0, parents='root', validation_df=validation_df,
                                       main_process_id=process_id)

    print("-------------------------")
    print("finished in ", time.time() - begin, " seconds")

    obj = {
        "trees": trees,
        "alphas": alphas,
        "config": config,
        "nan_values": nan_values
    }

    # -----------------------------------------

    # train set accuracy
    df = base_df.copy()
    evaluate(obj, df, task='train')

    # validation set accuracy
    if isinstance(validation_df, pd.DataFrame):
        evaluate(obj, validation_df, task='validation')

    # -----------------------------------------

    return obj


# -----------------------------------------

def predict(model, param):
    """
	Parameters:
		model (built chefboost model): you should pass model argument to the return of fit function
		param (list): pass input features as python list

		e.g. chef.predict(model, param = ['Sunny', 'Hot', 'High', 'Weak'])
	Returns:
		prediction
	"""

    trees = model["trees"]
    config = model["config"]

    alphas = []
    if "alphas" in model:
        alphas = model["alphas"]

    nan_values = []
    if "nan_values" in model:
        nan_values = model["nan_values"]

    # -----------------------
    # handle missing values

    column_index = 0
    for column in nan_values:
        column_name = column[0]
        missing_value = column[1]

        if pd.isna(missing_value) != True:
            # print("missing values will be replaced with ",missing_value," in ",column_name," column")

            if pd.isna(param[column_index]):
                param[column_index] = missing_value

        column_index = column_index + 1

    # print("instance: ", param)
    # -----------------------

    # -----------------------

    classification = False
    prediction = 0
    prediction_classes = []

    # -----------------------

    # -----------------------

    if len(trees) > 1:  # bagging or boosting
        index = 0
        for tree in trees:

            custom_prediction = tree.findDecision(param)

            if custom_prediction != None:
                if type(custom_prediction) != str:  # regression
                    prediction += custom_prediction
                else:
                    classification = True
                    prediction_classes.append(custom_prediction)

            index = index + 1


    else:  # regular decision tree
        tree = trees[0]
        prediction = tree.findDecision(param)

    if classification == False:
        return prediction
    else:

        predictions = np.array(prediction_classes)

        # find the most frequent prediction
        (values, counts) = np.unique(predictions, return_counts=True)
        idx = np.argmax(counts)
        prediction = values[idx]

        return prediction


def evaluate(model, df, target_label='Decision', task='test'):
    """
    Parameters:
        model (built chefboost model): you should pass the return of fit function
        df (pandas data frame): data frame you would like to evaluate
        task (string): optionally you can pass this train, validation or test
    :param task:
    :param df:
    :param model:
    :param target_label:
    """

    # --------------------------

    if target_label != 'Decision':
        df = df.rename(columns={target_label: 'Decision'})

    # if target is not the last column
    if df.columns[-1] != 'Decision':
        new_column_order = df.columns.drop('Decision').tolist() + ['Decision']
        print(new_column_order)
        df = df[new_column_order]

    # --------------------------

    functions.bulk_prediction(df, model)

    eval.evaluate(df, task=task)

def sampling_func(data, sample_pct):
    np.random.seed(123)
    N = len(data)
    sample_n = int(len(data)*sample_pct) # integer
    sample = data.take(np.random.permutation(N)[:sample_n])
    return sample


def data_split(data, _portion: float):
    target_unique = data['Decision'].unique()
    data_0 = data[data['Decision'] == target_unique[0]]
    data_1 = data[data['Decision'] == target_unique[1]]

    sample_data_0 = int(len(data_0) * _portion)
    sample_data_1 = int(len(data_1) * _portion)

    train_data_0 = data_0.take(np.random.permutation(len(data_0))[:(1-sample_data_0)])
    train_data_1 = data_1.take(np.random.permutation(len(data_1))[:(1-sample_data_1)])
    train_data = pd.concat([train_data_0, train_data_1], axis=0)

    test_data_0 = data_0.take(np.random.permutation(len(data_0))[:sample_data_0])
    test_data_1 = data_1.take(np.random.permutation(len(data_1))[:sample_data_1])
    test_data = pd.concat([test_data_0, test_data_1], axis=0)

    return train_data, test_data

def check_decision(og_data):
    data = og_data.copy()
    target_label = og_data.columns[len(data.columns) - 1]
    if target_label != 'Decision':
        dec = og_data.loc[:, target_label].copy()
        data['Decision'] = dec
        data = data.drop(target_label, axis=1)
    else:
        print('You have Decision Columns in your dataframe! No need to Change!')
    return data
