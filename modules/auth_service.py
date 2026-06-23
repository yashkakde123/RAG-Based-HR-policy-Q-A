import os
import json
import hashlib

class LocalAuthService:
    def __init__(self, filepath="config/users.json"):
        self.filepath = filepath
        # Ensure the config directory exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        # Initialize JSON database file if it doesn't exist yet
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                json.dump({}, f)

    def _hash_password(self, password):
        """SHA-256 hashing to satisfy REQ-07 Security Standards."""
        return hashlib.sha256(password.encode()).hexdigest()

    def sign_in_user(self, email, password):
        # 1. Check Hardcoded Super-Admin first (Emergency Access)
        if email == "admin@cdac.in" and password == "admin123":
            return {"success": True, "user_info": {"email": email, "role": "admin"}}
        
        # 2. Check Local Offline JSON Database
        try:
            with open(self.filepath, "r") as f:
                users = json.load(f)
            
            hashed_pass = self._hash_password(password)
            if email in users and users[email]["password"] == hashed_pass:
                return {"success": True, "user_info": {"email": email, "role": users[email]["role"]}}
            
            return {"success": False, "error": "Invalid email or password."}
        except Exception as e:
            return {"success": False, "error": f"Local Directory Error: {str(e)}"}

    def sign_up_user(self, email, password, invite_code):
        # Enforce strict invitation validation (Fixes the dummy email loophole!)
        if invite_code != "CDAC_GATE_2026":
            return {"success": False, "error": "Invalid Corporate Invitation Passcode. Registration denied."}

        # Enforce corporate domain segregation (REQ-07)
        if not email.endswith("@cdac.in"):
            return {"success": False, "error": "Only CDAC corporate domains (@cdac.in) are permitted."}
        
        try:
            with open(self.filepath, "r") as f:
                users = json.load(f)
            
            if email in users or email == "admin@cdac.in":
                return {"success": False, "error": "This email address is already registered."}
            
            # Secure password hashing
            users[email] = {
                "password": self._hash_password(password),
                "role": "user"
            }
            
            with open(self.filepath, "w") as f:
                json.dump(users, f, indent=4)
                
            return {"success": True, "msg": "User successfully registered in local database!"}
        except Exception as e:
            return {"success": False, "error": f"Failed to write to database: {str(e)}"}
