from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import precision_recall_fscore_support
from sklearn.utils import resample
import pandas as pd
import numpy as np


def stratified_kfold_export(data_x, data_y, dataset_name, n_splits=10):
    dataset_name = "data/validation_splits/" + dataset_name
    with open(dataset_name + '_data_x.txt', 'w', encoding='utf-8') as text_file:
        text_file.write("Text\n")
        for line in data_x:
            text_file.write(' '.join(line.split()) + '\n')
    with open(dataset_name + '_data_y.txt', 'w', encoding='utf-8') as text_file:
        for line in data_y:
            text_file.write(str(line)+'\n')

    skf = StratifiedKFold(n_splits, random_state=157)
    iter = 0
    for train_index, test_index in skf.split(data_x, data_y):
        with open(dataset_name + '_train_x_%d.txt' % iter, 'w', encoding='utf-8') as text_file:
            text_file.write("Text\n")
            for line in data_x[train_index]:
                text_file.write(' '.join(line.split())+'\n')
        with open(dataset_name + '_train_y_%d.txt' % iter, 'w', encoding='utf-8') as text_file:
            for line in data_y[train_index]:
                text_file.write(str(line)+'\n')
        with open(dataset_name + '_test_x_%d.txt' % iter, 'w', encoding='utf-8') as text_file:
            text_file.write("Text\n")
            for line in data_x[test_index]:
                text_file.write(' '.join(line.split())+'\n')
        with open(dataset_name + '_test_y_%d.txt' % iter, 'w', encoding='utf-8') as text_file:
            for line in data_y[test_index]:
                text_file.write(str(line)+'\n')
        iter += 1


def sentistrength_import(evaluate_y_path, predict_y_path, has_neutral=False):
    predict_y = list()
    evaluate_y = list()
    with open(evaluate_y_path, encoding='utf-8') as text_file:
        for line in text_file:
            evaluate_y.append(int(line))
    with open(predict_y_path, encoding='utf-8') as text_file:
        _temp = text_file.readline()
        for line in text_file:
            split_line = line.split('\t')
            sentiment = int(split_line[2]) + int(split_line[3])
            if sentiment < 0:
                predict_y.append(0)
            else:
                if has_neutral and sentiment == 0:
                    predict_y.append(2)
                else:
                    predict_y.append(1)
    return {"individual": precision_recall_fscore_support(evaluate_y, predict_y),
            "micro-average": precision_recall_fscore_support(evaluate_y, predict_y, average="micro")}


def sentistrengthse_import(evaluate_y_path, predict_y_path, has_neutral=False):
    predict_y = list()
    evaluate_y = list()
    with open(evaluate_y_path, encoding='utf-8') as text_file:
        for line in text_file:
            evaluate_y.append(int(line))
    with open(predict_y_path) as text_file:
        _temp = text_file.readline()
        for line in text_file:
            split_line = line.split('\t')[1].split(' ')
            sentiment = int(split_line[0]) + int(split_line[1])
            if sentiment < 0:
                predict_y.append(0)
            else:
                if has_neutral and sentiment == 0:
                    predict_y.append(2)
                else:
                    predict_y.append(1)
    return {"individual": precision_recall_fscore_support(evaluate_y, predict_y),
            "micro-average": precision_recall_fscore_support(evaluate_y, predict_y, average="micro")}


def bootstrap_trend_export(data_x, data_y, dataset_name, has_neutral=False):
    dataset_name = "data/validation_splits/" + dataset_name
    train_x, test_x, train_y, test_y = train_test_split(data_x, data_y, test_size=0.2, random_state=157)
    with open(dataset_name + '_test_x.txt', 'w', encoding='utf-8') as text_file:
        text_file.write("Text\n")
        for line in data_x:
            text_file.write(' '.join(line.split()) + '\n')
    with open(dataset_name + '_test_y.txt', 'w', encoding='utf-8') as text_file:
        for line in data_y:
            text_file.write(str(line)+'\n')
    for sample_rate in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        n_samples = int(sample_rate * len(train_y) + 1)
        train_xr, train_yr = resample(train_x, train_y, n_samples=n_samples, random_state=157)
        with open(dataset_name + '_train_xr_%f.txt' % sample_rate, 'w', encoding='utf-8') as text_file:
            text_file.write("Text\n")
            for line in train_xr:
                text_file.write(' '.join(line.split())+'\n')
        with open(dataset_name + '_train_yr_%f.txt' % sample_rate, 'w', encoding='utf-8') as text_file:
            for line in train_yr:
                text_file.write(str(line)+'\n')


if __name__ == '__main__':
    # data = pd.read_csv("data/labelled/Gerrit.csv").as_matrix()
    # data = pd.read_csv("data/labelled/StackOverflow2.csv", encoding='latin1').as_matrix()
    # data_1 = pd.read_csv("data/labelled/StackOverflow2.csv", encoding='latin1')
    # data_2 = pd.read_csv("data/labelled/Gerrit.csv")
    # data_3 = pd.read_csv("data/labelled/JIRA.csv")
    # data = pd.concat([data_1, data_2, data_3]).as_matrix()
    # data_x = np.array([x for x in data[:,0]])
    # data_y = np.array([int(x) for x in data[:,1]])
    # stratified_kfold_export(data_x, data_y, dataset_name="StackOverflow2")
    # bootstrap_trend_export(data_x, data_y, dataset_name="Combined")
    metrics = sentistrengthse_import("data/validation_splits/StackOverflow2_data_y.txt", "data/validation_splits/StackOverflow2_predict_y_sentistrengthse.txt", has_neutral=False)
    print("Accuracy: %s Precision: %s, Recall: %s" % (metrics['micro-average'][0], metrics['individual'][0], metrics['individual'][1]))
