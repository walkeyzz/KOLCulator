import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

def load_and_prepare_data(file_path):
    # Memuat data CSV
    df = pd.read_csv(file_path, delimiter=';')
    df = df.drop(columns=['Unnamed: 14', 'Unnamed: 15'])

    # Menambahkan Engagement Rate jika belum ada di data CSV
    df['Engagement_Rate'] = (df['Avg_Likes'] + df['Avg_Comments']) / df['Followers']

    # Menghapus baris dengan nilai NaN
    df.dropna(inplace=True)

    # Memastikan semua kolom yang digunakan sebagai input adalah numerik
    df['Views_from_Collab'] = pd.to_numeric(df['Views_from_Collab'], errors='coerce')
    df['Likes_from_Collab'] = pd.to_numeric(df['Likes_from_Collab'], errors='coerce')
    df['Comments_from_Collab'] = pd.to_numeric(df['Comments_from_Collab'], errors='coerce')
    df['Share_from_Collab'] = pd.to_numeric(df['Share_from_Collab'], errors='coerce')
    df['CPM'] = pd.to_numeric(df['CPM'], errors='coerce')

    # Menambahkan penghapusan atau penggantian nilai NaN setelah konversi ke numerik
    df.dropna(inplace=True)
    
    return df

def train_model(X, y):
    # Membagi data menjadi set pelatihan dan pengujian
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Melatih model
    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Memprediksi rating pada data uji
    y_pred = model.predict(X_test).round().astype(int)
    
    # Menghitung error
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    print(f"Root Mean Squared Error (RMSE) dari model Gradient Boosting: {rmse}")

    return model, X_test, y_test

def test_model(model, X_full, y_full):
    # Memprediksi rating untuk seluruh dataset
    predicted_ratings = model.predict(X_full)
    
    # Membulatkan hasil prediksi
    predicted_ratings_rounded = predicted_ratings.round().astype(int)

    # Menghitung persentase kesamaan antara prediksi dan aktual
    correct_predictions = (predicted_ratings_rounded == y_full).sum()
    total_predictions = len(y_full)
    accuracy = (correct_predictions / total_predictions) * 100

    print(f"Accuracy: {accuracy:.2f}%")
    
    # Menampilkan hasil perbandingan antara rating aktual dan prediksi
    comparison_df = pd.DataFrame({'Actual Rating': y_full, 'Predicted Rating': predicted_ratings_rounded})
    comparison_df['Match'] = comparison_df['Actual Rating'] == comparison_df['Predicted Rating']

    # Visualisasi perbandingan akurasi
    plt.figure(figsize=(10, 6))
    comparison_df['Match'].value_counts().plot(kind='bar', color=['green', 'red'], alpha=0.7)
    plt.title('Accuracy of Model Predictions with Gradient Boosting')
    plt.xlabel('Prediction Correctness')
    plt.ylabel('Count')
    plt.xticks([0, 1], ['Correct', 'Incorrect'], rotation=0)
    plt.show()

def main():
    # Load and prepare data
    file_path = r"DataKOL.csv"
    df = load_and_prepare_data(file_path)
    
    # Memilih fitur dan label untuk seluruh data
    X_full = df[['Views_from_Collab', 'Likes_from_Collab', 'Comments_from_Collab', 'Share_from_Collab', 'CPM']]
    y_full = df['Rating']
    
    # Scale data
    scaler = StandardScaler()
    X_full_scaled = scaler.fit_transform(X_full)

    # Train model
    model, X_test, y_test = train_model(X_full_scaled, y_full)

    # Test model on full dataset
    test_model(model, X_full_scaled, y_full)

if __name__ == "__main__":
    main()
