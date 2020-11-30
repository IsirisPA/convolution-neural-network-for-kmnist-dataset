# -*- coding: utf-8 -*-
"""main_autoencoder.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gTwUxvLIbPbbylTeWWgpzSBwFWU_gvfS
"""

#from google.colab import drive
#drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
import os
import sys, getopt
import keras
import struct
import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt
# %matplotlib inline
from keras.models import Model
from keras.optimizers import RMSprop
from keras.layers import Input,Dense,Flatten,Dropout,merge,Reshape,Conv2D,MaxPooling2D,UpSampling2D,Conv2DTranspose
from keras.layers.normalization import BatchNormalization
from keras.models import Model,Sequential
from keras.callbacks import ModelCheckpoint
from keras.optimizers import Adadelta, RMSprop,SGD,Adam
from keras import regularizers
from keras import backend as K
from keras.utils import to_categorical
from array import array
from sklearn.model_selection import train_test_split

class MnistDataloader(object):

    def __init__(self, dataset):
        self.dataset = dataset
  
    def read_images_labels(self, images_filepath):        
        with open(images_filepath, 'rb') as file:
            magic, size, rows, cols = struct.unpack(">IIII", file.read(16))
            if magic != 2051:
                raise ValueError('Magic number mismatch, expected 2051, got {}'.format(magic))
            image_data = array("B", file.read())        
        images = []
        for i in range(size):
            images.append([0] * rows * cols)
        for i in range(size):
            img = np.array(image_data[i * rows * cols:(i + 1) * rows * cols])
            img = img.reshape(28, 28)
            images[i][:] = img            
        
        return images
            
    def load_data(self):
        data = self.read_images_labels(self.dataset)
        return data

def encoder(input_img, num_conv2d, conv2d_sizes): 

    if (num_conv2d < 1):
        print("Number of convolutional layers must be at least 1.")
        return
    elif (num_conv2d != len(conv2d_sizes)):
        print("Number of convolutional layers and length of convolutional layer sizes list must agree.")
        return 
    else:
        encode = Conv2D(conv2d_sizes[0], (3, 3), activation='sigmoid', padding='same')(input_img)
        encode = BatchNormalization()(encode)
        encode = MaxPooling2D(pool_size=(2, 2))(encode)
        encode = Dropout(0.25)(encode)
        for layer in range(1,num_conv2d):
            encode = Conv2D(conv2d_sizes[layer], (3, 3), activation='sigmoid', padding='same')(encode)
            encode = BatchNormalization()(encode)
            if (layer == 1):
                encode = MaxPooling2D(pool_size=(2, 2))(encode)
                encode = Dropout(0.25)(encode)
            if (layer != num_conv2d - 1 and layer != 1):
                encode = Dropout(0.30)(encode)
        return encode


def decoder(encode, num_conv2d, conv2d_sizes):    

    if (num_conv2d < 1):
        print("Number of convolutional layers must be at least 1.")
        return
    elif (num_conv2d != len(conv2d_sizes)):
        print("Number of convolutional layers and length of convolutional layer sizes list must agree.")
        return 
    else:
        sizes = list()
        sizes = conv2d_sizes
        sizes.pop()
        sizes.reverse()
        decode = Conv2D(sizes[0], (3, 3), activation='sigmoid', padding='same')(encode)
        decode = BatchNormalization()(decode)
        for layer in range(1,num_conv2d - 1):
            if (layer >= num_conv2d - 3):
                decode = UpSampling2D((2,2))(decode)
            decode = Conv2D(sizes[layer], (3, 3), activation='sigmoid', padding='same')(decode)
            if (layer != num_conv2d - 2):
                decode = BatchNormalization()(decode)
        return decode

def main(argv):

    #DATA LOADING

    dataset_filepath = ''
    try:
        opts, args = getopt.getopt(argv,"d:",["ifile="])
    except getopt.GetOptError:
        print("error on giving arguments")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-d", "--ifile"):
            dataset_filepath = arg
      
    mnist_dataloader = MnistDataloader(dataset_filepath)
    dataset = mnist_dataloader.load_data()

    #DATA PARTITIONING (80% train , 20% test)
    train_x, train_y, test_x, test_y = train_test_split(dataset, dataset, test_size=0.2, random_state=13)

    #DATA PREPROCESSING

    #convert data into numpy array
    train_x = np.array(train_x)
    test_x = np.array(test_x)

    #specify datatype
    train_x = train_x.astype('float32')
    test_x = test_x.astype('float32')

    #convert each 28 x 28 image into a matrix of size 28 x 28 x 1, which will be fed into the network
    train_x = train_x.reshape(len(train_x), 28, 28, 1)
    test_x = test_x.reshape(len(test_x), 28, 28, 1)

    #rescale  with respective maximum pixel value (here 255)
    train_x = train_x / 255.0
    test_x = test_x / 255.0
    

    #print(train_x.shape)
    
    # divide the data properly (80% train , 20% validation)
    train_x,valid_x,train_label,valid_label = train_test_split(train_x, train_x, test_size=0.2, random_state=13)
    
    while(1):

        #request hyperparameters from the user
        batch_size = int(input("Type batch size: ")  )
        epochs = int(input("Type epochs: "))
        num_conv2d = int(input("Type number of convolutional layers: "))
        conv2d_sizes = list()
        for i in range(num_conv2d):
            conv2d_sizes.append(int(input("Type size of convolutional layer: ")))

        inChannel = 1
        x, y = 28, 28
        input_img = Input(shape = (x, y, inChannel))
        num_classes = 10

        #create model
        #autoencoder = Model(input_img, decoder(encoder(input_img)))
 
        autoencoder = Model(input_img, decoder(encoder(input_img, num_conv2d, conv2d_sizes), num_conv2d, conv2d_sizes))

        #compile model using the optimizer to be RMSProp
        autoencoder.compile(loss='mean_squared_error', optimizer = RMSprop())  

        autoencoder.summary() #optional visualize the layers created above

        #model training
        autoencoder_train = autoencoder.fit(train_x, train_label, batch_size=batch_size,epochs=epochs,verbose=1,validation_data=(valid_x, valid_label))


        print("Type 1 to continue with another experiment.")
        print("Type 2 to to show plots.")
        print("Type 3 to save current model.")
        try:
            choice = int(input())
            if(choice == 1):
                continue
            elif(choice == 2):
                #print("show plots")
                loss = autoencoder_train.history['loss']
                val_loss = autoencoder_train.history['val_loss']
                epochs = range(int(epochs))
                plt.figure()
                plt.plot(epochs, loss, 'bo', label='loss')
                plt.plot(epochs, val_loss, 'b', label='Validation loss')
                plt.title('Training and validation loss')
                plt.ylim(0.00, 0.03)
                plt.legend()
                plt.show()
                break
            elif(choice == 3):
                model_path = input("Please type the path to store the model: ")
                #autoencoder.save_weights('autoencoder.h5')
                autoencoder.save_weights(model_path)
                break
            else:
                raise Exception("Invalid key.")
        except:
            print("Program terminates.")
            break

if __name__ == "__main__":
    main(sys.argv[1:])