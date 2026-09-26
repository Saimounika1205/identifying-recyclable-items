import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models

IMG_SIZE = 224
BATCH_SIZE = 32

datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2,
    rotation_range=20,
    zoom_range=0.2,
    horizontal_flip=True
)

train = datagen.flow_from_directory(
    'dataset/train',
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training'
)

val = datagen.flow_from_directory(
    'dataset/train',
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation'
)

print("Class Indices:", train.class_indices)

# 🔥 Use MobileNet (faster than EfficientNet)
base = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224,224,3))

# STEP 1: Freeze base
base.trainable = False

x = base.output
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dense(128, activation='relu')(x)
out = layers.Dense(train.num_classes, activation='softmax')(x)

model = models.Model(inputs=base.input, outputs=out)

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print("🚀 STEP 1 TRAINING...")
model.fit(train, validation_data=val, epochs=5)

# STEP 2: Fine-tune last layers
print("🚀 STEP 2 FINE-TUNING...")

base.trainable = True

for layer in base.layers[:-20]:
    layer.trainable = False

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

model.fit(train, validation_data=val, epochs=3)

# Save model
model.save("model.h5")