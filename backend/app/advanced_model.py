import tensorflow as tf
import numpy as np
import ipaddress
from tensorflow.keras import layers, Model
import joblib

class IPEmbeddingLayer(layers.Layer):
    """Embedding personalizado para rangos IP"""
    def __init__(self, embedding_dim=16):
        super().__init__()
        self.embedding_dim = embedding_dim
        # 256 posibles primeros octetos
        self.embedding = tf.Variable(tf.random.normal([256, embedding_dim]), trainable=True)
    
    def call(self, ip_int):
        # ip_int es el primer octeto (0-255)
        return tf.nn.embedding_lookup(self.embedding, ip_int)

def create_advanced_model():
    """Modelo con embeddings de IP y features complejos"""
    
    # Entrada: primer octeto de la IP (para embedding)
    ip_input = layers.Input(shape=(1,), dtype=tf.int32, name='ip_octet')
    ip_embedding = IPEmbeddingLayer(embedding_dim=16)(ip_input)
    ip_embedding = layers.Flatten()(ip_embedding)
    
    # Entrada: features numéricas (abuse_score, total_reports, etc.)
    numeric_input = layers.Input(shape=(12,), name='numeric_features')
    
    # Entrada: features categóricas (tipo de ISP, país, etc.)
    categorical_input = layers.Input(shape=(8,), name='categorical_features')
    
    # Procesar numéricas
    x_numeric = layers.Dense(32, activation='relu')(numeric_input)
    x_numeric = layers.BatchNormalization()(x_numeric)
    x_numeric = layers.Dropout(0.3)(x_numeric)
    
    # Procesar categóricas
    x_cat = layers.Dense(16, activation='relu')(categorical_input)
    x_cat = layers.BatchNormalization()(x_cat)
    
    # Concatenar todo
    concatenated = layers.Concatenate()([ip_embedding, x_numeric, x_cat])
    
    # Capas densas
    x = layers.Dense(64, activation='relu')(concatenated)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(32, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(16, activation='relu')(x)
    
    # Salida (3 clases con atención)
    attention = layers.Dense(3, activation='softmax', name='class_output')(x)
    
    # Salida adicional (score de riesgo)
    risk_output = layers.Dense(1, activation='sigmoid', name='risk_output')(x)
    
    model = Model(inputs=[ip_input, numeric_input, categorical_input], 
                  outputs=[attention, risk_output])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss={'class_output': 'sparse_categorical_crossentropy', 'risk_output': 'mse'},
        loss_weights={'class_output': 1.0, 'risk_output': 0.5},
        metrics={'class_output': 'accuracy', 'risk_output': 'mae'}
    )
    
    return model

def ip_to_features(ip):
    """Convertir IP a features numéricas + categóricas"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        ip_int = int(ip_obj)
        
        # Primer octeto (0-255) para embedding
        first_octet = ip_int >> 24 & 0xFF
        
        # Features numéricas (12 features)
        numeric_features = np.array([
            first_octet / 255.0,  # normalized
            (ip_int & 0xFFFF) / 65535.0,  # últimos 2 octetos normalizados
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0  # placeholders, se llenan con datos reales
        ])
        
        # Features categóricas (8 features)
        categorical_features = np.zeros(8)
        
        # Clase de IP (A, B, C, D)
        if first_octet <= 127:
            categorical_features[0] = 1  # Clase A
        elif first_octet <= 191:
            categorical_features[1] = 1  # Clase B
        elif first_octet <= 223:
            categorical_features[2] = 1  # Clase C
        elif first_octet <= 239:
            categorical_features[3] = 1  # Clase D
        
        # Es IP privada
        categorical_features[4] = 1 if ip_obj.is_private else 0
        
        # Es multicast
        categorical_features[5] = 1 if ip_obj.is_multicast else 0
        
        # Es loopback
        categorical_features[6] = 1 if ip_obj.is_loopback else 0
        
        return first_octet, numeric_features, categorical_features
        
    except:
        return 0, np.zeros(12), np.zeros(8)

def train_advanced_model(dataset_size=10000):
    """Entrenar modelo avanzado con datos reales"""
    from database import SessionLocal, IPDataset
    
    session = SessionLocal()
    data = session.query(IPDataset).limit(dataset_size).all()
    
    if len(data) < 100:
        print(f"⚠️ Dataset pequeño ({len(data)}), construyendo más datos...")
        build_real_dataset()
        data = session.query(IPDataset).limit(dataset_size).all()
    
    X_ip_octets = []
    X_numeric = []
    X_categorical = []
    y_class = []
    y_risk = []
    
    for entry in data:
        first_octet, numeric_feat, categorical_feat = ip_to_features(entry.ip)
        
        # Combinar features guardadas con las extraídas
        stored_features = entry.features
        numeric_feat[2] = stored_features.get('abuse_score', 0) / 100.0
        numeric_feat[3] = min(stored_features.get('total_reports', 0) / 100.0, 1.0)
        numeric_feat[4] = stored_features.get('unique_categories', 0) / 10.0
        numeric_feat[5] = stored_features.get('has_recent_report', 0)
        numeric_feat[6] = stored_features.get('is_vpn', 0)
        numeric_feat[7] = stored_features.get('is_proxy', 0)
        numeric_feat[8] = stored_features.get('is_tor', 0)
        numeric_feat[9] = stored_features.get('is_datacenter', 0)
        
        X_ip_octets.append([first_octet])
        X_numeric.append(numeric_feat)
        X_categorical.append(categorical_feat)
        y_class.append(entry.label)
        y_risk.append(entry.abuse_count / 100.0)
    
    X_ip_octets = np.array(X_ip_octets, dtype=np.int32)
    X_numeric = np.array(X_numeric, dtype=np.float32)
    X_categorical = np.array(X_categorical, dtype=np.float32)
    y_class = np.array(y_class, dtype=np.int32)
    y_risk = np.array(y_risk, dtype=np.float32)
    
    # Dividir entrenamiento/validación
    split = int(0.8 * len(X_ip_octets))
    
    model = create_advanced_model()
    
    # Entrenar
    history = model.fit(
        [X_ip_octets[:split], X_numeric[:split], X_categorical[:split]],
        {'class_output': y_class[:split], 'risk_output': y_risk[:split]},
        validation_data=(
            [X_ip_octets[split:], X_numeric[split:], X_categorical[split:]],
            {'class_output': y_class[split:], 'risk_output': y_risk[split:]}
        ),
        epochs=30,
        batch_size=64,
        verbose=1
    )
    
    # Guardar modelo optimizado para CPU
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float32]
    converter.representative_dataset = lambda: [(
        np.expand_dims(X_ip_octets[:10], 0),
        np.expand_dims(X_numeric[:10], 0),
        np.expand_dims(X_categorical[:10], 0)
    )]
    
    tflite_model = converter.convert()
    with open('app/advanced_model.tflite', 'wb') as f:
        f.write(tflite_model)
    
    print(f"✅ Modelo avanzado entrenado. Precisión: {history.history['val_class_output_accuracy'][-1]:.2%}")
    return model
