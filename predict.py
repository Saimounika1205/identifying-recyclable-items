import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

model = load_model("model.h5")

# ✅ PASTE YOUR ACTUAL CLASS ORDER HERE
classes = ['battery','biological','cardboard','clothes','glass','metal','paper','plastic','shoes','trash']

def is_recyclable(label):
    recyclable = ['glass','metal','paper','plastic','cardboard']
    return "Recyclable" if label in recyclable else "Non-Recyclable"

def predict(img_path):
    img = image.load_img(img_path, target_size=(224,224))
    img = image.img_to_array(img) / 255.0
    img = np.expand_dims(img, axis=0)

    pred = model.predict(img)
    
    class_index = np.argmax(pred)
    label = classes[class_index]

    confidence = float(np.max(pred)) * 100

    return label, is_recyclable(label), round(confidence, 2)