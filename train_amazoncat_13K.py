'''
Created on Nov, 2017

@author: FrancesZhou
'''

from __future__ import absolute_import

import os
import argparse
import numpy as np
from model.preprocessing.dataloader import DataLoader_all as DataLoader5
from model.preprocessing.preprocessing import generate_label_embedding_from_file_2
from model.preprocessing.dataloader import *
from model.core.biLSTM import biLSTM
from model.core.LSTM import LSTM
from model.core.CNN import CNN
from model.core.XML_CNN import XML_CNN
from model.core.CNN2 import CNN2
from model.core.solver import ModelSolver
from model.utils.io_utils import load_pickle


def main():
    parse = argparse.ArgumentParser()
    # ---------- environment setting: which gpu -------
    parse.add_argument('-gpu', '--gpu', type=str, default='0', help='which gpu to use: 0 or 1')
    # ---------- foler path of train/test data -------
    parse.add_argument('-folder', '--folder_path', type=str,
                       default='datasets/AmazonCat-13K/data/deeplearning_data/adjacent_labels/',
                       help='path to train/test data')
    # ---------- vocab and word embeddings --------
    # parse.add_argument('-vocab', '--vocab_path', type=str, default='vocab.6B.300d.pkl', help='path to the vocab')
    parse.add_argument('-word_embeddings', '--word_embedding_path', type=str,
                       default='word_emb.6B.300d.npy',
                       help='path to the word embeddings')
    # ---------- model ----------
    parse.add_argument('-max_seq_len', '--max_seq_len', type=int, default=500,
                       help='maximum sequence length')
    parse.add_argument('-model', '--model', type=str, default='CNN', help='model: LSTM, biLSTM, CNN')
    parse.add_argument('-pretrained_model', '--pretrained_model_path', type=str,
                       default=None, help='path to the pretrained model')
    parse.add_argument('-cal_metrics', '--cal_metrics', type=int, default=1,
                       help='if calculate wts_p and wts_ndcg for baseline results')
    parse.add_argument('-alpha', '--alpha', type=float, default=0.2,
                       help='trade off parameter between baseline score and refinement score')
    # ---------- params for CNN ------------
    parse.add_argument('-num_filters', '--num_filters', type=int,
                       default=32, help='number of filters in CNN')
    parse.add_argument('-pooling_units', '--pooling_units', type=int,
                       default=64, help='number of pooling units')
    parse.add_argument('-dropout_keep_prob', '--dropout_keep_prob', type=float,
                       default=0.5, help='keep probability in dropout layer')
    filter_sizes = [2, 4, 8]
    # ---------- training parameters --------
    # parse.add_argument('-if_use_all_true', '--if_use_all_true', type=int, default=0, help='if use all true labels for training')
    parse.add_argument('-if_output_all_labels', '--if_output_all_labels', type=int, default=0,
                       help='if output all labels')
    parse.add_argument('-n_epochs', '--n_epochs', type=int, default=10, help='number of epochs')
    parse.add_argument('-batch_size', '--batch_size', type=int, default=256, help='batch size for training')
    parse.add_argument('-batch_pid_size', '--batch_pid_size', type=int, default=5, help='batch pid size for testing')
    # parse.add_argument('-num_candidate', '--num_candidate', type=int, default=20, help='number of candidate labels')
    # parse.add_argument('-topk', '--topk', type=int, default=6, help='k in competitive layer')
    parse.add_argument('-show_batches', '--show_batches', type=int,
                       default=1000, help='show how many batches have been processed.')
    parse.add_argument('-lr', '--learning_rate', type=float, default=0.0001, help='learning rate')
    parse.add_argument('-update_rule', '--update_rule', type=str, default='adam', help='update rule')
    # ------ train or predict -------
    parse.add_argument('-train', '--train', type=int, default=1, help='if training')
    parse.add_argument('-test', '--test', type=int, default=0, help='if testing')
    parse.add_argument('-predict', '--predict', type=int, default=0, help='if predicting')
    args = parse.parse_args()

    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu
    print('-------------- load vocab and word embeddings ---------------')
    word_embeddings = np.load('datasets/material/' + args.word_embedding_path)
    # word_embedding_dim
    word_embedding_dim = word_embeddings.shape[-1]
    print('word_embeddings shape: ' + str(word_embeddings.shape))
    # add '<PAD>' embedding
    word_embeddings = np.concatenate((np.zeros((1, word_embedding_dim)), word_embeddings), axis=0)
    print('after add PAD embedding, word_embeddings shape:' + str(word_embeddings.shape))
    print('-------------- load label embeddings ------------------------')
    all_labels, label_embeddings = generate_label_embedding_from_file_2(args.folder_path + 'label.embeddings')
    label_embeddings = np.array(label_embeddings)
    label_dict = dict(zip(all_labels, range(len(all_labels))))
    print('number of labels: ' + str(len(all_labels)))
    # label_embedding_dim
    label_embedding_dim = len(label_embeddings[all_labels[0]])
    print('-------------- load label propensity ------------------------')
    label_prop = load_pickle(args.folder_path + 'inv_prop_dict.pkl')
    print('-------------- load train/test data -------------------------')
    train_doc = load_pickle(args.folder_path + 'train_doc_wordID.pkl')
    test_doc = load_pickle(args.folder_path + 'test_doc_wordID.pkl')
    train_label = load_pickle(args.folder_path + 'train_label.pkl')
    test_label = load_pickle(args.folder_path + 'test_label.pkl')
    print('-------------- load candidate labels ------------------------')
    if 'sleec' in args.model:
        candidate_type = 'sleec'
    elif 'pfastrexml' in args.model:
        candidate_type = 'pfastrexml'
    elif 'pfastxml' in args.model:
        candidate_type = 'pfastxml'
    elif 'fastxml' in args.model:
        candidate_type = 'fastxml'
    print('candidate from: ' + candidate_type)
    candidate_folder_path = args.folder_path + candidate_type + '_candidate/'
    train_candidate_label = load_pickle(candidate_folder_path + 'train_candidate_label.pkl')
    test_candidate_label = load_pickle(candidate_folder_path + 'test_candidate_label.pkl')
    print('============== create train/test data loader ...')
    if 'XML' not in args.model:
        train_loader = TrainDataLoader2(train_doc, train_label, train_candidate_label, label_dict, label_prop,
                                        10, 10, max_seq_len=args.max_seq_len)
        max_seq_len = train_loader.max_seq_len
        # max_seq_len = args.max_seq_len
        # train_loader = {}
        print('max_seq_len: ' + str(max_seq_len))
        test_loader = TestDataLoader2(test_doc, test_label, test_candidate_label, label_dict, label_prop,
                                      max_seq_len=max_seq_len, if_cal_metrics=args.cal_metrics)
        # test_loader = DataLoader3(test_doc, test_label, test_candidate_label, label_dict, args.batch_size,
        #                           given_seq_len=True, max_seq_len=max_seq_len)
    # ----------------------- train ------------------------
    print('============== build model ...')
    if 'biLSTM' in args.model:
        print('build biLSTM model ...')
        # biLSTM: max_seq_len, word_embedding_dim, hidden_dim, label_embedding_dim, num_classify_hidden, args.batch_size
        model = biLSTM(max_seq_len, word_embedding_dim, 64, label_embedding_dim, 32, args)
        args.if_use_seq_len = 1
    elif 'LSTM' in args.model:
        print('build LSTM model ...')
        # LSTM: max_seq_len, word_embedding_dim, hidden_dim, label_embedding_dim, num_classify_hidden, args.batch_size
        model = LSTM(max_seq_len, word_embedding_dim, 64, label_embedding_dim, 32, args)
        args.if_use_seq_len = 1
    elif 'CNN' in args.model:
        print('build CNN model ...')
        # CNN: sequence_length, word_embeddings, filter_sizes, label_embeddings, num_classify_hidden, args
        # args.num_filters, args.pooling_units, args.batch_size, args.dropout_keep_prob
        model = CNN(max_seq_len, word_embeddings, filter_sizes, label_embeddings, 32, args)
        args.if_use_seq_len = 0
    elif 'XML' in args.model:
        print('build XML-CNN model ...')
        train_loader = DataLoader5(train_doc, train_label, all_labels,
                                   args.batch_size,
                                   given_seq_len=False, max_seq_len=args.max_seq_len)
        max_seq_len = train_loader.max_seq_len
        test_loader = DataLoader5(test_doc, test_label, all_labels,
                                  args.batch_size,
                                  given_seq_len=True, max_seq_len=max_seq_len)
        # max_seq_len, word_embedding, filter_sizes, label_output_dim, hidden_dim, args
        # args.num_filters, args.pooling_units, args.batch_size, args.dropout_keep_prob
        model = XML_CNN(max_seq_len, word_embeddings, filter_sizes, len(all_labels), 128, args)
        args.if_output_all_labels = 1
        args.if_use_seq_len = 0

    print('================= model solver ...')
    # solver: __init__(self, model, train_data, test_data, **kwargs):
    solver = ModelSolver(model, train_loader, test_loader,
                         if_use_seq_len=args.if_use_seq_len,
                         if_output_all_labels=args.if_output_all_labels,
                         show_batches=args.show_batches,
                         n_epochs=args.n_epochs,
                         batch_size=args.batch_size,
                         update_rule=args.update_rule,
                         learning_rate=args.learning_rate,
                         pretrained_model=args.pretrained_model_path,
                         model_path=args.folder_path + args.model + '/',
                         test_path=args.folder_path + args.model + '/')
    # train
    if args.train:
        print('================= begin training...')
        solver.train(args.folder_path + args.model + '/outcome.txt')

    # test
    if args.test:
        print('================= begin testing...')
        solver.test(args.folder_path + args.model + '/' + args.pretrained_model_path,
                    args.folder_path + args.model + '/test_outcome.txt')

    # predict
    if args.predict:
        print('================= begin predicting...')
        predict_path = args.folder_path + 'model_save/' + args.model + '/'
        solver.predict(trained_model_path=predict_path,
                       output_file_path=predict_path + 'predict_outcome.txt',
                       k=10, emb_saved=1, can_saved=1)


if __name__ == "__main__":
    main()
