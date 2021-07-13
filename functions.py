import pathlib
import os
from os import path
import multiprocessing
import CB as cb
import time


def bulk_prediction(df, model):
    predictions = []

    for index, instance in df.iterrows():
        features = instance.values[0:-1]
        prediction = cb.predict(model, features)
        predictions.append(prediction)
    df['Prediction'] = predictions


def initializeFolders():
    time_start_initialfolder = time.time()
    import sys
    sys.path.append("..")
    pathlib.Path("outputs").mkdir(parents=True, exist_ok=True)
    pathlib.Path("outputs/data").mkdir(parents=True, exist_ok=True)
    pathlib.Path("outputs/rules").mkdir(parents=True, exist_ok=True)

    # -----------------------------------

    # clear existing rules in outputs/

    outputs_path = os.getcwd() + os.path.sep + "outputs" + os.path.sep

    try:
        if path.exists(outputs_path + "data"):
            for file in os.listdir(outputs_path + "data"):
                os.remove(outputs_path + "data" + os.path.sep + file)

        if path.exists(outputs_path + "rules"):
            for file in os.listdir(outputs_path + "rules"):
                if ".py" in file or ".json" in file or ".txt" in file or ".pkl" in file or ".csv" in file:
                    os.remove(outputs_path + "rules" + os.path.sep + file)
    except Exception as err:
        print("WARNING: ", str(err))
    print('Time of InitializeFolders: ', time.time() - time_start_initialfolder)


# ------------------------------------

def initializeParams(config):
    time_start_initialize = time.time()
    algorithm = 'ID3'

    enableParallelism = True
    num_cores = int(multiprocessing.cpu_count() / 2)  # allocate half of your total cores

    # 코어의 개수를 왜 /2했을까?

    # num_cores = int((3*multiprocessing.cpu_count())/4) #allocate 3/4 of your total cores
    # num_cores = multiprocessing.cpu_count()

    for key, value in config.items():
        if key == 'algorithm':
            algorithm = value
        # ---------------------------------

        # ---------------------------------

        # ---------------------------------

        # ---------------------------------
        elif key == 'enableParallelism':
            enableParallelism = value
        elif key == 'num_cores':
            num_cores = value

    config['algorithm'] = algorithm

    config['enableParallelism'] = enableParallelism
    config['num_cores'] = num_cores
    time_end_initialize = time.time()
    print('Time of InitializeParams: ', time_end_initialize - time_start_initialize)
    return config


def createFile(file, content):
    time_start_createFile = time.time()
    f = open(file, "w")
    f.write(content)
    print('Time of createFile: ', time.time() - time_start_createFile)


def storeRule(file, content):
    f = open(file, "a+")
    f.writelines(content)
    f.writelines("\n")
