import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
import matplotlib
from PIL import Image
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from skimage.io import imread
from skimage.transform import resize
from sklearn.utils import resample
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, f1_score, classification_report
from sklearn.preprocessing import OneHotEncoder
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.utils import to_categorical, plot_model
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.preprocessing.image import img_to_array, array_to_img
from tensorflow.keras.models import save_model
import argparse


def print_custom_metrics(y_true, y_pred, classes):
    for i, class_name in enumerate(classes):
        sensitivity = recall_score(y_true, y_pred, labels=[i], average='weighted')
        ppv = precision_score(y_true, y_pred, labels=[i], average='weighted')

        print(f"\n{class_name.capitalize()}:")
        print(f"Sensitivity (Recall): {sensitivity:.3f}")
        print(f"PPV (Precision): {ppv:.3f}")


classes = ["other", "chair"]  # 0=other, 1=chair



from sklearn.metrics import confusion_matrix
import numpy as np

def calculate_mcc(y_true, y_pred):
    if np.issubdtype(y_pred.dtype, np.floating):
        y_pred = (y_pred > 0.5).astype(int)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    numerator = (tp * tn) - (fp * fn)
    denominator = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    
    if denominator == 0:
        return 0.0  
    else:
        return numerator / denominator


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=str,
        required=True
    )
    args = parser.parse_args()

    base_dir = '/path_to_dataset'
    dataset_path = os.path.join(base_dir, args.dataset)
    train_image_dir = os.path.join(dataset_path, "train")
    test_image_dir = os.path.join(dataset_path, "test")

    def count_images_in_directory(directory_path):
        count = 0
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
                    count += 1
        return count

    train_path = os.path.join(dataset_path, 'train')
    test_path = os.path.join(dataset_path, 'test')

    train_count = count_images_in_directory(train_path)
    test_count = count_images_in_directory(test_path)
    total_count = train_count + test_count


    def display_image_from_row(row):
        image_data = row['Image_Data']
        label = row['Labels']
        plt.title(f"Label: {label}")
        plt.axis('off')


    def to_rgb(image):
        if len(image.shape) == 2:
            return np.stack((image,) * 3, axis=-1)
        return image


    filepaths = []
    images = []
    labels = []

    folds = os.listdir(train_image_dir)
    for fold in folds:
        foldpath = os.path.join(train_image_dir, fold)
        filelist = os.listdir(foldpath)
        for file in filelist:
            fpath = os.path.join(foldpath, file)
            image_data = np.array(Image.open(fpath))
            image_data = to_rgb(image_data)
            images.append(image_data/255.0)
            labels.append(fold)

    ImageSeries = pd.Series(images, name='Image_Data')
    LabelSeries = pd.Series(labels, name='Labels')
    data_train = pd.concat([ImageSeries, LabelSeries], axis=1)
    data_train = data_train.sample(frac=1).reset_index(drop=True)


    filepaths = []
    images = []
    labels = []

    folds = os.listdir(test_image_dir)
    for fold in folds:
        foldpath = os.path.join(test_image_dir, fold)
        filelist = os.listdir(foldpath)
        for file in filelist:
            fpath = os.path.join(foldpath, file)
            image_data = np.array(Image.open(fpath))
            image_data = to_rgb(image_data)
            images.append(image_data/255.0)
            labels.append(fold)

    ImageSeries = pd.Series(images, name='Image_Data')
    LabelSeries = pd.Series(labels, name='Labels')
    data_test = pd.concat([ImageSeries, LabelSeries], axis=1)
    data_test = data_test.sample(frac=1).reset_index(drop=True)
    data_train


    train_data, validation_data = train_test_split(data_train, test_size=0.20, random_state=42)


    counts = train_data.Labels.value_counts()


    labels = train_data['Labels']


    label_to_index = {label: index for index, label in enumerate(np.unique(labels))}
    train_data['Label_Index'] = train_data['Labels'].map(label_to_index)

    class_sample_count = train_data['Label_Index'].value_counts().to_dict()
    max_samples = max(class_sample_count.values())

    datagen = ImageDataGenerator(
        rotation_range=40,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0,
        horizontal_flip=True,
        fill_mode='nearest'
    )

    x = 2
    def augment_image(image_array, num_required):
        global x
        if image_array.max() <= 1:
            image_array = (image_array * 255).astype(np.uint8)

        image_array = image_array.astype(np.float32) / 255.0

        if x <=2:
            pass


        image = np.expand_dims(image_array, 0)
        aug_iter = datagen.flow(image)
        aug_images = []

        for i in range(num_required):
            aug_image = next(aug_iter)[0]
            aug_image = (aug_image * 255).astype(np.uint8)
            aug_images.append(aug_image)

            if x <=2:
              x += 1
        return aug_images


    samples_to_add_per_class = {label: max_samples - count for label, count in class_sample_count.items()}

    balanced_data = []
    for label, num_required in samples_to_add_per_class.items():
        class_samples = train_data[train_data['Label_Index'] == label]['Image_Data'].sample(n=num_required, replace=True)
        for image_array in class_samples:
            augmented_images = augment_image(image_array, 1)
            for img in augmented_images:
                balanced_data.append({'Image_Data': img, 'Labels': label})

    augmented_df = pd.DataFrame(balanced_data)
    augmented_df['Labels'] = augmented_df['Labels'].map({v: k for k, v in label_to_index.items()})

    balanced_train_data = pd.concat([train_data.drop('Label_Index', axis=1), augmented_df])

    counts = balanced_train_data['Labels'].value_counts()


    X_train = []
    for idx in range(len(train_data)):
        image_data = train_data.iloc[idx]['Image_Data']
        X_train.append(image_data)

    X_train = [to_rgb(img) for img in X_train]
    X_train = np.array(X_train)
    y_train = np.array(train_data['Labels'].tolist())


    X_train_balanced = []
    for idx in range(len(balanced_train_data)):
        image_data = balanced_train_data.iloc[idx]['Image_Data']
        X_train_balanced.append(image_data)

    X_train_balanced = [to_rgb(img) for img in X_train_balanced]
    X_train_balanced = np.array(X_train_balanced)
    y_train_balanced = np.array(balanced_train_data['Labels'].tolist())

    X_val = []
    for idx in range(len(validation_data)):
        image_data = validation_data.iloc[idx]['Image_Data']
        X_val.append(image_data)

    X_val = [to_rgb(img) for img in X_val]
    X_val = np.array(X_val)
    y_val = np.array(validation_data['Labels'].tolist())

    X_test = []
    for idx in range(len(data_test)):
        image_data = data_test.iloc[idx]['Image_Data']
        X_test.append(image_data)
    X_test = [to_rgb(img) for img in X_test]
    X_test = np.array(X_test)
    y_test = np.array(data_test['Labels'].tolist())

    # (1=chair, 0=other)
    y_train_encoded = (y_train_balanced == "chair").astype(int) 
    y_val_encoded = (y_val == "chair").astype(int)
    y_test_encoded = (y_test == "chair").astype(int)

    from tensorflow.keras import layers, models, optimizers
    from tensorflow.keras.utils import to_categorical
    from tensorflow.keras.applications import InceptionV3
    from tensorflow.keras.applications.inception_v3 import preprocess_input

    inception_model = InceptionV3(weights='imagenet', include_top=False, input_shape=(299, 299, 3))

    for layer in inception_model.layers:
        layer.trainable = False

    X_train_resized = np.array([img_to_array(array_to_img(img).resize((299, 299))) for img in X_train_balanced])
    X_val_resized = np.array([img_to_array(array_to_img(img).resize((299, 299))) for img in X_val])
    X_test_resized = np.array([img_to_array(array_to_img(img).resize((299, 299))) for img in X_test])

    X_train_resized = preprocess_input(X_train_resized)
    X_val_resized = preprocess_input(X_val_resized)
    X_test_resized = preprocess_input(X_test_resized)


    def create_inception_model(input_shape, num_classes):
        model = models.Sequential()
        model.add(inception_model)
        model.add(layers.GlobalAveragePooling2D())
        model.add(layers.Dense(1000, activation='relu'))
        model.add(layers.Dropout(0.5))
        model.add(layers.Dense(1, activation='sigmoid')) 
        return model

    input_shape_inception = (299, 299, 3)
    num_classes_inception = 1 
    inception_model_instance = create_inception_model(input_shape_inception, num_classes_inception)


    #Save env
    import pickle
    with open('prepare_env.pkl', 'wb') as f:
        pickle.dump({
            'model': inception_model_instance,
            'X_train': X_train_resized,
            'y_train': y_train_encoded,
            'X_val': X_val_resized,
            'y_val': y_val_encoded,
            'X_test': X_test_resized,
            'y_test': y_test_encoded,
            'classes': classes
        }, f)


