'''
- make each network more complex
V binary output
- cross validation
X increase size of images
- the other metrics
X try Marco's GAN
V extract nose and replace face with it
'''

import os
import sys
import random
from sklearn.metrics import roc_curve
from sklearn.metrics import auc

sys.path.append(os.getcwd())

from categorization.cnn import *
from categorization.stacking_model import *

def get_accuracy(test_labels, prediction_labels):
    sum_acc = 0.0
    for i in range(len(test_labels)):
        if (test_labels[i] == (prediction_labels[i] >= 0.5)):
            sum_acc += 1
    
    return sum_acc / len(test_labels)

if __name__ == "__main__":

    image_folder_sick = 'data/parsed/brightened/sick'
    image_folder_healthy = 'data/parsed/brightened/healthy'
    image_folder_val_sick = 'data/parsed/validation_sick'
    image_folder_val_healthy = 'data/parsed/validation_healthy'
    save_path = 'categorization/model_saves/'
    image_size = 128
    face_features = ["mouth", "nose", "skin", "eyes"]

    fpr_sum = 0
    tpr_sum = 0
    auc_sum = 0
    
    for i in range(10):
        print("Creating empty models...")
        for feature in face_features:
            print(feature + "...")
            model = make_model(image_size, feature)
            model.save(save_path + os.sep + feature + os.sep + "model.h5")

        print("Loading the stacked model...")

        all_models = load_all_models(save_path, face_features)

        test_faces, _ = load_data(
        'data/parsed/validation_sick', 'data/parsed/validation_healthy', image_size, "face")

        train_images, train_labels, cross_val_images, cross_val_labels, test_images, test_labels = make_training_sets(
            face_features, image_folder_sick, image_folder_healthy, image_folder_val_sick, image_folder_val_healthy, image_size)

        print(cross_val_labels)

        # for i in range(3):
        stacked = define_stacked_model(all_models, face_features)
        
        monitor = "val_accuracy"
        early_stopping = tf.keras.callbacks.EarlyStopping(monitor = monitor, mode = 'max', patience=10, verbose = 1)
        model_check = tf.keras.callbacks.ModelCheckpoint(save_path + 'stacked/model.h5', monitor=monitor, mode='max', verbose=1, save_best_only=True)
        
        print("Starting training...")

        history = stacked.fit(
            train_images, train_labels, epochs=50, batch_size=2, callbacks=[model_check, early_stopping],
            validation_data=(cross_val_images, cross_val_labels), verbose = 1)

        
        # save_history(save_path, history, "stacked")

        print("Loading model and making predictions...")
        stacked = tf.keras.models.load_model(save_path + 'stacked/model.h5')
            
            
        #  load best model as stacked to plot predictions


        pred = stacked.predict(test_images).ravel()
        
        fpr_keras, tpr_keras, thresholds_keras = roc_curve(test_labels, pred)
        auc_keras = auc(fpr_keras, tpr_keras)

        fpr_sum += fpr_keras
        tpr_sum += tpr_keras
        auc_sum += auc_keras
    
    fpr_sum /= 10
    tpr_sum /= 10
    auc_sum /= 10

    plt.figure()
    plt.plot([0, 1], [0, 1], 'k--')
    plt.plot(fpr_sum, tpr_sum, label='Stacked (area = {:.3f})'.format(auc_sum))
    plt.xlabel('False positive rate')
    plt.ylabel('True positive rate')
    plt.title('ROC curve averaged over 10 runs')
    plt.legend(loc='best')
    plt.savefig("data/plots/roc.png")

    # print("Accuracy: ", get_accuracy(test_labels, pred))
    # plt.figure(figsize=(10, 10))
    # for i in range(30):
    #     plt.subplot(6, 5, i+1)
    #     plt.xticks([])
    #     plt.yticks([])
    #     plt.grid(False)
    #     plt.imshow(test_images[1][i], cmap=plt.cm.binary)
    #     result = pred[i]
    #     real = test_labels[i]
    #     plt.xlabel("%d, real: %d" % (result, real))
    # plt.suptitle("Results " + feature + " model")
    # plt.savefig("data/plots/predictions" + i + ".png")