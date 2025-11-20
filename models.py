from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Text, primary_key=True)          # provider-specific id (string)
    provider = db.Column(db.String(50), primary_key=True)  
    email = db.Column(db.String(200), index=True)
    avatar_url = db.Column(db.String(500))
    last_login = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # convenience representation
    def __repr__(self):
        return f"<User {self.provider}:{self.id} {self.email}>"
