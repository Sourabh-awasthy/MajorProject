import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.utils import to_categorical

# -----------------------------
# 1. Generate Synthetic Dataset
# -----------------------------
np.random.seed(42)

# Define possible crops
crops = ['Wheat', 'Rice', 'Maize', 'Cotton', 'Sugarcane', 'Soybean']

# Generate 500 random samples
n_samples = 500
data = {
    'N': np.random.randint(50, 150, n_samples),             # Nitrogen content
    'K': np.random.randint(20, 80, n_samples),              # Potassium
    'pH': np.random.uniform(5.5, 8.0, n_samples),           # pH value
    'moisture': np.random.uniform(20, 45, n_samples),       # Moisture percentage
    'temperature': np.random.uniform(18, 35, n_samples),    # Temperature °C
    'crop': np.random.choice(crops, n_samples)              # Random crop
}

df = pd.DataFrame(data)
df.to_csv('crop_data.csv', index=False)
print("✅ Synthetic dataset 'crop_data.csv' generated!\n")

# -----------------------------
# 2. Load and Prepare Data
# -----------------------------
data = pd.read_csv("crop_data.csv")

X = data[['N', 'K', 'pH', 'moisture', 'temperature']].values
y = data['crop'].values

# Encode crop labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
y_categorical = to_categorical(y_encoded)

# Normalize input features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_categorical, test_size=0.2, random_state=42)

# -----------------------------
# 3. Build the Deep Learning Model
# -----------------------------
model = Sequential([
    Dense(64, input_dim=X_train.shape[1], activation='relu'),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dense(y_categorical.shape[1], activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# -----------------------------
# 4. Train the Model
# -----------------------------
history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=50,
    batch_size=16,
    verbose=1
)

# -----------------------------
# 5. Evaluate Model
# -----------------------------
loss, acc = model.evaluate(X_test, y_test)
print(f"\n📊 Test Accuracy: {acc*100:.2f}%")

# -----------------------------
# 6. Predict for New Soil Data
# -----------------------------
new_data = np.array([[90, 40, 6.8, 35, 27]])  # Example soil parameters
new_data_scaled = scaler.transform(new_data)

pred = model.predict(new_data_scaled)
predicted_crop = label_encoder.inverse_transform([np.argmax(pred)])
print(f"\n🌾 Recommended Crop: {predicted_crop[0]}")

