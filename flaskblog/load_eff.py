import os
import cv2
import datetime
import shutil
import pandas as pd
import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow import optimizers
from tensorflow.keras import regularizers, initializers
from tensorflow.keras.applications import ResNet50, EfficientNetB0, EfficientNetB1, MobileNetV2, EfficientNetV2B0, \
    MobileNet, EfficientNetV2B2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, GlobalAveragePooling2D, Dropout, BatchNormalization

RegL = 0.0
SIZE = 750
EPOCHS = 100
DROPOUT_RATE = 0.55
INPUT_SHAPE = (SIZE, SIZE, 3)

conv_base = EfficientNetB0(input_shape=(SIZE, SIZE, 3), weights='imagenet', include_top=False)
model = Sequential()
model.add(conv_base)
model.add(GlobalAveragePooling2D())
model.add(Dense(1024, activation='relu', kernel_regularizer=regularizers.l2(RegL),
                kernel_initializer=initializers.TruncatedNormal(mean=0.0, stddev=0.05)
                ))
model.add(Dropout(DROPOUT_RATE))
model.add(Dense(128, activation='relu', kernel_regularizer=regularizers.l2(RegL),
                kernel_initializer=initializers.TruncatedNormal(mean=0.0, stddev=0.05)
                ))
model.add(Dropout(DROPOUT_RATE))
model.add(Dense(32, activation='relu', kernel_regularizer=regularizers.l2(RegL),
                kernel_initializer=initializers.TruncatedNormal(mean=0.0, stddev=0.05)
                ))
model.add(Dropout(DROPOUT_RATE))
model.add(Dense(1, activation='sigmoid'))
# model.compile(optimizer=optimizers.Adam(lr=LEARNING_RATE),
#               loss='binary_crossentropy', metrics=['mae']
#               )
model.load_weights("model.hdf5")

image_path = r"D:\scu\Innovation\new\png\283646.png"
image = cv2.imread(image_path)
image = cv2.resize(image, (SIZE, SIZE))
image = image[np.newaxis, :, :, :]
a = (model.predict(image) - 0.05) * 3.5
print(a[0, 0])

#
# def divide(y):
#     i, j, k = .45, 1.55, 2.45
#     if y < i:
#         x = 0
#     elif i <= y < j:
#         x = 1
#     elif j <= y < k:
#         x = 2
#     else:
#         x = 3
#     return x
#
#
# image_directory = 'D:/scu/Innovation/new/png/'
# images = os.listdir(image_directory)
# xlsx_dir = r"D:\scu\Innovation\new\test2.xlsx"
# dataset = []
# labels = []
# indexes = []
# df = pd.read_excel(xlsx_dir)
# df = df.set_index('胸片号')
# series = df['尘肺期别']
# for i, image_name in enumerate(images):
#     if image_name.split('.')[1] == 'png':
#         image = cv2.imread(image_directory + image_name, 1)
#         image = cv2.resize(image, (SIZE, SIZE))
#
#         # 对于完整胸片
#         index = int(image_name.split('.')[0])
#         label = series[index]
#
#         # 公共
#         dataset.append(np.array(image))
#         # a = datagen.flow(image[np.newaxis, :, :, :])
#         # for i in range(2):
#         # dataset.append(np.squeeze(next(a)))
#         labels.append(label)
#         indexes.append(index)
# dataset = np.array(dataset)
# labels = np.array(labels)
# pred = map(divide, (np.squeeze(model.predict(dataset)) - 0.05) * 3.5)
