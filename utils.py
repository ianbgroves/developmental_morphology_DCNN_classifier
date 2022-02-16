import tensorflow as tf  # version 2.5
from tensorflow import keras
from tensorflow.keras.layers import LeakyReLU, Softmax
from tensorflow.keras.layers import Conv2D, MaxPooling2D, SeparableConv2D
from tensorflow.keras.layers import Dense, Flatten, Dropout, Reshape, Activation
from tensorflow.keras.layers import InputLayer, Input
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.layers import LSTM
from tensorflow.keras.optimizers import Adam, Adagrad, Adadelta, Adamax, SGD, Ftrl, Nadam, RMSprop
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras import backend as K
from tensorflow.keras.utils import to_categorical
from tensorflow.keras import Sequential
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras import regularizers

import imgaug as ia
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import PIL
from pathlib import Path
from tensorflow.keras import layers
from imgaug import augmenters as iaa
import imageio
from PIL import Image
import os, sys
import cv2
import imutils
from datetime import datetime
import math
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import math

from pylab import *
from numpy import *

from random import random, seed, shuffle
from scipy.ndimage import geometric_transform
from scipy.ndimage import map_coordinates
from PIL import Image, ImageOps
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.ticker as plticker
import matplotlib as mpl
from sklearn.cluster import KMeans
import seaborn as sns
sns.set_theme(style="white")

#resnet50 imports
from tensorflow.keras.applications.resnet50 import ResNet50
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input

#inceptionv3 imports
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.applications.inception_v3 import preprocess_input as preprocess_inception


def k_fold_splitter(split_aug, k):

  training_list = []
  val_list = []
  for i in range(0,k):
    val_list.append(np.array(split_aug[i]))
    training_list.append(np.delete(split_aug, i))


  return val_list, training_list

def aug_rot(split):
  split_aug = []
  for feature, label in split:
    for angle in np.arange(0, 360, 10):
      rotate = iaa.geometric.Affine(rotate = angle)
      feature = rotate(image = feature)
      split_aug.append([feature, label])
  return split_aug

def aug_shear(split):
  split_aug = []
  for feature, label in split:
    for angle in np.arange(0, 360, 10):
      # feature = cv2.equalizeHist(feature)
      shear = iaa.ShearX(20)
      rotate = iaa.geometric.Affine(rotate = angle)
      feature = rotate(image = feature)
      feature2 = shear(image = rotate(image = feature))
      split_aug.append([feature, label])
      split_aug.append([feature2, label])
      return split_aug

def aug_g_blur(split):
  split_aug = []
  for feature, label in split:
    for angle in np.arange(0, 360, 10):
        # feature = cv2.equalizeHist(feature)
        gblur = iaa.GaussianBlur(sigma = 5)
        feature2 = gblur(image = feature)
        rotate = iaa.geometric.Affine(rotate = angle)
        feature = rotate(image = feature)
        feature2 = rotate(image = feature2)
        split_aug.append([feature, label])
        split_aug.append([feature2, label])
        return split_aug

def aug_cutout(split):
  split_aug = []
  for feature, label in split:
    for angle in np.arange(0, 360, 10):
        # feature = cv2.equalizeHist(feature)
        cutout = iaa.Cutout()
        feature2 = cutout(image = feature)
        feature3 = cutout(image = feature)
        rotate = iaa.geometric.Affine(rotate = angle)
        feature = rotate(image = feature)
        feature2 = rotate(image = feature2)
        feature3 = rotate(image = feature3)
        split_aug.append([feature, label])
        split_aug.append([feature2, label])
        split_aug.append([feature3, label])
        return split_aug

def aug_crop(split):
  split_aug = []
  for feature, label in split:
    for percent in np.arange(0, 0.3, 0.01):
        # feature = cv2.equalizeHist(feature)
        crop = iaa.Crop(percent = percent)
        feature = crop(image = feature)
        split_aug.append([feature, label])
        return split_aug

def aug_rand_comb(split):
  split_aug = []
  gblurstr, cutoutstr, shearstr = 'gblurstr', 'cutoutstr', 'shearstr'
  choices = [gblurstr, cutoutstr, shearstr]
  for feature, label in split:
    augmentation = np.random.choice(choices)
    if cutoutstr in augmentation:
        #do rotation and cutout
        print('doing cutout')
        for angle in np.arange(0, 360, 10):
            # feature = cv2.equalizeHist(feature)
            cutout = iaa.Cutout()
            feature2 = cutout(image = feature)
            feature3 = cutout(image = feature)
            rotate = iaa.geometric.Affine(rotate = angle)
            feature = rotate(image = feature)
            feature2 = rotate(image = feature2)
            feature3 = rotate(image = feature3)
            split_aug.append([feature, label])
            split_aug.append([feature2, label])
            split_aug.append([feature3, label])
    elif gblurstr in augmentation:
        #do rotation and gblur
        print('doing gblur')
        for angle in np.arange(0, 360, 10):
            # feature = cv2.equalizeHist(feature)
            gblur = iaa.GaussianBlur(sigma = 5)
            feature2 = gblur(image = feature)
            rotate = iaa.geometric.Affine(rotate = angle)
            feature = rotate(image = feature)
            feature2 = rotate(image = feature2)
            split_aug.append([feature, label])
            split_aug.append([feature2, label])
    else:
        #do rotation and shear
        print('doing shear')
        for angle in np.arange(0, 360, 10):
            # feature = cv2.equalizeHist(feature)
            shear = iaa.ShearX(20)
            rotate = iaa.geometric.Affine(rotate = angle)
            feature = rotate(image = feature)
            feature2 = shear(image = rotate(image = feature))
            split_aug.append([feature, label])
            split_aug.append([feature2, label])
  return split_aug

def create_training_data(imformat, duplicate_channels):
  tdata = []
  for img in os.listdir('labeled_data/10_1'):  # iterate over each image
      try:
          img_array = Image.open('labeled_data/10_1/{}'.format(img)).convert(imformat)
          img_array = ImageOps.equalize(img_array, mask= None)
          if duplicate_channels:
            img_array = img_array.convert('RGB')                 
          img_array = img_array.resize((200,200), Image.ANTIALIAS)
          img_array = np.array(img_array)
          tdata.append([img_array, 0])
      except Exception as e:  
          pass
  for img in os.listdir('labeled_data/10_2'):  # iterate over each image
      try:
          img_array = Image.open('labeled_data/10_2/{}'.format(img)).convert(imformat) 
          img_array = ImageOps.equalize(img_array, mask= None)
          if duplicate_channels:
            img_array = img_array.convert('RGB')                 
          img_array = img_array.resize((200,200), Image.ANTIALIAS)
          img_array = np.array(img_array)
          tdata.append([img_array, 1])
      except Exception as e:  
          pass
  for img in os.listdir('labeled_data/10_3'):  # iterate over each image
      try:
          img_array = Image.open('labeled_data/10_3/{}'.format(img)).convert(imformat) 
          img_array = ImageOps.equalize(img_array, mask= None)
          if duplicate_channels:
            img_array = img_array.convert('RGB')             
          img_array = img_array.resize((200,200), Image.ANTIALIAS)
          img_array = np.array(img_array)
          tdata.append([img_array, 2])
      except Exception as e:  
          pass
  return tdata

def train_model(train, val, name):
  from datetime import date as dt
  seed(1234)
  shuffle(train)
  shuffle(val)

  # Preprocessing the data into X_train etc with relevant input shapes
  X_train = []
  y_train = []
  X_val = []
  y_val = []
  img_size = 200

  for i in train:
    for feature, label in i:
      X_train.append(feature)
      y_train.append(label)
  for feature, label in val:
    X_val.append(feature)
    y_val.append(label)

  X_train = np.array(X_train) / 255
  X_val = np.array(X_val) / 255

  X_train = X_train.reshape(X_train.shape[0], 200, 200, 1)
  X_val = X_val.reshape(X_val.shape[0], 200, 200, 1)

  X_train.astype('float32')
  X_val.astype('float32')
  print('X_train shape:', np.shape(X_train))
  print('X_val shape:', np.shape(X_val))


  y_train=to_categorical(y_train)
  y_val=to_categorical(y_val)
  print('y_train shape:', np.shape(y_train))
  print('y_val shape:', np.shape(y_val))

  layer_drop = 0.2
  final_drop = 0.5
  activation = 'relu'
  lamda = 0.0001

  model = Sequential([
    layers.Conv2D(16, 3, padding='same', activation= activation, input_shape = (200, 200, 1), kernel_regularizer=regularizers.l2(lamda)),
    layers.Dropout(layer_drop),
    layers.MaxPooling2D((2,2), padding='same'),
    layers.Conv2D(32, 3, padding='same', activation=activation, kernel_regularizer=regularizers.l2(lamda)),
    layers.Dropout(layer_drop),
    layers.MaxPooling2D((2,2), padding='same'),
    layers.Conv2D(64, 3, padding='same', activation=activation, kernel_regularizer=regularizers.l2(lamda)),
    layers.Dropout(layer_drop),
    layers.MaxPooling2D((2,2), padding='same'),
    layers.Conv2D(128, 3, padding='same', activation=activation, kernel_regularizer=regularizers.l2(lamda)),
    layers.Dropout(layer_drop),
    layers.MaxPooling2D((2,2), padding='same'),
    layers.Conv2D(256, 3, padding='same', activation=activation, kernel_regularizer=regularizers.l2(lamda)),
    layers.Dropout(layer_drop),
    layers.MaxPooling2D((2,2), padding='same'),
    layers.Conv2D(512, 3, padding='same', activation=activation, kernel_regularizer=regularizers.l2(lamda)),
    layers.Dropout(layer_drop),
    layers.MaxPooling2D((2,2), padding='same'),
    layers.Conv2D(1024, 3, padding='same', activation=activation, kernel_regularizer=regularizers.l2(lamda)),
    layers.Dropout(layer_drop),
    layers.MaxPooling2D((2,2), padding='same'),
    layers.Flatten(),
    layers.Dense(1024, activation=activation),
    layers.Dropout(final_drop),
    layers.Dense(3, activation = 'softmax')
  ])

  model.compile(optimizer = Adam(learning_rate = 0.0001),
                loss = 'categorical_crossentropy',
                metrics = ['accuracy'])

  earlyStop = EarlyStopping(monitor = 'val_accuracy', min_delta = 0.01, patience = 10, mode='auto', restore_best_weights=True)
  epochs = 50
  history = model.fit(x=X_train,
                      y=y_train,
                      epochs=epochs,
                      batch_size=32,
                      validation_data=(X_val, y_val),
                      callbacks=[earlyStop])



  acc = history.history['accuracy']
  val_acc = history.history['val_accuracy']
  loss = history.history['loss']
  val_loss = history.history['val_loss']
  accuracy = history.history['val_accuracy'][-1]

  today = dt.today()
  date = today.strftime("%b-%d-%Y")
  model.save(model_path + name + '{}'.format(date))

  del model
  K.clear_session()

  return round(max(val_acc)*100, 1)

def read_args(baseline=False, cutout=False, shear=False, g_blur=False, crop=False, rand_comb=False, mobius=False):
  import argparse

  # Initialise parser
  parser = argparse.ArgumentParser(description='One augmentation must be selected, type --help for details')

  # Adding optional argument
  parser.add_argument('--baseline', dest='baseline', default=False, action='store_true', help = 'if set, augments the data with baseline')
  parser.add_argument('--cutout', dest='cutout', default=False, action='store_true',  help = 'if set, augments the data with cutout')
  parser.add_argument('--shear', dest='shear', default=False, action='store_true',  help = 'if set, augments the data with shear')
  parser.add_argument('--gblur', dest='gblur', default=False, action='store_true',  help = 'if set, augments the data with gblur')
  parser.add_argument('--crop', dest='crop', default=False, action='store_true',  help = 'if set, augments the data with crop')
  parser.add_argument('--randcomb', dest='randcomb', default=False, action='store_true',  help = 'if set, augments the data with randcomb')  
  parser.add_argument('--mobius', dest='mobius', default=False, action='store_true',  help = 'if set, augments the data with mobius transforms')  

  # Read arguments from command line
  args = parser.parse_args()

  while(True):
      if vars(args)['baseline']:
          baseline = True
          break
      if vars(args)['cutout']:
          cutout = True
          break
      if vars(args)['shear']:
          shear = True
          break
      if vars(args)['gblur']:
          g_blur = True
          break
      if vars(args)['crop']:
          crop = True
          break
      if vars(args)['randcomb']:
          rand_comb = True
          break
      if vars(args)['mobius']:
          mobius = True
          break
      else:
        print('No augmentation set, please parse \"--help", or refer to README.txt')
        exit()
  return baseline, cutout, shear, g_blur, crop, rand_comb, mobius

def aug_mobius(split, M, mode, user_defined, rgb):
  split_aug = []
  start_points = 32, 16, 16, 32, 32, 48 
  end_points = 16, 32, 32, 48, 48, 32

  #do the mobius transforms
  for feature, label in split:
    feature, uninterpolated_feature = mobius_fast_interpolation('example', True, feature,
                                                              M, 
                                                              mode = mode, rgb = rgb, 
                                                              output_height=200, 
                                                              output_width=200,
                                                              user_defined=user_defined,
                                                              start_points = start_points,
                                                              end_points = end_points)
    feature = np.array(feature)
    split_aug.append([feature, label])
    # for angle in np.arange(0,360,10):
    #   rotate = iaa.geometric.Affine(rotate = angle)
    #   feature = rotate(image = feature)
    #   # feature = np.array(rotate) 

  return split_aug

# def aug_rot(split):
  # split_aug = []
  # for feature, label in split:
    # for angle in np.arange(0, 360, 10):
      # rotate = iaa.geometric.Affine(rotate = angle)
      # feature = rotate(image = feature)
      # split_aug.append([feature, label])
  # return split_aug


def train_model_inceptionv3(train, val, name):
  from datetime import date as dt
  seed(1234)
  shuffle(train)
  shuffle(val)

  # Preprocessing the data into X_train etc with relevant input shapes
  X_train = []
  y_train = []
  X_val = []
  y_val = []
  img_size = 200

  for i in train:
    for feature, label in i:
      X_train.append(feature)
      y_train.append(label)
  for feature, label in val:
    X_val.append(feature)
    y_val.append(label)

  X_train = np.array(X_train) / 255
  X_val = np.array(X_val) / 255

  X_train = preprocess_inception(X_train)
  X_val = preprocess_inception(X_val)
  
  y_train=to_categorical(y_train)
  y_val=to_categorical(y_val)

  print('X_train shape:', np.shape(X_train))
  print('X_val shape:', np.shape(X_val))

  print('y_train shape:', np.shape(y_train))
  print('y_val shape:', np.shape(y_val))


  inception_model = InceptionV3(include_top=False, weights=None, input_tensor=None, input_shape=(200, 200, 3), pooling=None)
  flattened_output = tf.keras.layers.Flatten()(inception_model.output)
  fc_classification_layer = tf.keras.layers.Dense(3, activation='softmax')(flattened_output)
  model = tf.keras.models.Model(inputs=inception_model.input, outputs = fc_classification_layer)
  model.compile(optimizer = Adam(learning_rate = 0.00001),
                loss = 'categorical_crossentropy',
                metrics = ['accuracy'])

  early_stop = EarlyStopping(monitor = 'val_accuracy', min_delta = 0.01, patience = 10, mode='auto', restore_best_weights=True)
  epochs = 50
  
  history = model.fit(x=X_train,
                      y=y_train,
                      epochs=epochs,
                      batch_size=32,
                      validation_data=(X_val, y_val),
                      callbacks=[early_stop])



  acc = history.history['accuracy']
  val_acc = history.history['val_accuracy']
  loss = history.history['loss']
  val_loss = history.history['val_loss']
  accuracy = history.history['val_accuracy'][-1]

  today = dt.today()
  date = today.strftime("%b-%d-%Y")
  model.save('new_models_dec_2021/' + name + '{}'.format(date))

  del model
  K.clear_session()

  return round(max(val_acc)*100, 1)


def train_model_resnet50(train, val, name):
  from datetime import date as dt
  seed(1234)
  shuffle(train)
  shuffle(val)

  # Preprocessing the data into X_train etc with relevant input shapes
  X_train = []
  y_train = []
  X_val = []
  y_val = []
  img_size = 200

  for i in train:
    for feature, label in i:
      X_train.append(feature)
      y_train.append(label)
  for feature, label in val:
    X_val.append(feature)
    y_val.append(label)

  X_train = np.array(X_train) / 255
  X_val = np.array(X_val) / 255

  X_train = preprocess_input(X_train)
  X_val = preprocess_input(X_val)
  
  y_train=to_categorical(y_train)
  y_val=to_categorical(y_val)

  print('X_train shape:', np.shape(X_train))
  print('X_val shape:', np.shape(X_val))

  print('y_train shape:', np.shape(y_train))
  print('y_val shape:', np.shape(y_val))



  resnet50_model = ResNet50(include_top=False, weights=None, input_tensor=None, input_shape=(200, 200, 3), pooling=None)
  flattened_output = tf.keras.layers.Flatten()(resnet50_model.output)
  fc_classification_layer = tf.keras.layers.Dense(3, activation='softmax')(flattened_output)
  model = tf.keras.models.Model(inputs=resnet50_model.input, outputs = fc_classification_layer)
  model.compile(optimizer = Adam(learning_rate = 0.00001),
                loss = 'categorical_crossentropy',
                metrics = ['accuracy'])

  early_stop = EarlyStopping(monitor = 'val_accuracy', min_delta = 0.01, patience = 10, mode='auto', restore_best_weights=True)
  epochs = 50

  
  history = model.fit(x=X_train,
                      y=y_train,
                      epochs=epochs,
                      batch_size=32,
                      validation_data=(X_val, y_val),
                      callbacks=[early_stop])



  acc = history.history['accuracy']
  val_acc = history.history['val_accuracy']
  loss = history.history['loss']
  val_loss = history.history['val_loss']
  accuracy = history.history['val_accuracy'][-1]

  today = dt.today()
  date = today.strftime("%b-%d-%Y")
  model.save('new_models_dec_2021/' + name + '{}'.format(date))

  del model
  K.clear_session()

  return round(max(val_acc)*100, 1)
  

def parse_args():
  import argparse

  # Initialise parser
  parser = argparse.ArgumentParser(description='One augmentation must be selected, type --help for details')

  # Adding optional argument
  parser.add_argument('--baseline', dest='baseline', default=False, action='store_true', help = 'if set, augments the data with baseline')
  parser.add_argument('--cutout', dest='cutout', default=False, action='store_true',  help = 'if set, augments the data with cutout')
  parser.add_argument('--shear', dest='shear', default=False, action='store_true',  help = 'if set, augments the data with shear')
  parser.add_argument('--gblur', dest='gblur', default=False, action='store_true',  help = 'if set, augments the data with gblur')
  parser.add_argument('--crop', dest='crop', default=False, action='store_true',  help = 'if set, augments the data with crop')
  parser.add_argument('--randcomb', dest='randcomb', default=False, action='store_true',  help = 'if set, augments the data with randcomb')  
  parser.add_argument('--mobius', dest='mobius', default=False, action='store_true',  help = 'if set, augments the data with mobius transforms')  

  # Read arguments from command line
  args = parser.parse_args()

  while(True):
      if vars(args)['baseline']:
          baseline = True
          break
      if vars(args)['cutout']:
          cutout = True
          break
      if vars(args)['shear']:
          shear = True
          break
      if vars(args)['gblur']:
          gblur = True
          break
      if vars(args)['crop']:
          crop = True
          break
      if vars(args)['randcomb']:
          randcomb = True
          break
      if vars(args)['mobius']:
          randcomb = True
          break
      else:
        print('No augmentation set, please parse \"--help", or refer to README.txt')
        exit()
  return baseline, cutout, shear, gblur, crop, randcomb, mobius

# Adapted from https://github.com/stanfordmlgroup/mobius
def shift_func(coords,a,b,c,d):
    """ Define the mobius transformation, though backwards """
    #turn the first two coordinates into an imaginary number
    z = coords[0] + 1j*coords[1]
    w = (d*z-b)/(-c*z+a) #the inverse mobius transform
    #take the color along for the ride
    return real(w),imag(w),coords[2]

# Adapted from https://github.com/stanfordmlgroup/mobius
def mobius_fast_interpolation(name, save, image, M, mode, rgb, output_height=None, output_width=None, user_defined=False, start_points = None, end_points = None):
    image = np.array(image)
    original_image=image
    height=image.shape[0]
    width=image.shape[1]

    # User can pick output size
    if output_height == None:
        output_height = height
    if output_width == None:
        output_width = width
    if user_defined ==True:
        # Method one 
        # You pick starting and ending point
        a, b, c, d, original_points,new_points = getabcd_1fix(height,width,start_points, end_points)
    else:
        # Method two
        # Randomly generated starting the ending point
        a, b, c, d,original_points,new_points  = madmissable_abcd(M,height,width)
    e=[complex(0,0)]*height*width
    z=np.array(e).reshape(height,width)
    for i in range(0,height):
        for j in range(0,width):
            z[i,j]=complex(i,j)
    i=np.array(list(range(0,height))*width).reshape(width,height).T
    j=np.array(list(range(0,width))*height).reshape(height,width)

    r = ones((output_height, output_width,3),dtype=uint8)*255*0        
    w = (a*z+b)/(c*z+d)
    first=real(w)*1
    second=imag(w)*1
    first=first.astype(int)
    second=second.astype(int)
    
    f1=first>=0
    f2=first<output_height
    f= f1 & f2
    s1=second>=0
    s2=second<output_width
    s= s1 & s2
    
    combined = s&f

    r[first[combined],second[combined],:]=image[i[combined],j[combined],:]

    r_interpolated = r.copy()
    u=[True]*output_height*output_width
    canvas=np.array(u).reshape(output_height,output_width)
    canvas[first[combined],second[combined]]=False
    converted_empty_index = np.where(canvas == True )
    converted_first = converted_empty_index[0]
    converted_second = converted_empty_index[1]

    new = converted_first.astype(complex)
    new.imag = converted_second

    ori = (d*new-b)/(-c*new+a)

    p=np.hstack([ori.real,ori.real,ori.real])
    k=np.hstack([ori.imag,ori.imag,ori.imag])
    zero=np.zeros_like(ori.real)
    one=np.ones_like(ori.real)
    two=np.ones_like(ori.real)*2
    third = np.hstack([zero,one,two])
    number_of_interpolated_point = len(one)
    e = number_of_interpolated_point
    interpolated_value_unfinished = map_coordinates(image, [p, k,third], order=1,mode=mode ,cval=0)
    t = interpolated_value_unfinished

    interpolated_value = np.stack([t[0:e],t[e:2*e],t[2*e:]]).T

    r_interpolated[converted_first,converted_second,:] = interpolated_value

    new_image=Image.fromarray(r_interpolated)
    uninterpolated_image=Image.fromarray(r)
    if not rgb:
        new_image = new_image.convert("L")
        return new_image, uninterpolated_image
    
    return new_image, uninterpolated_image

# Adapted from https://github.com/stanfordmlgroup/mobius
def getabcd_1fix(height, width, start_points, end_points):
     
    # fixed start and end points
    
    start1_x, start1_y, start2_x, start2_y, start3_x, start3_y = start_points
    end1_x, end1_y, end2_x, end2_y, end3_x, end3_y = end_points
    zp=[complex(start1_x,start1_y), complex(start2_x, start2_y), complex(start3_x, start3_y)]
    wa=[complex(end1_x, end1_y), complex(end2_x, end2_y),complex(end3_x, end3_y)]

    # This is for ploting points on the output, not useful for calculation
    original_points = np.array([[start1_x,start1_y], [start2_x, start2_y], [start3_x, start3_y]],dtype=int)
    new_points  = np.array([[end1_x, end1_y], [end2_x, end2_y],[end3_x, end3_y]],dtype=int)

    a = np.linalg.det([[zp[0]*wa[0], wa[0], 1], 
                    [zp[1]*wa[1], wa[1], 1], 
                    [zp[2]*wa[2], wa[2], 1]]);
    b = np.linalg.det([[zp[0]*wa[0], zp[0], wa[0]], 
                    [zp[1]*wa[1], zp[1], wa[1]], 
                    [zp[2]*wa[2], zp[2], wa[2]]]);  

    c = np.linalg.det([[zp[0], wa[0], 1], 
                    [zp[1], wa[1], 1], 
                    [zp[2], wa[2], 1]]);

    d = np.linalg.det([[zp[0]*wa[0], zp[0], 1], 
                    [zp[1]*wa[1], zp[1], 1], 
                    [zp[2]*wa[2], zp[2], 1]]);

    return a,b,c,d,original_points,new_points 

# Adapted from https://github.com/stanfordmlgroup/mobius
# Test if a, b, c, and d fit our criteria
def M_admissable(M, a,b,c,d):
    size = 32
    v1 = np.absolute(a) ** 2 / np.absolute(a*d - b*c)
    if not (v1 < M and v1 > 1/M):
        return False

    v2 = np.absolute(a-size*c) ** 2 / (np.absolute(a*d -b*c))
    if not (v2 < M and v2 > 1/M):
        return False

    v3 = np.absolute(complex(a,-size*c)) ** 2 / np.absolute(a*d-b*c)
    if not (v3 < M and v3 > 1/M):
        return False

    v4 = np.absolute(complex(a-size*c,-size*c)) ** 2 / np.absolute(a*d-b*c)
    if not (v4 < M and v4 > 1/M):
        return False
    
    v5 = np.absolute(complex(a-size/2*c,-size/2*c)) ** 2 / (np.absolute(a*d-b*c))
    if not (v5 < M and v5 > 1/M):
        return False

    v6 = np.absolute(complex(size/2*d-b,size/2*d)/complex(a-size/2*c,-size/2*c)-complex(size/2,size/2))
    if not( v6 < size/4):
        return False
    
    
    return  True

# Adapted from https://github.com/stanfordmlgroup/mobius
def madmissable_abcd(M,height,width):
    test=False 
    while test==False:
        # Zp are the start points (3 points)
        # Wa are the end points  (3 points)
        zp=[complex(height*random(),width*random()), complex(height*random(),width*random()),complex(height*random(),width*random())] 
        wa=[complex(height*random(),width*random()), complex(height*random(),width*random()),complex(height*random(),width*random())]

        # This is for ploting points on the output, not useful for calculation
        original_points = np.array([[real(zp[0]),imag(zp[0])],
                                  [real(zp[1]),imag(zp[1])],
                                  [real(zp[2]),imag(zp[2])]],dtype=int)
        new_points = np.array([[real(wa[0]),imag(wa[0])],
                                  [real(wa[1]),imag(wa[1])],
                                  [real(wa[2]),imag(wa[2])]],dtype=int)
        
        # transformation parameters
        a = linalg.det([[zp[0]*wa[0], wa[0], 1], 
                      [zp[1]*wa[1], wa[1], 1], 
                      [zp[2]*wa[2], wa[2], 1]]);

        b = linalg.det([[zp[0]*wa[0], zp[0], wa[0]], 
                      [zp[1]*wa[1], zp[1], wa[1]], 
                      [zp[2]*wa[2], zp[2], wa[2]]]);         


        c = linalg.det([[zp[0], wa[0], 1], 
                      [zp[1], wa[1], 1], 
                      [zp[2], wa[2], 1]]);

        d = linalg.det([[zp[0]*wa[0], zp[0], 1], 
                      [zp[1]*wa[1], zp[1], 1], 
                      [zp[2]*wa[2], zp[2], 1]]);
        test=M_admissable(M,a,b,c,d)
    
    return a, b, c, d, original_points, new_points

  
def create_training_data_k_means():

  tdata = []
  tlabel = []
  for img in os.listdir('labeled_data/10_1'):  # iterate over each image
      try:
          img_array = cv2.imread('labeled_data/10_1/{}'.format(img), cv2.IMREAD_GRAYSCALE) 
          tdata.append(cv2.resize(img_array, (200, 200)))
          tlabel.append(0)
      except Exception as e:  
          pass

  for img in os.listdir('labeled_data/10_2'):  # iterate over each image
      try:
          img_array = cv2.imread('labeled_data/10_2/{}'.format(img), cv2.IMREAD_GRAYSCALE) 
          tdata.append(cv2.resize(img_array, (200, 200)))
          tlabel.append(1)
      except Exception as e:  
          pass

  for img in os.listdir('labeled_data/10_3'):  # iterate over each image
      try:
          img_array = cv2.imread('labeled_data/10_3/{}'.format(img), cv2.IMREAD_GRAYSCALE) 
          tdata.append(cv2.resize(img_array, (200, 200)))
          tlabel.append(2)
      except Exception as e:  
          pass
  return tdata, tlabel

def reshape_and_normalize(X, Y, nb_classes):
  
  X = np.array(X).reshape(-1, 200, 200, 1) # Array containing every pixel as an index (1D array - 40,000 long)
  X_train = np.array(X)
  Y_train = np.array(Y)
  print ("The shape of X is " + str(X_train.shape))
  print ("The shape of y is " + str(Y_train.shape)) # This is only used to check our clustering

  # Data Normalization

  print(X_train.min()) # Should be 0
  print(X_train.max()) # Should be 255

  # Conversion to float

  X_train = X_train.astype('float32') 

  # Normalization

  X_train = X_train/255.0

  print(X_train.min()) # Should be 0
  print(X_train.max()) # Should be 1.0

  #check that X has been correctly split into train and test sets
  print('X_train shape:', X_train.shape)
  print(X_train.shape[0], 'train samples')

  # convert class vectors to binary class matrices with one-hot encoding

  Y_train = to_categorical(Y_train, nb_classes)
  return X_train, Y_train

def scree_plot(pca):


  import matplotlib.ticker as plticker

  xloc = plticker.MultipleLocator(base=1.0) # this locator puts ticks at regular intervals
  yloc = plticker.MultipleLocator(base=100000) # this locator puts ticks at regular intervals

  fig, ax = plt.subplots()
  PC_values = np.arange(pca.n_components_) + 1
  ax.plot(PC_values, pca.explained_variance_ratio_, color='red', linewidth=2.0)
  ax.xaxis.set_major_locator(xloc)
  ax.set_ylim(0,(round(max(pca.explained_variance_ratio_))))

  plt.xlabel('PC')
  plt.ylabel('Variance')
  plt.savefig(os.getcwd() + '/scree.png')

  print ("Proportion of Variance Explained : ", np.round(pca.explained_variance_ratio_, 2))  
      
  out_sum = np.cumsum(np.round(pca.explained_variance_ratio_, 2))
  print ("Cumulative Prop. Variance Explained: ", out_sum)

def fit_PCA(X_train, n_components):
    
  X = X_train.reshape(-1,X_train.shape[1]*X_train.shape[2]) 
  scaler = StandardScaler()

  pca = PCA(n_components)
  pca_fit = pca.fit(X) #fit the data according to our PCA instance

  print("Number of components before PCA  = " + str(X.shape[1]))
  print("Number of components after PCA 2 = " + str(pca.n_components_)) 
  
  #dimension reduced from 40000 to 2
  scores_pca = pca.transform(X)
  return pca, pca_fit, scores_pca

def elbow_plot(PCA_components):

  xloc = plticker.MultipleLocator(base=1.0) # this locator puts ticks at regular intervals
  yloc = plticker.MultipleLocator(base=100000) # this locator puts ticks at regular intervals

  wcss = []

  for i in range(1,11): 
    kmeans = KMeans(n_clusters=i, init ='k-means++', max_iter=300,  n_init=10, random_state=0 )
    kmeans.fit(PCA_components)
    wcss.append(kmeans.inertia_)

  fig, ax = plt.subplots()
  ax.plot(range(1,11),wcss, color= 'darkcyan', linewidth = 2.0)
  ax.xaxis.set_major_locator(xloc)
  ax.yaxis.set_major_locator(yloc)
  ax.set_ylim(0,(round(max(wcss), -5)))
  ax.set_xlabel('k')
  ax.set_ylabel('WCSS')
  ax.axes.ticklabel_format(axis='y', style='sci', scilimits=(0,0), useMathText=True)

  plt.savefig(os.getcwd() + '/elbow.png')

def fit_k_means(PCA_components, Y_train, number_of_clusters):

  kmeans = KMeans(n_clusters=number_of_clusters, init ='k-means++', max_iter=300, n_init=10,random_state=0)
  kmeans.fit(PCA_components)
  k_means_labels = kmeans.labels_ #List of labels of each dataset

  unique_labels = len(np.unique(k_means_labels)) 

  #2D matrix  for an array of indexes of the given label
  cluster_index= [[] for i in range(unique_labels)]
  for i, label in enumerate(k_means_labels,0):
      for n in range(unique_labels):

          if label == n:
              cluster_index[n].append(i)
          else:
              continue
  Y_clust = [[] for i in range(unique_labels)]
  for n in range(unique_labels):

      Y_clust[n] = Y_train[cluster_index[n]] #Y_clust[0] contains array of "correct" category from y_train for the cluster_index[0]
      assert(len(Y_clust[n]) == len(cluster_index[n])) #dimension confirmation


  for i in range(0, len(Y_clust)):
    for j in range(0, len(Y_clust[i])):
      if Y_clust[i][j][0] != 0.0:
        Y_clust[i][j][0] = 1.0
      elif Y_clust[i][j][1] != 0.0:
        Y_clust[i][j][1] = 2.0
      elif Y_clust[i][j][2] != 0.0:
        Y_clust[i][j][2] = 3.0
  return kmeans, k_means_labels, Y_clust, unique_labels
  
def counter(cluster):
    unique, counts = np.unique(cluster, return_counts=True)
    label_index = dict(zip(unique[1:4], counts[1:4]))
    return label_index

def plotter(label_dict, class_names):

    plt.bar(range(len(label_dict)), list(label_dict.values()), align='center', width=0.8, edgecolor='black', linewidth=1, color='darkgreen')
    a = []
    for i in [*label_dict]: a.append(class_names[i])
    plt.xticks(range(len(label_dict)), list(a), rotation=0, rotation_mode='anchor')
    plt.yticks()
    plt.xlabel('Sub-stage')
    plt.ylabel('Count')

def plot_counts(label_count):

  class_names = {1: '10.1', 2: '10.2', 3: '10.3'}
  #Bar graph with the number of items of different categories clustered in it
  plt.figure()
  plt.subplots_adjust(wspace = 0.8)
  mpl.rcParams['axes.linewidth'] = 2
  for i in range (1,4):
      plt.subplot(3, 3, i)
      plotter(label_count[i-1], class_names) 
      plt.title("Cluster " + str(i))
  plt.savefig(os.getcwd() + '/counts.png')

def plot_scatter(k_means_labels, kmeans, PCA_components):
  plt.clf()
  plt.figure()

  ax = sns.scatterplot(PCA_components[0], PCA_components[1], hue=k_means_labels, palette = ['orange', 'blue', 'green'])
  ax = sns.scatterplot(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], color= 'r', s = 100)

  ax.set_ylabel('PC 2', fontsize = 14)
  ax.set_xlabel('PC 1', fontsize = 14)

  plt.tick_params(axis='both',which='both', bottom=False, top = False, labelbottom=False, labelleft=False)
  plt.savefig(os.getcwd() + '/scatter.png')