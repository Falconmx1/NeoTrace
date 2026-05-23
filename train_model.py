import tensorflow as tf
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# 1. Generar dataset sintético realista (luego lo reemplazas con datos reales)
np.random.seed(42)
n_samples = 10000

def generate_synthetic_data():
    # IPs normales (60%)
    normal = np.random.randn(int(n_samples*0.6), 6) * 0.5
    normal[:, 0] = np.random.uniform(0, 23, int(n_samples*0.6))  # hora
    normal[:, 1:3] = 0  # no VPN ni proxy
    normal[:, 3] = np.random.poisson(1, int(n_samples*0.6))  # países vistos
    normal[:, 4] = np.random.poisson(0.5, int(n_samples*0.6))  # puertos
    normal[:, 5] = np.random.poisson(0.2, int(n_samples*0.6))  # reports
    
    # Sospechosas (30%)
    sospechoso = np.random.randn(int(n_samples*0.3), 6) * 0.8
    sospechoso[:, 0] = np.random.uniform(0, 23, int(n_samples*0.3))
    sospechoso[:, 1] = np.random.choice([0,1], int(n_samples*0.3), p=[0.3,0.7])  # 70% VPN
    sospechoso[:, 2] = np.random.choice([0,1], int(n_samples*0.3), p=[0.5,0.5])  # 50% proxy
    sospechoso[:, 3] = np.random.poisson(3, int(n_samples*0.3))
    sospechoso[:, 4] = np.random.poisson(2, int(n_samples*0.3))
    sospechoso[:, 5] = np.random.poisson(1.5, int(n_samples*0.3))
    
    # Maliciosas (10%)
    malicioso = np.random.randn(int(n_samples*0.1), 6) * 1.2
    malicioso[:, 0] = np.random.uniform(0, 23, int(n_samples*0.1))
    malicioso[:, 1] = np.random.choice([0,1], int(n_samples*0.1), p=[0.1,0.9])
    malicioso[:, 2] = np.random.choice([0,1], int(n_samples*0.1), p=[0.2,0.8])
    malicioso[:, 3] = np.random.poisson(5, int(n_samples*0.1))
    malicioso[:, 4] = np.random.poisson(4, int(n_samples*0.1))
    malicioso[:, 5] = np.random.poisson(3, int(n_samples*0.1))
    
    X = np.vstack([normal, sospechoso, malicioso])
    y = np.array([0]*int(n_samples*0.6) + [1]*int(n_samples*0.3) + [2]*int(n_samples*0.1))
    
    # Normalizar features
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    return X, y, scaler

X, y, scaler = generate_synthetic_data()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 2. Construir modelo TensorFlow
model = tf.keras.Sequential([
    tf.keras.layers.Dense(32, activation='relu', input_shape=(6,)),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(3, activation='softmax')  # 3 clases
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 3. Entrenar
history = model.fit(X_train, y_train, epochs=50, batch_size=32, 
                    validation_data=(X_test, y_test), verbose=1)

# 4. Convertir a TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Guardar modelo y scaler
with open('backend/app/ip_classifier.tflite', 'wb') as f:
    f.write(tflite_model)

import joblib
joblib.dump(scaler, 'backend/app/scaler.pkl')

print("✅ Modelo entrenado y convertido a TF Lite")
print(f"Precisión: {model.evaluate(X_test, y_test)[1]:.2%}")
