import streamlit as st
import pandas as pd
import instaloader
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
from PIL import Image
import requests
from io import BytesIO

# Load the external CSS file
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Apply the CSS file
load_css("styles.css")


def main():
    # Fungsi untuk mendapatkan data Instagram menggunakan Instaloader
    def get_instagram_data(username):
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)
        
        total_likes = 0
        total_comments = 0
        total_views = 0
        num_posts = 0
        views_last_3 = []
        likes_last_3 = []
        comments_last_3 = []
        post_times = []  # Menyimpan waktu posting untuk analisis waktu aktif
        
        for post in profile.get_posts():
            total_likes += post.likes
            total_comments += post.comments
            if post.is_video:
                total_views += post.video_view_count
            else:
                total_views += post.likes  # Approximation for non-video posts
            num_posts += 1
            
            # Simpan waktu posting dalam format jam
            post_times.append(post.date_local.hour)
            
            # Save the views, likes, and comments of the last 3 posts
            if len(views_last_3) < 3:
                views_last_3.append(post.video_view_count if post.is_video else post.likes)
                likes_last_3.append(post.likes)
                comments_last_3.append(post.comments)
        
        if num_posts == 0:
            return None
        
        avg_likes = total_likes / num_posts
        avg_comments = total_comments / num_posts
        avg_views = total_views / num_posts
        followers = profile.followers
        engagement_rate = (avg_likes + avg_comments) / followers if followers > 0 else 0
        
        profile_pic = profile.profile_pic_url  # Fetch the profile picture URL
        
        return avg_views, avg_likes, avg_comments, followers, engagement_rate, profile_pic, views_last_3, likes_last_3, comments_last_3, post_times

    def format_followers(followers):
        if followers >= 1_000_000:
            return f"{followers/1_000_000:.1f}M"
        elif followers >= 1_000:
            return f"{followers/1_000:.1f}K"
        else:
            return str(followers)

    # Memuat data CSV
    df = pd.read_csv(r"DataKOL.csv", delimiter=';')
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

    # Memilih fitur dan label
    X = df[['Views_from_Collab', 'Likes_from_Collab', 'Comments_from_Collab', 'Share_from_Collab', 'CPM']]
    y = df['Rating']

    # Normalisasi data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Membagi data menjadi set pelatihan dan pengujian
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.1, random_state=42)

    # Melatih model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Memprediksi rating pada data uji
    y_pred = model.predict(X_test)

    # Menghitung error
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5

    # Aplikasi Streamlit untuk prediksi harga KOL

    # Input dari user (username Instagram)
    username = st.text_input("Masukkan Username Instagram KOL", key="username_input")

    if st.button("Dapatkan Data dan Prediksi Harga"):
        if username:
            # Mengambil data Instagram menggunakan Instaloader
            instagram_data = get_instagram_data(username)
            
            if instagram_data:
                avg_views, avg_likes, avg_comments, followers, engagement_rate, profile_pic, views_last_3, likes_last_3, comments_last_3, post_times = instagram_data
                
                # Download and display the profile picture using PIL
                response = requests.get(profile_pic)
                img = Image.open(BytesIO(response.content))
                st.image(img, caption=f"Profile picture of @{username}", use_column_width=True)

                # Style the output using HTML and CSS
                formatted_followers = format_followers(followers)
                st.markdown(f"""
                    <div style="background-color:#4C3A51;padding:10px;border-radius:10px;">
                        <h2 style="color:white;text-align:center;">{formatted_followers} Followers</h2>
                    </div>
                    <div style="text-align:center;">
                        <h3>@{username}</h3>
                        <h2 style="color:#FB8500;">{engagement_rate*100:.2f}%</h2>
                        <p>Engagement Rate</p>
                    </div>
                    <div style="background-color:#4C3A51;padding:10px;border-radius:10px;">
                        <h4 style="color:white;text-align:center;">Average Interactions per Post</h4>
                        <p style="color:white;text-align:center;">{avg_views:,.0f} views <br> {avg_likes:,.0f} likes <br> {avg_comments:,.0f} comments</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Menormalkan input pengguna
                user_input = [[avg_views, avg_likes, avg_comments, followers, engagement_rate]]
                user_input_scaled = scaler.transform(user_input)
                
                # Memasukkan data ke model untuk prediksi Rating
                predicted_rating = model.predict(user_input_scaled)[0]
                
                # Menghitung harga berdasarkan Rating dan mengalikan dengan 1000
                cpm = 15000  # Sebagai contoh, CPM adalah Cost Per 1000 views
                predicted_price = (avg_views / 1000) * cpm * predicted_rating 
                
                # Menentukan rentang harga (misalnya +/- 20%)
                min_price = predicted_price * 0.8
                max_price = predicted_price * 1.2
                
                st.subheader("Prediksi Harga untuk KOL")
                st.write(f"Prediksi rentang harga yang sesuai: Rp {min_price:,.2f} - Rp {max_price:,.2f}")
                
                # Plot grafik engagement rate
                plot_engagement_rate(engagement_rate, followers)
                
                # Plot grafik views, likes, and comments for the last 3 posts
                plot_last_3_metrics(views_last_3, likes_last_3, comments_last_3)

                # Plot grafik most active time of followers
                plot_most_active_time(post_times)
                
            else:
                st.error("Tidak dapat mengambil data dari Instagram. Periksa username atau akun mungkin bersifat pribadi.")
        else:
            st.error("Mohon masukkan username Instagram KOL.")

def plot_engagement_rate(engagement_rate, followers):
    # Data engagement rate berdasarkan jumlah followers
    avg_engagement_rates = {
        '1K - 5K': 6.08,
        '5K - 20K': 4.8,
        '20K - 100K': 5.1,
        '100K - 1M': 3.78,
        'Over 1M': 2.66
    }
    
    # Menentukan kategori followers
    if followers >= 1_000_000:
        category = 'Over 1M'
    elif 100_000 <= followers < 1_000_000:
        category = '100K - 1M'
    elif 20_000 <= followers < 100_000:
        category = '20K - 100K'
    elif 5_000 <= followers < 20_000:
        category = '5K - 20K'
    else:
        category = '1K - 5K'
    
    # Plotting grafik base
    categories = list(avg_engagement_rates.keys())
    values = list(avg_engagement_rates.values())
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(categories, values, color='#4C3A51', label='Average Engagement Rate')
    
    # Menambahkan engagement rate KOL ke grafik
    kol_index = categories.index(category)
    plt.bar(categories[kol_index], engagement_rate * 100, color='#FB8500', label=f'{category} KOL Engagement Rate')
    
    # Menampilkan nilai persentase pada grafik
    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 0.5, f'{bar.get_height():.2f}%', ha='center', color='white')
    
    plt.text(bars[kol_index].get_x() + bars[kol_index].get_width() / 2, engagement_rate * 100 + 0.1, f'{engagement_rate * 100:.2f}%', ha='center', color='black', fontweight='bold')
    
    plt.xlabel('No. of Followers')
    plt.ylabel('Average Engagement Rate (%)')
    plt.title('Average Engagement Rates on Instagram')
    plt.legend()
    st.pyplot(plt)

def plot_last_3_metrics(views, likes, comments):
    posts = ['Post 1', 'Post 2', 'Post 3']
    
    # Plotting views
    plt.figure(figsize=(10, 4))
    plt.plot(posts, views, marker='o', linestyle='-', color='blue')
    plt.title('Views for Last 3 Posts')
    plt.xlabel('Posts')
    plt.ylabel('Views')
    plt.grid(True)
    st.pyplot(plt)

    # Plotting likes
    plt.figure(figsize=(10, 4))
    plt.plot(posts, likes, marker='o', linestyle='-', color='green')
    plt.title('Likes for Last 3 Posts')
    plt.xlabel('Posts')
    plt.ylabel('Likes')
    plt.grid(True)
    st.pyplot(plt)

    # Plotting comments
    plt.figure(figsize=(10, 4))
    plt.plot(posts, comments, marker='o', linestyle='-', color='red')
    plt.title('Comments for Last 3 Posts')
    plt.xlabel('Posts')
    plt.ylabel('Comments')
    plt.grid(True)
    st.pyplot(plt)

def plot_most_active_time(post_times):
    # Hitung frekuensi postingan berdasarkan jam
    post_hours = [0] * 8  # Array untuk menyimpan jumlah postingan di setiap 3 jam
    
    for hour in post_times:
        post_hours[hour // 3] += 1  # Menambah jumlah postingan di interval 3 jam tertentu
    
    if sum(post_hours) == 0:
        st.write("No posts available to analyze.")
        return
    
    # Plot the histogram
    plt.figure(figsize=(10, 5))
    intervals = ['12-3am', '3-6am', '6-9am', '9am-12pm', '12-3pm', '3-6pm', '6-9pm', '9pm-12am']
    plt.bar(intervals, post_hours, color='orange', alpha=0.7)
    plt.xlabel('Time Interval')
    plt.ylabel('Number of Posts')
    plt.title('Total Number of Posts by 3-Hour Interval')
    st.pyplot(plt)
            
if __name__ == '__main__':
    main()
