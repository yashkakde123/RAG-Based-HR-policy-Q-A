import requests
import firebase_admin
from firebase_admin import credentials, auth as admin_auth
import streamlit as st

class FirebaseAuthService:
    def __init__(self):
        # Initialize Firebase Admin SDK for backend security
        if not firebase_admin._apps:
            cred = credentials.Certificate("config/firebase_creds.json")
            firebase_admin.initialize_app(cred)
        
        # We only need the API Key to talk to the REST API
        self.api_key = st.secrets["firebase"]["apiKey"]

    def sign_in_user(self, email, password):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Use Admin SDK to verify the token is legitimate
            decoded_token = admin_auth.verify_id_token(data['idToken'])
            return {"success": True, "user_info": decoded_token, "idToken": data['idToken']}
            
        except requests.exceptions.HTTPError:
            return {"success": False, "error": "Invalid email or password. Please try again."}

    def sign_up_user(self, email, password):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return {"success": True, "msg": "User successfully registered!"}
            
        except requests.exceptions.HTTPError as e:
            error_message = response.json().get("error", {}).get("message", "Registration failed.")
            return {"success": False, "error": f"Registration failed: {error_message}"}
        
    def reset_password(self, email):
        """Sends a password reset email via Firebase REST API."""
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={self.api_key}"
        payload = {"requestType": "PASSWORD_RESET", "email": email}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return {"success": True, "msg": f"A password reset link has been sent to {email}."}
            
        except requests.exceptions.HTTPError:
            return {"success": False, "error": "Failed to send reset email. Make sure the email is registered."}