'''
Created on Dec, 2017

@author: FrancesZhou
'''

from __future__ import absolute_import

import argparse
import numpy as np
import re
import sys
import collections
sys.path.append('../material')
#from ..material.utils import load_pickle, dump_pickle, load_txt, get_wordID_from_vocab
from datasets.material.utils import load_pickle, dump_pickle, load_txt, get_wordID_from_vocab, get_wordID_from_vocab_dict_for_raw_text, write_label_pairs_into_file, get_asin_from_map_file

def clean_str(string):
    # remove stopwords
    # string = ' '.join([word for word in string.split() if word not in cachedStopWords])
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()


train_asin_label_fea_file = 'sources/xml/amazon_train.txt'
test_asin_label_fea_file = 'sources/xml/amazon_test.txt'
# *_train.txt and *_test.txt with first line as header info.
train_asin_map_file = 'sources/xml/Amazon-670K_train_map.txt'
test_asin_map_file = 'sources/xml/Amazon-670K_test_map.txt'
asin_map_file = 'sources/asin_map.pkl'
text_data_file = 'sources/text_data.pkl'
#cat_data_file = 'sources/cat_data.pkl'
data_source_path = 'data/deeplearning_data/docs/'
data_des_path = 'data/deeplearning_data/adjacent_labels/'

#label_map_file = 'sources/xml/AmazonCat-13K_label_map.txt'

def get_train_test_data(vocab,
                        asin_map_file, text_data_file,
                        train_asin_map_file, test_asin_map_file,
                        train_asin_label_fea_file, test_asin_label_fea_file):
    vocab = load_pickle('../material/' + vocab)
    vocab_dict = dict(zip(vocab, range(len(vocab))))
    asin_map = load_pickle(asin_map_file)
    asin_map_dict = dict(zip(asin_map, range(len(asin_map))))
    text_data = load_pickle(text_data_file)
    #
    train_asin_label_fea = load_txt(train_asin_label_fea_file)[1:]
    test_asin_label_fea = load_txt(test_asin_label_fea_file)[1:]
    # remove all replica in both train and test asin map
    train_asin_map = get_asin_from_map_file(train_asin_map_file)
    test_asin_map = get_asin_from_map_file(test_asin_map_file)
    train_asin_map_dict = dict(zip(train_asin_map, range(len(train_asin_map))))
    test_asin_map_dict = dict(zip(test_asin_map, range(len(test_asin_map))))
    #
    train_rep = [item for item, count in collections.Counter(train_asin_map).items() if count > 1]
    test_rep = [item for item, count in collections.Counter(test_asin_map).items() if count > 1]
    train_asin = set(train_asin_map) - set(train_rep)
    test_asin = set(test_asin_map) - set(test_rep)
    # remove asins from test data which appear in train data
    test_asin = test_asin - train_asin
    train_asin = list(train_asin)
    test_asin = list(test_asin)
    # train
    print('get train data')
    all_labels = []
    train_doc_wordID = {}
    train_label = {}
    train_feature = {}
    k = 0
    for t in train_asin:
        k = k + 1
        if k % 10000 == 0:
            print(k)
        try:
            #ind = asin_map.index(t)
            ind = asin_map_dict[t]
        except:
            continue
        #train_data[ind] = clean_str(text_data[ind])
        text = clean_str(text_data[ind])
        wordID = get_wordID_from_vocab_dict_for_raw_text(text, vocab_dict)
        if not wordID:
            continue
        train_doc_wordID[ind] = wordID
        #
        #line = train_asin_label_fea[train_asin_map.index(t)]
        line = train_asin_label_fea[train_asin_map_dict[t]]
        labels_str, feature_str = line.split(' ', 1)
        labels = [int(label) for label in labels_str.split(',')]
        all_labels.append(labels)
        train_label[ind] = labels
        train_feature[ind] = feature_str
    # test
    print('get test data')
    test_doc_wordID = {}
    test_label = {}
    test_feature = {}
    k = 0
    for t in test_asin:
        k = k + 1
        if k % 10000 == 0:
            print(k)
        try:
            ind = asin_map_dict[t]
            #ind = asin_map.index(t)
        except:
            continue
        #test_data[ind] = clean_str(text_data[ind])
        text = clean_str(text_data[ind])
        wordID = get_wordID_from_vocab_dict_for_raw_text(text, vocab_dict)
        if not wordID:
            continue
        test_doc_wordID[ind] = wordID
        #
        #line = test_asin_label_fea[test_asin_map.index(t)]
        line = test_asin_label_fea[test_asin_map_dict[t]]
        labels_str, feature_str = line.split(' ', 1)
        labels = [int(label) for label in labels_str.split(',')]
        test_label[ind] = labels
        test_feature[ind] = feature_str
    all_labels = np.unique(np.concatenate(all_labels)).tolist()
    print('dump train/test data')
    dump_pickle(train_feature, data_source_path + 'train_feature.pkl')
    dump_pickle(test_feature, data_source_path + 'test_feature.pkl')
    dump_pickle(train_doc_wordID, data_source_path + 'train_doc_wordID.pkl')
    dump_pickle(train_label, data_source_path + 'train_label.pkl')
    dump_pickle(test_doc_wordID, data_source_path + 'test_doc_wordID.pkl')
    dump_pickle(test_label, data_source_path + 'test_label.pkl')
    return all_labels, train_doc_wordID, train_label, test_doc_wordID, test_label, train_feature, test_feature

'''
def get_train_test_wordID_from_vocab(vocab, train_doc_data, test_doc_data):
    vocab = load_pickle('../material/' + vocab)
    # train_data = load_pickle(train_doc_data)
    # test_data = load_pickle(test_doc_data)
    train_data = train_doc_data
    test_data = test_doc_data
    train_doc_wordID = {}
    test_doc_wordID = {}
    vocab_dict = dict(zip(vocab, range(len(vocab))))
    print 'get train wordID data'
    k = 0
    for id, text in train_data.items():
        k = k + 1
        if k % 1000 == 0:
            print k
        #text = id + '. ' + text
        wordID = get_wordID_from_vocab_dict(text, vocab_dict)
        train_doc_wordID[id] = wordID
    print 'get test wordID data'
    k = 0
    for id, text in test_data.items():
        k = k + 1
        if k % 1000 == 0:
            print k
        #text = id + '. ' + text
        wordID = get_wordID_from_vocab_dict(text, vocab_dict)
        test_doc_wordID[id] = wordID
    return train_doc_wordID, test_doc_wordID
    #dump_pickle(train_doc_wordID, train_doc_wordID_final)
    #dump_pickle(test_doc_wordID, test_doc_wordID_final)
'''

def generate_label_pair(train_asin_label):
    train_label = train_asin_label
    # get label pairs
    label_pairs = []
    for _, labels_doc in train_label.items():
        if len(labels_doc) == 1:
            continue
        labels_doc = sorted(labels_doc)
        label_pair_start = labels_doc[0]
        for label in labels_doc[1:]:
            label_pairs.append([label_pair_start, label])
    # delete duplica
    label_pairs = np.array(label_pairs, dtype=np.int32)
    label_pairs = np.unique(label_pairs, axis=0)
    all_adjacent_labels = np.unique(np.concatenate(label_pairs))
    return label_pairs, all_adjacent_labels

def get_valid_train_test_data(all_adjacent_labels,
                              train_doc_data, test_doc_data,
                              train_asin_label, test_asin_label,
                              train_asin_feature=None, test_asin_feature=None
                              ):
    train_pids = train_doc_data.keys()
    print('get valid train data')
    k = 0
    for pid in train_pids:
        k = k + 1
        if k % 50000 == 0:
            print(k)
        #l = train_asin_label[pid]
        l2 = list(set(train_asin_label[pid]) & set(all_adjacent_labels))
        if len(l2):
            train_asin_label[pid] = l2
        else:
            del train_asin_label[pid]
            del train_doc_data[pid]
            del train_asin_feature[pid]
    test_pids = test_doc_data.keys()
    print('get valid test data')
    k = 0
    for pid in test_pids:
        k = k + 1
        if k % 50000 == 0:
            print(k)
        l2 = list(set(test_asin_label[pid]) & set(all_adjacent_labels))
        if len(l2):
            test_asin_label[pid] = l2
        else:
            del test_asin_label[pid]
            del test_doc_data[pid]
            del test_asin_feature[pid]
    return train_doc_data, test_doc_data, train_asin_label, test_asin_label, train_asin_feature, test_asin_feature


# get label embeddings for all_labels
# def get_label_embedding_for_all_labels(label_map_file)

def main():
    parse = argparse.ArgumentParser()

    parse.add_argument('-which_labels', '--which_labels', type=str,
                       default='adjacent',
                       help='adjacent labels or all labels')
    parse.add_argument('-if_split_train_test', '--if_split_train_test', type=int,
                       default=0,
                       help='if have split train and test data: 0 for not, 1 for have split')
    args = parse.parse_args()

    print('get train and test data-------------------')
    if args.if_split_train_test:
        train_doc_wordID = load_pickle(data_source_path + 'train_doc_wordID.pkl')
        train_asin_label = load_pickle(data_source_path + 'train_label.pkl')
        test_doc_wordID = load_pickle(data_source_path + 'test_doc_wordID.pkl')
        test_asin_label = load_pickle(data_source_path + 'test_label.pkl')
        train_asin_feature = load_pickle(data_source_path + 'train_feature.pkl')
        test_asin_feature = load_pickle(data_source_path + 'test_feature.pkl')
        all_labels = np.unique(np.concatenate(train_asin_label.values())).tolist()
    else:
        all_labels, train_doc_wordID, train_asin_label, test_doc_wordID, test_asin_label, train_asin_feature, test_asin_feature = \
            get_train_test_data('vocab.6B.300d.pkl',
                                asin_map_file, text_data_file,
                                train_asin_map_file, test_asin_map_file,
                                train_asin_label_fea_file, test_asin_label_fea_file)

    if args.which_labels == 'adjacent':
        # 1. label embedding
        print('get label pair-----------------------')
        label_pairs, all_adjacent_labels = generate_label_pair(train_asin_label)
        print(len(set(all_labels) - set(all_adjacent_labels)))
        # 2. write label_pairs to txt file
        print('write label pair into file --------------')
        write_label_pairs_into_file(label_pairs, data_des_path + 'labels.edgelist')
        # 3. get valid train/test doc_data and asin_label
        print('get valid train and test data ----------------')
        train_doc_wordID, test_doc_wordID, train_asin_label, test_asin_label, train_asin_feature, test_asin_feature = \
            get_valid_train_test_data(
                all_adjacent_labels,
                train_doc_wordID, test_doc_wordID,
                train_asin_label, test_asin_label,
                train_asin_feature, test_asin_feature
        )
        print('dump data -------------------------------')
        dump_pickle(train_doc_wordID, data_des_path + 'train_doc_wordID.pkl')
        dump_pickle(test_doc_wordID, data_des_path + 'test_doc_wordID.pkl')
        dump_pickle(train_asin_label, data_des_path + 'train_label.pkl')
        dump_pickle(test_asin_label, data_des_path + 'test_label.pkl')
        dump_pickle(train_asin_feature, data_des_path + 'train_feature.pkl')
        dump_pickle(test_asin_feature, data_des_path + 'test_feature.pkl')

    elif args.which_labels == 'all':
        pass
        # 1. doc wordID
        # train_doc_wordID, test_doc_wordID = get_train_test_wordID_from_vocab(
        #     load_pickle(train_doc_data_file), load_pickle(test_doc_data_file))
        # 2. doc labels
        # train_asin_label, test_asin_label
        # 3. label embedding
        # TODO




if __name__ == "__main__":
    main()
