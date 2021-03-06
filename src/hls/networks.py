from __future__ import print_function

import tensorflow as tf
import inspect
import json
import os

from config import flags as config
from utils import merge_dict_a_into_b


def create_initializer(initializer_range=0.02):
  return tf.truncated_normal_initializer(stddev=initializer_range)

def w_network_fully_connected(w_var_scope, num_rules, w_dict, reuse=False, dropout_keep_prob=1.0):
    x = w_dict['x']
    rule = w_dict['rules'] #one hot rule representation
    rules_int = w_dict['rules_int'] #integer rule representation

    rule_or_emb = rule
    
    inputs = tf.concat(values = [x, rule_or_emb], axis=-1)

    prev_layer = inputs

    with tf.variable_scope(w_var_scope, reuse=reuse, initializer=create_initializer()) as vs:
        for i, num_neurons in enumerate(config.w_layers):
            cur_layer = tf.layers.dense(prev_layer, num_neurons,
                    activation=tf.nn.relu, name='w_layer_%d' % i)
            if config.network_dropout is True:
                cur_layer = tf.nn.dropout(cur_layer, dropout_keep_prob)
            prev_layer = cur_layer
        logit = tf.layers.dense(prev_layer, 1, name='w_linear_layer')
    return logit

def f_network_fully_connected(f_var_scope, f_dict, num_classes, 
                              reuse=False, ph_vars=None, 
                              dropout_keep_prob=1.0):
    
    x = f_dict['x']
    if not ph_vars:
        with tf.variable_scope(f_var_scope, reuse=reuse, initializer=create_initializer()) as vs:
            prev_layer = x
            for i, num_neurons in enumerate(config.f_layers):
                cur_layer = tf.layers.dense(prev_layer, num_neurons,
                        activation=tf.nn.relu)
                if config.network_dropout is True:
                    cur_layer = tf.nn.dropout(cur_layer, dropout_keep_prob)
                prev_layer = cur_layer

            logits = tf.layers.dense(prev_layer,num_classes)
    else:
        for i in range(0,len(ph_vars)-2,2):
            kernel = ph_vars[i]
            bias = ph_vars[i+1]
            x = tf.matmul(x,kernel)
            x = x + bias
            x = tf.nn.relu(x)
            if config.network_dropout is True:
                x = tf.nn.dropout(x,dropout_keep_prob)

        kernel = ph_vars[-2]
        bias = ph_vars[-1]
        logits = tf.matmul(x,kernel) + bias
    return logits
