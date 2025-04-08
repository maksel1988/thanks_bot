from flask import Blueprint, render_template
from datetime import datetime
from bot.services.stats import get_monthly_stats

stats_blueprint = Blueprint('stats', __name__)

@stats_blueprint.route('/')
def index():
    now = datetime.now()
    stats = get_monthly_stats(now.year, now.month)
    return render_template('index.html', 
                         stats=stats, 
                         current_month=now.strftime('%B %Y'))
