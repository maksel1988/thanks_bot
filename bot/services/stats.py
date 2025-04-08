from datetime import datetime
from sqlalchemy import func
from ..services.db import get_db
from ..models.thanks import ThanksMessage

def get_monthly_stats(year: int = None, month: int = None):
    db = next(get_db())
    
    query = db.query(
        ThanksMessage.receiver_usernames,
        func.count(ThanksMessage.id).label('count')
    )
    
    if year and month:
        query = query.filter(
            func.extract('year', ThanksMessage.created_at) == year,
            func.extract('month', ThanksMessage.created_at) == month
        )
    
    return query.group_by(ThanksMessage.receiver_usernames)\
               .order_by(func.count(ThanksMessage.id).desc())\
               .all()

def export_stats(start_date: datetime, end_date: datetime):
    db = next(get_db())
    
    return db.query(
        func.to_char(ThanksMessage.created_at, 'YYYY-MM').label('period'),
        ThanksMessage.receiver_usernames,
        func.count(ThanksMessage.id).label('count')
    ).filter(
        ThanksMessage.created_at.between(start_date, end_date)
    ).group_by(
        'period', ThanksMessage.receiver_usernames
    ).order_by(
        'period', func.count(ThanksMessage.id).desc()
    ).all()
