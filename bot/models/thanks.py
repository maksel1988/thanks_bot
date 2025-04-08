from sqlalchemy import Column, Integer, String, DateTime, func
from ..services.db import Base

class ThanksMessage(Base):
    __tablename__ = 'thanks_messages'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer)
    sender_username = Column(String)
    receiver_usernames = Column(String)  # храним как строку "@user1 @user2"
    message_text = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<ThanksMessage(from={self.sender_username}, to={self.receiver_usernames})>"
