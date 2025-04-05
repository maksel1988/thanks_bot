from flask import Flask, render_template, request, send_file
import psycopg2
from datetime import datetime
import os
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# Настройки PostgreSQL
DB_NAME = os.getenv('DB_NAME', 'thanks_bot')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT username, COUNT(*) as count 
        FROM mentions 
        WHERE mentioned_at >= date_trunc('month', NOW())
        GROUP BY username 
        ORDER BY count DESC
        LIMIT 10
    """)
    current_stats = cur.fetchall()
    
    cur.execute("""
        SELECT username, COUNT(*) as count 
        FROM mentions 
        GROUP BY username 
        ORDER BY count DESC
        LIMIT 10
    """)
    all_time_stats = cur.fetchall()
    
    cur.execute("""
        SELECT username, thanks_count, month, year 
        FROM monthly_winners 
        ORDER BY year DESC, month DESC
        LIMIT 12
    """)
    monthly_winners = cur.fetchall()
    
    cur.close()
    conn.close()
    
    current_month = datetime.now().strftime('%B %Y')
    
    return render_template(
        'index.html',
        current_month=current_month,
        current_stats=current_stats,
        all_time_stats=all_time_stats,
        monthly_winners=monthly_winners
    )

@app.route('/export', methods=['GET', 'POST'])
def export_data():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        format_type = request.form.get('format', 'csv')
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    m.username,
                    t.sender_username,
                    t.message_text,
                    m.mentioned_at
                FROM mentions m
                JOIN thanks t ON m.thanks_id = t.id
                WHERE m.mentioned_at BETWEEN %s AND %s
                ORDER BY m.mentioned_at DESC
            """, (start_date, end_date))
            
            data = cur.fetchall()
            columns = ['Кому', 'От кого', 'Текст', 'Дата']
            df = pd.DataFrame(data, columns=columns)
            
            if format_type == 'csv':
                output = BytesIO()
                df.to_csv(output, index=False, encoding='utf-8')
                output.seek(0)
                return send_file(
                    output,
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'thanks_export_{start_date}_{end_date}.csv'
                )
            else:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Благодарности')
                output.seek(0)
                return send_file(
                    output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'thanks_export_{start_date}_{end_date}.xlsx'
                )
            
        except Exception as e:
            return f"Ошибка: {str(e)}", 500
        
    return render_template('export.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
