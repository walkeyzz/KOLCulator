import streamlit as st
import bcrypt
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from TesAja3 import main as kolculator_main
import pandas as pd
import instaloader
import requests
import json

# Load the external CSS file
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Apply the CSS file
load_css("styles.css")

# Database setup
engine = create_engine('sqlite:///users.db')
Base = declarative_base()

st.markdown(
    """
    <style>
    /* Make the app fullscreen */
    /* Set the container width to 100% */
    .block-container {
        padding-left: 0rem;
        padding-right: 0rem;
        padding-top: 100px;
        padding-bottom: 0rem;
    }
    
    /* Hide Streamlit's default hamburger menu */
    .css-1fcdlh6 {
        display: none;
    }
    
    /* Hide Streamlit's default footer */
    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

class KOLData(Base):
    __tablename__ = 'kol_data'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    followers = Column(Integer)
    avg_views = Column(Float)
    avg_likes = Column(Float)
    avg_comments = Column(Float)
    engagement_rate = Column(Float)
    ratecard_price = Column(Float)
    deal_status = Column(String)
    status = Column(String)
    notes = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="kol_data")

User.kol_data = relationship("KOLData", order_by=KOLData.id, back_populates="user")

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session_db = Session()

def save_kol_data(kol_data):
    existing_user = session_db.query(KOLData).filter_by(username=kol_data.username).first()
    if existing_user:
        st.error("Username already exists.")
    else:
        session_db.add(kol_data)
        session_db.commit()
        st.success("KOL Data has been submitted successfully.")

def fetch_instagram_data(username):
    try:
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)
        
        followers = profile.followers
        total_likes = 0
        total_comments = 0
        total_views = 0
        num_posts = 0
        
        for post in profile.get_posts():
            total_likes += post.likes
            total_comments += post.comments
            if post.is_video:
                total_views += post.video_view_count
            else:
                total_views += post.likes  # Approximation for non-video posts
            num_posts += 1
        
        avg_likes = total_likes / num_posts if num_posts > 0 else 0
        avg_comments = total_comments / num_posts if num_posts > 0 else 0
        avg_views = total_views / num_posts if num_posts > 0 else 0
        engagement_rate = (avg_likes + avg_comments) / followers if followers > 0 else 0
        
        return {
            'followers': followers,
            'avg_views': avg_views,
            'avg_likes': avg_likes,
            'avg_comments': avg_comments,
            'engagement_rate': engagement_rate
        }
    except instaloader.exceptions.ProfileNotExistsException:
        st.error("Username not found.")
        return None

def fetch_user_json():
    json_file_path = 'user_login.json'
    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
        return data
    except FileNotFoundError:
        return {"error": "File not found"}

def update_kol_status(kol_username, new_status):
    kol_data = session_db.query(KOLData).filter_by(username=kol_username).first()
    if kol_data:
        kol_data.status = new_status
        session_db.commit()
        return True
    return False

def delete_kol_data_by_username(username):
    kol_data = session_db.query(KOLData).filter_by(username=username).first()
    if kol_data:
        session_db.delete(kol_data)
        session_db.commit()
        return True
    return False

def main():
    user_data = fetch_user_json()
    st.session_state.username = user_data["username"]

    menu = ["Home", "Input Data", "KOL Data", "Update Data", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("KOLCulator System")
        kolculator_main()
    
    elif choice == "Input Data":
        st.subheader("Input KOL Data")
        with st.form("kol_data_form", clear_on_submit=True):
            username = st.text_input("Instagram Username", key="input_username")
            ratecard = st.number_input("Ratecard Price", min_value=0.0, format="%.2f", key="input_ratecard")
            status = st.selectbox("Status", ["Open", "Process", "Skip"], key="input_status")
            notes = st.text_area("Notes", key="input_notes")

            if username:
                ig_data = fetch_instagram_data(username)
                if ig_data:
                    followers = ig_data['followers']
                    avg_views = ig_data['avg_views']
                    avg_likes = ig_data['avg_likes']
                    avg_comments = ig_data['avg_comments']
                    engagement_rate = ig_data['engagement_rate']

                    st.write(f"Followers: {followers}")
                    st.write(f"Average Views: {avg_views:.2f}")
                    st.write(f"Average Likes: {avg_likes:.2f}")
                    st.write(f"Average Comments: {avg_comments:.2f}")
                    st.write(f"Engagement Rate: {engagement_rate:.2%}")

                    cpm = (ratecard / avg_views) * 1000 if avg_views > 0 else None

                    if cpm is not None:
                        if cpm < 20000:  # Example logic
                            deal = "WORTH IT"
                        elif cpm < 40000:
                            deal = "OK"
                        else:
                            deal = "OVERPRICE"
                    else:
                        deal = "CPM Calculation Error"
                        
                    st.write(f"Deal Status: {deal}")

            submitted = st.form_submit_button("Submit")
            if submitted and ig_data:
                user_id = session_db.query(User).filter_by(username=st.session_state.username).first().id
                kol_data = KOLData(
                    username=username,
                    followers=followers,
                    avg_views=avg_views,
                    avg_likes=avg_likes,
                    avg_comments=avg_comments,
                    engagement_rate=engagement_rate,
                    ratecard_price=ratecard,
                    deal_status=deal,
                    status=status,
                    notes=notes,
                    user_id=user_id
                )
                save_kol_data(kol_data)
            elif submitted and not ig_data:
                st.error("Failed to fetch Instagram data. Please check the username.")

    elif choice == "KOL Data":
        user_id = session_db.query(User).filter_by(username=st.session_state.username).first().id
        kol_data_list = session_db.query(KOLData).filter_by(user_id=user_id).all()

        data = {
            'ID': [kol_data.id for kol_data in kol_data_list],
            'Username': [kol_data.username for kol_data in kol_data_list],
            'Followers': [kol_data.followers for kol_data in kol_data_list],
            'Average Views': [kol_data.avg_views for kol_data in kol_data_list],
            'Average Likes': [kol_data.avg_likes for kol_data in kol_data_list],
            'Average Comments': [kol_data.avg_comments for kol_data in kol_data_list],
            'Engagement Rate': [kol_data.engagement_rate for kol_data in kol_data_list],
            'Ratecard': [kol_data.ratecard_price for kol_data in kol_data_list],
            'Deal': [kol_data.deal_status for kol_data in kol_data_list],
            'Status': [kol_data.status for kol_data in kol_data_list],
            'Notes': [kol_data.notes for kol_data in kol_data_list],
        }

        df = pd.DataFrame(data)
        styled_df = df.style.hide(axis='index')

        st.subheader("Your KOL Data")
        st.write(styled_df.to_html(), unsafe_allow_html=True)

    elif choice == "Update Data":
        st.subheader("Update or Delete KOL Data by Username")
        kol_username = st.text_input("Enter the Username of the data to update or delete")
        new_status = st.selectbox("Update Status to", ["Open", "Process", "Skip"])
        
        if st.button("Update Status"):
            if update_kol_status(kol_username, new_status):
                st.success(f"Status of username {kol_username} has been updated to {new_status}.")
            else:
                st.error(f"No data found with username {kol_username}.")
        
        if st.button("Delete"):
            if delete_kol_data_by_username(kol_username):
                st.success(f"Data with username {kol_username} has been deleted successfully.")
            else:
                st.error(f"No data found with username {kol_username}.")

    elif choice == "Logout":
        st.write('<meta http-equiv="refresh" content="0; URL=\'http://localhost:5001/">', unsafe_allow_html=True)

if __name__ == '__main__':
    main()
