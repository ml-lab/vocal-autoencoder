import tensorflow as tf
import numpy as np
import math
import random

import sys

import os
import glob

from wav import loadfft, savefft, sanity

TRAIN_REPEAT=1
DIMS=[512,256]
#SIZE=256
SIZE=64

def create(x, layer_sizes):

        # Build the encoding layers
        next_layer_input = x

        encoding_matrices = []
        for i, dim in enumerate(layer_sizes):
                input_dim = int(next_layer_input.get_shape()[1])

                # Initialize W using random values in interval [-1/sqrt(n) , 1/sqrt(n)]
                W = tf.Variable(tf.random_uniform([input_dim, dim], -1.0 / math.sqrt(input_dim), 1.0 / math.sqrt(input_dim)))

                # Initialize b to zero
                b = tf.Variable(tf.zeros([dim]))

                # We are going to use tied-weights so store the W matrix for later reference.
                encoding_matrices.append(W)

                output = tf.nn.tanh(tf.matmul(next_layer_input,W) + b,name='encoder-'+str(i))

                # the input into the next layer is the output of this layer
                next_layer_input = output

        # The fully encoded x value is now stored in the next_layer_input
        encoded_x = next_layer_input

        # build the reconstruction layers by reversing the reductions
        layer_sizes.reverse()
        encoding_matrices.reverse()


        for i, dim in enumerate(layer_sizes[1:] + [ int(x.get_shape()[1])]) :
                # we are using tied weights, so just lookup the encoding matrix for this step and transpose it
                W = tf.transpose(encoding_matrices[i])
                b = tf.Variable(tf.zeros([dim]))
                output = tf.nn.tanh(tf.matmul(next_layer_input,W) + b)
                next_layer_input = output

        # the fully encoded and reconstructed value of x is here:
        reconstructed_x = next_layer_input

        return {
                'encoded': encoded_x,
                'decoded': reconstructed_x,
                'cost' : tf.sqrt(tf.reduce_mean(tf.square(x-reconstructed_x)))
        }

def deep_test():
        sess = tf.Session()

        x = tf.placeholder("float", [None, SIZE],name='x')
        autoencoder = create(x, DIMS)
        #train_step = tf.train.GradientDescentOptimizer(3.0).minimize(autoencoder['cost'])
        train_step = tf.train.AdamOptimizer(1e-3).minimize(autoencoder['cost'])
        init = tf.initialize_all_variables()
        sess.run(init)
        saver = tf.train.Saver()
        saver.save(sess, 'model.ckpt')

        tf.train.write_graph(sess.graph_def, 'log', 'model.pbtxt', False)

        #output = irfft(filtered)
        i=0
        #write('output.wav', rate, output)
        for trains in range(TRAIN_REPEAT):
            for file in glob.glob('training/*.wav'):
                i+=1
                learn(file, sess, train_step, x,i, autoencoder, saver)
        

def learn(filename, sess, train_step, x, k, autoencoder, saver):
        wavobj = loadfft(filename)
        transformed = wavobj['transformed']
        transformed_raw = wavobj['raw']
        rate = wavobj['rate']

        batch = []
        # do 1000 training steps
        for i in range(int(len(transformed)/SIZE)): # Our dataset consists of two centers with gaussian noise w/ sigma = 0.1
                c1 = transformed[i*SIZE:i*SIZE+SIZE]
                batch += [c1]
        sess.run(train_step, feed_dict={x: np.array(batch)})
        print(k,filename, " cost", sess.run(autoencoder['cost'], feed_dict={x: batch}))
        #print(i, " original", batch[0])
        #print( i, " decoded", sess.run(autoencoder['decoded'], feed_dict={x: batch}))
        saver.save(sess, 'model.ckpt')

def deep_gen():
        sess = tf.Session()
        wavobj = loadfft('input.wav')
        sanity(wavobj)
        transformed = wavobj['transformed']

        x = tf.placeholder("float", [None, SIZE], name='x')
        autoencoder = create(x, DIMS)
        init = tf.initialize_all_variables()
        sess.run(init)
        saver = tf.train.Saver()
        saver.restore(sess, 'model.ckpt')





        filtered = np.array([])
        # do 1000 training steps
        batch = []
        # do 1000 training steps
        for i in range(int(len(transformed)/SIZE)):
                # Our dataset consists of two centers with gaussian noise w/ sigma = 0.1
                c1 = transformed[i*SIZE:i*SIZE+SIZE]
                batch += [c1]

        decoded = sess.run(autoencoder['decoded'], feed_dict={x: np.array(batch)})
        #decoded = sess.run(autoencoder['decoded'], feed_dict={x: np.array(np.random.normal(0,1,[len(batch), 8192]))})
        ded = decoded.ravel()
        #filtered = np.append(filtered, batch)
        filtered = np.append(filtered,ded)
        #print(i, " cost", sess.run(autoencoder['cost'], feed_dict={x: batch}))
        #print(i, " original", batch[0])
        #print( i, " decoded", sess.run(autoencoder['decoded'], feed_dict={x: batch}))
        savefft('output.wav', wavobj, filtered)
                       
if __name__ == '__main__':
    if(sys.argv[1] == 'train'):
        print("Train")
        deep_test()
    else:
        print("Generate")
        deep_gen()


