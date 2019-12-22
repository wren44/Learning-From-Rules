from hls_data_types import test_w
from utils import merge_dict_a_into_b
import data_utils
import metrics_utils
import tensorflow as tf
import numpy as np
from sklearn.metrics import precision_recall_fscore_support
from analyze_w_predictions import analyze_w_predictions

class HLSTest():
    def __init__(self, hls, config):
        self.hls = hls
        self.config = config

    def maybe_save_predictions(self, save_filename, x, l, m, preds, d):
        if save_filename is None:
            return

        save_x = []
        save_l = []
        save_m = []
        save_preds = []
        save_d = []
        for xx, ll, mm, dd, p in zip(x, l, m, d, preds):
            save_x.append(xx)
            save_l.append(ll)
            save_m.append(mm)
            save_d.append(dd)
            save_preds.append(p)
                

        data_utils.dump_labels_to_file(save_filename,
                np.array(save_x),
                np.array(save_l),
                np.array(save_m),
                np.array(save_preds),
                np.array(save_d))

    def test_f(self, datafeeder, log_output=False, data_type='test_f', save_filename=None):
        sess = self.hls.sess
        with sess.as_default():
            # Test model
            probs = tf.nn.softmax(self.hls.f_d_logits)  # Apply softmax to logits
            pred = tf.argmax(probs, 1)
            labels = tf.argmax(self.hls.f_d_labels, 1)
            correct_prediction = tf.equal(pred, labels)
            # Calculate accuracy
            accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
            test_x, test_y, l, m, d = datafeeder.get_f_test_data(data_type)
            feed_dict = {
                    self.hls.f_x: test_x,
                    self.hls.f_d_labels: test_y
                    }
            try:
                merge_dict_a_into_b(self.hls.dropout_test_dict,feed_dict)
            except KeyError:
                pass
            acc, pred1, labels1 = sess.run([accuracy, pred, labels], feed_dict=feed_dict)
            precision, recall, f1_score, support = precision_recall_fscore_support(labels1, pred1)
            accuracy1 = metrics_utils.compute_accuracy(support, recall)

            # save predictions to file
            self.maybe_save_predictions(save_filename, test_x, l, m, pred1, d)
            if log_output:
                print('test_f: precision: ', precision)
                print('test_f: recall: ', recall)
                print('test_f: f1_score: ', f1_score)
                print('test_f: support: ', support)
                print('test_f: accuracy: ', accuracy1)
                print('test_f: avg_f1_score: ',np.mean(f1_score))

            return precision, recall, f1_score, support

    # We test w using data from d
    #
    # data_type is either test_w or covered_U
    def test_w(self, datafeeder, log_output=False, data_type=test_w, save_filename=None):
        sess = self.hls.sess
        total_preds = []
        total_true_labels = []
        with sess.as_default():
            # Test model
            f_d_U_probs = self.hls.f_d_U_probs
            weights = self.hls.f_d_U_weights

            # Calculate accuracy
            total_batch = datafeeder.get_batches_per_epoch(data_type)

            if save_filename is not None:
                save_x = []
                save_l = []
                save_m = []
                save_L = []
                save_d = []
                save_weights = []
                save_f_d_U_probs = []

            for i in range(total_batch):
                x, l, m, L, d  = datafeeder.get_w_test_data(data_type)
                feed_dict = {
                        self.hls.f_d_U_x: x,
                        self.hls.f_d_U_l: l,
                        self.hls.f_d_U_m: m,
                        self.hls.f_d_U_L: L,
                        self.hls.f_d_U_d: d
                        }
                merge_dict_a_into_b(self.hls.dropout_test_dict,feed_dict)
                infered_weights, f_probs = sess.run([weights, f_d_U_probs],feed_dict=feed_dict)
                        
                if save_filename:
                    for xx, ll, mm, LL, dd, w, f_p in zip(x, l, m, L, d, infered_weights, f_probs):
                        save_x.append(xx)
                        save_l.append(ll)
                        save_m.append(mm)
                        save_L.append(LL)
                        save_d.append(dd)
                        save_weights.append(w)                        
                        save_f_d_U_probs.append(f_p)

            if save_filename:
                # Dump pickles
                data_utils.dump_labels_to_file(save_filename,
                        np.array(save_x),
                        np.array(save_l),
                        np.array(save_m),
                        np.array(save_L),
                        np.array(save_d),
                        np.array(save_weights),                        
                        np.array(save_f_d_U_probs),
                        self.hls.rule_classes_list)

            analyze_w_predictions(np.array(save_x),
                                  np.array(save_l),
                                  np.array(save_m),
                                  np.array(save_L),
                                  np.array(save_d),
                                  np.array(save_weights),                        
                                  np.array(save_f_d_U_probs),
                                  self.hls.rule_classes_list)