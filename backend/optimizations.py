# 1. Usar inference optimizado de TensorFlow Lite con XNNPACK
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# 2. Configurar threads para CPU
tf.lite.Interpreter(
    model_path="app/advanced_model.tflite",
    num_threads=os.cpu_count()
)

# 3. Batch predictions para múltiples IPs
def batch_predict(ips):
    features_batch = [ip_to_features(ip) for ip in ips]
    # Procesar en lote
    return model.predict_on_batch(features_batch)

# 4. Usar numpy optimizado con BLAS
import numpy as np
np.show_config()  # Verificar que usa MKL/OpenBLAS
