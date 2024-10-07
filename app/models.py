from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .db import Base  # Ensure you import Base from the correct location
from datetime import datetime

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    plan_id = Column(String)
    amount = Column(Float)
    currency = Column(String)
    payment_status = Column(String)
    stripe_session_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")

