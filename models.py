from datetime import datetime
from extensions import db
import uuid
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String, primary_key=True)
    provider = db.Column(db.String(50), nullable=False) # google / github
    name = db.Column(db.String(100), nullable=False, default='User'+str(uuid.uuid4())[:4])
    email = db.Column(db.String(200), index=True)
    avatar_url = db.Column(db.String(500))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.provider}:{self.id} {self.email}>"
