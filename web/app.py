from flask import Flask, render_template, request, send_file
from io import BytesIO
import pandas as pd
from datetime import datetime
from bot.services.db import get_db
from bot.models.thanks import ThanksMessage

app = Flask(__name__)

@app.route('/')
def index():
    db = next(get_db())
    
    # Получаем статистику за текущий месяц
    current_month = datetime.now().strftime('%Y-%m')
    query = db.query(
        ThanksMessage.receiver_usernames,
        func.count(ThanksMessage.id).label('count')
    ).filter(
        func.to_char(ThanksMessage.created_at, 'YYYY-MM') == current_month
    ).group_by(
        ThanksMessage.receiver_usernames
    ).order_by(
        func.count(ThanksMessage.id).desc()
    )
    
    stats = query.all()
    
    return render_template('index.html', stats=stats, current_month=current_month)

@app.route('/export')
def export_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    db = next(get_db())
    
    query = db.query(
        func.to_char(ThanksMessage.created_at, 'YYYY-MM').label('period'),
        ThanksMessage.receiver_usernames,
        func.count(ThanksMessage.id).label('count')
    )
    
    if start_date:
        query = query.filter(ThanksMessage.created_at >= start_date)
    if end_date:
        query = query.filter(ThanksMessage.created_at <= end_date)
    
    stats = query.group_by(
        'period', ThanksMessage.receiver_usernames
    ).order_by(
        'period', func.count(ThanksMessage.id).desc()
    ).all()
    
    # Создаем DataFrame
    df = pd.DataFrame([(s.period, s.receiver_usernames, s.count) for s in stats],
                     columns=['Period', 'Usernames', 'Count'])
    
    # Создаем Excel файл в памяти
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Stats', index=False)
    writer.close()
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='thanks_stats.xlsx'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
