import os
import cv2
import datetime
import shutil

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
model.load_weights("model2.hdf5")

image_path = r"D:\scu\Innovation\new\png\273684.png"
image = cv2.imread(image_path)
image = cv2.resize(image, (SIZE, SIZE))
image = image[np.newaxis, :, :, :]
a = model.predict(image)
print(a[0, 0])
