import os
import cv2
import numpy as np
from keras.applications import VGG16
from keras.layers import Dense, Dropout, Flatten
from keras.models import Sequential
from tensorflow import optimizers

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def dis(image_path):
    SIZE = 150
    conv_base = VGG16(weights='imagenet',
                      include_top=False,
                      input_shape=(SIZE, SIZE, 3))
    conv_base.trainable = False
    model = Sequential()
    model.add(conv_base)
    model.add(Flatten(input_shape=conv_base.output_shape[1:]))
    model.add(Dense(256, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(2, activation='softmax'))
    model.compile(optimizer=optimizers.Adam(lr=0.0005 / 100),
                  loss='mse',
                  metrics=['accuracy'])
    # model.summary()

    model.load_weights("model.hdf5")

    # path = r"D:\scu\Innovation\Classifier\chest_xray\test\pneumonia\*"
    # image_path = np.random.choice(glob.glob(path))
    # abs_path = os.path.join(r'D:\scu\Innovation\Classifier\chest_xray\test\pneumonia', image_path)
    # a = cv2.imread(abs_path)
    # cv2.imshow('pic', a)
    # cv2.waitKey()
    # cv2.destroyAllWindows()
    image = cv2.imread(image_path)
    image = cv2.resize(image, (150, 150))
    image = image[np.newaxis, :, :, :]
    a = np.round(model.predict(image)[:, 1][0])
    if a:
        return 1
    return 0


if __name__ == '__main__':
    res = dis()
    print(res)
