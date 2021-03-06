from sklearn.metrics import precision_recall_fscore_support, accuracy_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.utils import resample
import pandas as pd
import numpy as np
import subprocess
import time


def train(train_x, train_y):
    with open("input.csv", 'w', encoding='utf-8') as text_file:
        for line, label in zip(train_x, train_y):
            text_file.write(' '.join(line.split()) + ',' + str(label) + '\n')
    try:
        subprocess.run(["java", "-jar", "./lib/external/Senti4SD/NgramsExtraction.jar", "input.csv",
                        "true"]).check_returncode()
        subprocess.run(["java",  "-jar", "-Xmx5000m", "./lib/external/Senti4SD/Senti4SD.jar", "-F", "A", "-i",
                        "input.csv", "-W", "./lib/external/Senti4SD/dsm.bin", "-oc", "output.csv", "-vd", "600",
                        "-L", "-ul", "UnigramsList", "bl", "BigramsList"]).check_returncode()
        subprocess.run(["Rscript", "./lib/external/Senti4SD/parameterTuning.R", "temp",
                        "./lib/external/Senti4SD/modelsLiblinear", "output.csv"]).check_returncode()
        subprocess.run(["Rscript", "./lib/external/Senti4SD/trainModel.R", "temp",
                        "temp/L2-regularized_logistic_regression_(primal).txt", "output.csv"]).check_returncode()
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)


def predict(predict_x):
    with open("test.txt", 'w', encoding='utf-8') as text_file:
        for line in predict_x:
            text_file.write(' '.join(line.split()) + '\n')
    try:
        subprocess.run(["java", "-jar", "./lib/external/Senti4SD/NgramsExtraction.jar", "test.txt"]).check_returncode()
        subprocess.run(["java",  "-jar", "-Xmx5000m", "./lib/external/Senti4SD/Senti4SD.jar", "-F", "A", "-i",
                        "test.txt", "-W", "./lib/external/Senti4SD/dsm.bin", "-oc", "output.csv", "-vd", "600",
                        "-ul", "UnigramsList", "bl", "BigramsList"]).check_returncode()
        subprocess.run(["Rscript", "./lib/external/Senti4SD/classification.R", "output.csv", "predictions.csv",
                        "temp/modelLiblinear_L2-regularized_logistic_regression_(primal).Rda"]).check_returncode()
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)
    predict_y = list()
    with open("predictions.csv", 'r') as text_file:
        _temp = text_file.readline()
        for line in text_file:
            predict_y.append(int(line.split(',')[1].strip()))
    return predict_y


def evaluate(evaluate_x, evaluate_y):
    predict_y = predict(evaluate_x)
    return {"individual": precision_recall_fscore_support(evaluate_y, predict_y),
            "micro-average": precision_recall_fscore_support(evaluate_y, predict_y, average="micro")}


def cross_val(data_x, data_y, num_classes, n_splits=5):
    skf = StratifiedKFold(n_splits, shuffle=True,random_state=157)
    print("Performing cross validation (%d-fold)..." % n_splits)
    precision_list = [0 for i in range(num_classes)]
    recall_list = [0 for i in range(num_classes)]
    f1_list = [0 for i in range(num_classes)]
    mean_accuracy = 0

    for train_index, test_index in skf.split(data_x, data_y):
        train_start_time = time.time()
        train(data_x[train_index], data_y[train_index])
        print("Train time:", time.time() - train_start_time)
        test_start_time = time.time()
        metrics = evaluate(data_x[test_index], data_y[test_index])
        print("Test time:", time.time() - test_start_time)
        mean_accuracy += metrics['micro-average'][0]
        precision_list = [x + y for x, y in zip(metrics['individual'][0], precision_list)]
        recall_list = [x + y for x, y in zip(metrics['individual'][1], recall_list)]
        f1_list = [x + y for x, y in zip(metrics['individual'][2], f1_list)]
        print("Accuracy: %s, Precision: %s, Recall: %s, F1: %s" % (metrics['micro-average'][0], metrics['individual'][0],
                                                                   metrics['individual'][1], metrics['individual'][2]))
    print("Mean accuracy: %s Mean precision: %s, Mean recall: %s, Mean F1: %s" % (mean_accuracy/n_splits, [precision/n_splits for precision in precision_list],
                                                                                  [recall/n_splits for recall in recall_list], [f1/n_splits for f1 in f1_list]))


def bootstrap_trend(data_x, data_y, num_classes):
    train_x, test_x, train_y, test_y = train_test_split(data_x, data_y, test_size=0.3, random_state=157, stratify=data_y)
    precision_list = [0 for i in range(num_classes)]
    recall_list = [0 for i in range(num_classes)]
    f1_list = [0 for i in range(num_classes)]
    accuracy_list = list()

    for sample_rate in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        n_samples = int(sample_rate * len(train_y) + 1)
        train_xr, train_yr = resample(train_x, train_y, n_samples=n_samples, random_state=157)
        print("Training with %d samples" % len(train_yr))
        train(train_xr, train_yr)
        metrics = evaluate(test_x, test_y)
        print("Accuracy: %s, Precision: %s, Recall: %s, F1: %s" % (metrics['micro-average'][0], metrics['individual'][0],
                                                                   metrics['individual'][1], metrics['individual'][2]))
        precision_list = [x + y for x, y in zip(metrics['individual'][0], precision_list)]
        recall_list = [x + y for x, y in zip(metrics['individual'][1], recall_list)]
        f1_list = [x + y for x, y in zip(metrics['individual'][2], f1_list)]
        accuracy_list.append(metrics['micro-average'][0])

    print("Accuracies:", accuracy_list)
    print("Dataset sizes:", [int(sample_rate * len(train_y) + 1) for sample_rate in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]])
    print("Mean accuracy: %s Mean precision: %s, Mean recall: %s, Mean F1: %s" % (sum(accuracy_list)/9, [precision/9 for precision in precision_list],
                                                                                  [recall/9 for recall in recall_list], [f1/9 for f1 in f1_list]))


def cross_dataset(data_list, num_classes):
    precision_list = [0 for i in range(num_classes)]
    recall_list = [0 for i in range(num_classes)]
    f1_list = [0 for i in range(num_classes)]
    accuracy_list = list()

    # Uncomment for resampling:
    # for i0 in range(len(data_list)):
    #     data_list[i0] = resample(data_list[i0], n_samples=1500, random_state=157, replace=False)

    for i0 in range(len(data_list)):
        data_train = data_list[i0].as_matrix()
        train_x = np.array([x.lower() for x in data_train[:,0]])
        train_y = np.array([int(x) for x in data_train[:,1]])
        train(train_x, train_y)
        for i1 in range(len(data_list)):
            if i1 != i0:
                data_test = data_list[i1].as_matrix()
                test_x = np.array([x.lower() for x in data_test[:, 0]])
                test_y = np.array([int(x) for x in data_test[:, 1]])
                metrics = evaluate(test_x, test_y)
                accuracy_list.append(metrics['micro-average'][0])
                precision_list = [x + y for x, y in zip(metrics['individual'][0], precision_list)]
                recall_list = [x + y for x, y in zip(metrics['individual'][1], recall_list)]
                f1_list = [x + y for x, y in zip(metrics['individual'][2], f1_list)]
                print(i0, i1, "Accuracy: %s, Precision: %s, Recall: %s, F1: %s" % (metrics['micro-average'][0], metrics['individual'][0],
                                                                                   metrics['individual'][1], metrics['individual'][2]))
    print("Mean accuracy: %s Mean precision: %s, Mean recall: %s, Mean F1: %s" % (sum(accuracy_list)/len(accuracy_list),
                                                                                  [precision/len(accuracy_list) for precision in precision_list],
                                                                                  [recall/len(accuracy_list) for recall in recall_list],
                                                                                  [f1/len(accuracy_list) for f1 in f1_list]))


if __name__ == '__main__':
    num_classes = 2
    # data = pd.read_csv("data/labelled/Gerrit.csv").as_matrix()
    # data = pd.read_csv("data/labelled/StackOverflowJavaLibraries.csv", encoding='latin1').as_matrix()
    data_1 = pd.read_csv("data/labelled/JIRA.csv")
    data_2 = pd.read_csv("data/labelled/AppReviews.csv")
    data_3 = pd.read_csv("data/labelled/Gerrit.csv")
    data_4 = pd.read_csv("data/labelled/StackOverflowEmotions.csv", encoding='latin1')
    data_5 = pd.read_csv("data/labelled/StackOverflowSentiments.csv", encoding='latin1')
    data_6 = pd.read_csv("data/labelled/StackOverflowJavaLibraries.csv", encoding='latin1')
    data_list = [data_4, data_5, data_6]
    iter = 0
    for dataset in data_list:
        iter += 1
        if iter == 1 or iter == 3:
            num_classes = 2
        else:
            num_classes = 3
        data = dataset.as_matrix()
        data_x = np.array([x.lower() for x in data[:,0]])
        data_y = np.array([int(x) for x in data[:,1]])
        bootstrap_trend(data_x, data_y, num_classes)
    # data = data_1.as_matrix()
    # data_x = np.array([x.lower() for x in data[:,0]])
    # data_y = np.array([int(x) for x in data[:,1]])
    # print("Dataset loaded to memory. Size:", len(data_y))
    # cross_val(data_x, data_y, num_classes, n_splits=10)
    # cross_dataset(data_list, num_classes)