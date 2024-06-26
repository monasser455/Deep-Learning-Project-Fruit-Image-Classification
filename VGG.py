import os
from turtle import pd
import cv2
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tqdm import tqdm
from random import shuffle
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, BatchNormalization, MaxPooling2D, Flatten, Dense, Dropout
from tflearn.layers.core import input_data, dropout, fully_connected

from keras.callbacks import ReduceLROnPlateau
from sklearn.model_selection import train_test_split
import joblib # save model with joblib

IMAGE_SIZE = (150, 150)
BATCH_SIZE = 32
EPOCHS = 30
NUM_CLASSES = 5
# Data preprocessing and augmentation using LeNet-5 approach
train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    rotation_range=10,
    width_shift_range=0.1,
    height_shift_range=0.1,
    fill_mode='nearest',
    brightness_range=[0.5, 1.5],  # Adjust brightness
    channel_shift_range=50.0,  # Adjust channel intensity
    vertical_flip=True,  # Flip vertically
    featurewise_center=False,
    featurewise_std_normalization=False,
    zca_whitening=False
)


def create_train_data():
    original_count = 0
    augmented_count = 0
    training_data = []
    testing_data=[]
    for folders in tqdm(os.listdir('C:/Users/monasser/Desktop/nural_project/dataset/train')):
        num_of_folder = 'C:/Users/monasser/Desktop/nural_project/dataset/train' + "/" + str(folders)
        c=0
        for img in tqdm(os.listdir(num_of_folder)):
            c+=1
            original_count += 1  # Increment original count for each image
            path = os.path.join(num_of_folder, img)
            img_data = cv2.imread(path, 0)

            img_data = cv2.resize(img_data, (IMAGE_SIZE[0], IMAGE_SIZE[1]))
            img_data = img_data.reshape((1,) + img_data.shape + (1,))  # Reshape for augmentation

            if(c>1700):
                label = np.zeros(NUM_CLASSES)  # Create an array of zeros
                label[int(folders) - 1] = 1  # Set the appropriate index to 1
                testing_data.append([np.array(img_data), label])
                continue


            # Generate augmented images
            i = 0
            for batch in train_datagen.flow(img_data, batch_size=1):
                augmented_count += 1  # Increment augmented count for each augmentation
                image = batch[0].reshape(IMAGE_SIZE[0], IMAGE_SIZE[1])
                label = np.zeros(NUM_CLASSES)  # Create an array of zeros
                label[int(folders) - 1] = 1  # Set the appropriate index to 1
                training_data.append([np.array(image), label])
                i += 1
                if i >= 5:  # Number of augmented images per original image
                    break

    shuffle(training_data)
    shuffle(testing_data)
    print("Original data count:", original_count)
    print("len Augmented Train data count:", len(training_data))
    print("len Test data:",len(testing_data))
    joblib.dump(training_data, "new_training_data.npy")
    joblib.dump(testing_data, "new_testing_data.npy")
    return testing_data,training_data


from keras.models import load_model
import h5py


if (os.path.exists('new_training_data.npy') and os.path.exists('new_testing_data.npy') ): # If you have already created the dataset:
    train_data =joblib.load('new_training_data.npy')
    testdata =joblib.load('new_testing_data.npy')
else: # If dataset is not created:
    testdata,train_data = create_train_data()

# Splitting data into train and test sets
# train, test = train_test_split(train_data, test_size=0.15, random_state=42)

# Reshape and preprocess data for LeNet-5
X_train = np.array([i[0] for i in train_data]).reshape(-1, IMAGE_SIZE[0], IMAGE_SIZE[1], 1)
Y_train = np.array([i[1] for i in train_data])

X_test = np.array([i[0] for i in testdata]).reshape(-1, IMAGE_SIZE[0], IMAGE_SIZE[1], 1)
Y_test = np.array([i[1] for i in testdata])


VGG_model = Sequential([
    # block 1
    Conv2D(64, kernel_size=(3, 3), padding="same", activation="relu", input_shape=(IMAGE_SIZE[0], IMAGE_SIZE[1], 1)),
    Conv2D(64, kernel_size=(3, 3), padding="same", activation="relu"),
    MaxPooling2D((2, 2), strides=(2, 2)),
    # block 2
    Conv2D(128, kernel_size=(3, 3), padding="same", activation="relu"),
    Conv2D(128, kernel_size=(3, 3), padding="same", activation="relu"),
    MaxPooling2D((2, 2), strides=(2, 2)),
    # block 3
    Conv2D(256, kernel_size=(3, 3), padding="same", activation="relu"),
    Conv2D(256, kernel_size=(3, 3), padding="same", activation="relu"),
    Conv2D(256, kernel_size=(3, 3), padding="same", activation="relu"),
    MaxPooling2D((2, 2), strides=(2, 2)),
    # block 4
    Conv2D(512, kernel_size=(3, 3), padding="same", activation="relu"),
    Conv2D(512, kernel_size=(3, 3), padding="same", activation="relu"),
    Conv2D(512, kernel_size=(3, 3), padding="same", activation="relu"),
    MaxPooling2D((2, 2), strides=(2, 2)),
    # block 5
    Conv2D(512, kernel_size=(3, 3), padding="same", activation="relu"),
    Conv2D(512, kernel_size=(3, 3), padding="same", activation="relu"),
    Conv2D(512, kernel_size=(3, 3), padding="same", activation="relu"),
    MaxPooling2D((2, 2), strides=(2, 2)),
    # block 5 fully connected
    Flatten(),
    Dense(4096, activation='relu'),
    Dense(4096, activation='relu'),
    Dropout(rate=0.5),
    Dense(5, activation='softmax')

])

from keras.callbacks import LearningRateScheduler

def lr_schedule(epoch):
    lr = 0.001
    if epoch > 30:
        lr *= 0.5
    elif epoch > 20:
        lr *= 0.7
    return lr

reduce_lr = LearningRateScheduler(lr_schedule)

# Compile the model with a lower learning rate and categorical crossentropy loss
VGG_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print('Model Details are : ')
print(VGG_model.summary())

if (os.path.exists('C:/Users/monasser/PycharmProjects/pythonProject4/VGG_model.tfl')):
    VGG_model=joblib.load('VGG_model.tfl')
else:
    # reduce_lr = ReduceLROnPlateau(monitor='loss', factor=0.2, patience=5, min_lr=0.0001)
    ThisModel = VGG_model.fit(X_train, Y_train, batch_size=64,callbacks=[reduce_lr], validation_data=(X_test, Y_test),
                                epochs=5, verbose=1)
    joblib.dump(VGG_model, "VGG_model.tfl")


import csv

# opening the file
with open("47.csv", "w", newline="") as f:
    # creating the writer
    writer = csv.writer(f)
    # using writerow to write individual record one by one
    writer.writerow(["Image", "Label", "Index"])
    writer.writerow(["image_id", "label"])
    # Make predictions
    label = ["apple", "banana", "grapes", "mango", "stra"]
    for image in tqdm(os.listdir('C:/Users/monasser/Desktop/nural_project/dataset/test')):
        img = cv2.imread(os.path.join('C:/Users/monasser/Desktop/nural_project/dataset/test', image), 0)
        img_test = cv2.resize(img, (IMAGE_SIZE))
        img_test = img_test.reshape(1, IMAGE_SIZE[0],IMAGE_SIZE[1], 1)  # Reshape for model input
        prediction = VGG_model.predict(img_test)[0]
        max_index = np.argmax(prediction)

        print(image.split('.')[0], "  ", label[max_index])
        # writer.writerow([image.split('.')[0],  label[max_index], max_index+1])
        writer.writerow([image.split('.')[0], max_index+1])




