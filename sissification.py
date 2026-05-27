import os
import random
import json
from flask import Flask, request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sissification.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sissy_soft_secret_key_777'
db = SQLAlchemy(app)

# ----------------------------------------------------
# МОДЕЛИ БАЗЫ ДАННЫХ
# ----------------------------------------------------

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_streak = db.Column(db.Integer, default=0)
    last_completed_date = db.Column(db.Date, nullable=True)
    reward_milestone = db.Column(db.Integer, default=7)

class TaskPool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(50), default="Общее")
    is_enabled = db.Column(db.Boolean, default=True)
    is_custom = db.Column(db.Boolean, default=False)
    is_mandatory = db.Column(db.Boolean, default=False)

class DailyAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task_pool.id'))
    date_assigned = db.Column(db.Date, default=date.today)
    is_completed = db.Column(db.Boolean, default=False)
    task = db.relationship('TaskPool')

class RewardLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    date_unlocked = db.Column(db.Date, default=date.today)
    is_claimed = db.Column(db.Boolean, default=False)

class PunishmentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    date_triggered = db.Column(db.Date, default=date.today)
    is_served = db.Column(db.Boolean, default=False)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    time_str = db.Column(db.String(10), nullable=False) # Формат HH:MM

# ----------------------------------------------------
# МЯГКИЙ МОБИЛЬНЫЙ ШАБЛОН (РОЗОВО-ЧЕРНЫЙ НЕОН)
# ----------------------------------------------------

MASTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Протокол Феминизации</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Comfortaa', sans-serif; 
            background-color: #0d0308; 
            color: #fff0f5; 
            margin: 0; 
            padding: 0; 
            font-size: 17px;
            -webkit-tap-highlight-color: transparent;
        }
        .navbar { 
            display: flex; 
            justify-content: space-around; 
            background-color: #1a0612; 
            border-bottom: 3px solid #ff66b2; 
            padding: 12px 5px; 
            position: sticky; 
            top: 0; 
            z-index: 100;
            box-shadow: 0 4px 20px rgba(255, 102, 178, 0.3);
        }
        .navbar a { 
            color: #ff99cc; 
            text-decoration: none; 
            font-weight: bold; 
            font-size: 0.95rem; 
            padding: 8px 4px;
            transition: all 0.3s ease;
        }
        .navbar a.active { 
            color: #ffffff; 
            text-shadow: 0 0 10px #ff66b2, 0 0 20px #ff66b2; 
        }
        .container { 
            padding: 20px 15px; 
            max-width: 100%; 
            box-sizing: border-box;
        }
        h1 { 
            text-align: center; 
            color: #ff3399; 
            text-shadow: 0 0 12px rgba(255, 51, 153, 0.6); 
            font-size: 1.8rem;
            margin-top: 10px;
        }
        h2 { 
            color: #ff66cc; 
            border-bottom: 2px solid #ff3399; 
            padding-bottom: 8px; 
            margin-top: 35px; 
            font-size: 1.3rem;
        }
        .streak-counter { 
            text-align: center; 
            font-size: 1.1rem; 
            color: #fff; 
            text-shadow: 0 0 8px #ff66b2; 
            border: 2px solid #ff66b2; 
            border-radius: 20px;
            padding: 15px; 
            margin-bottom: 25px; 
            background: #26091c;
            box-shadow: inset 0 0 10px rgba(255,102,178,0.2);
        }
        ul { list-style: none; padding: 0; margin: 0; }
        .card-item { 
            background: #1f0b17; 
            padding: 16px; 
            margin-bottom: 15px; 
            border-radius: 18px; 
            border: 1px solid #ff99cc;
            border-left: 6px solid #ff3399; 
            display: flex; 
            flex-direction: column;
            gap: 12px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
        }
        .card-item.completed { 
            border-left-color: #00ffcc; 
            border-color: #00cc99;
            opacity: 0.6; 
        }
        .card-item.completed .task-desc { 
            text-decoration: line-through; 
            color: #00ffcc; 
        }
        .btn { 
            background: linear-gradient(45deg, #ff3399, #ff80df); 
            color: white; 
            border: none; 
            padding: 12px 20px; 
            border-radius: 25px; 
            cursor: pointer; 
            font-weight: bold; 
            font-family: 'Comfortaa', sans-serif;
            text-decoration: none; 
            font-size: 1rem;
            text-align: center;
            display: block;
            box-shadow: 0 4px 10px rgba(255, 51, 153, 0.3);
        }
        .btn-success { background: linear-gradient(45deg, #00cc99, #66ffcc); color: #000; }
        .btn-danger { background: #400d1a; color: #ff6666; border: 1px solid #ff3333; }
        .btn-warning { background: #4d3d00; color: #ffff99; border: 1px solid #ffff33; }
        .btn-info { background: #0b2647; color: #99ccff; border: 1px solid #3399ff; }
        
        .input-text, select, input[type="time"], input[type="number"] { 
            background: #14050f; 
            border: 2px solid #ff66b2; 
            color: #fff; 
            padding: 12px; 
            border-radius: 15px; 
            font-size: 1rem;
            font-family: 'Comfortaa', sans-serif;
            width: 100%;
            box-sizing: border-box;
        }
        .form-block { 
            display: flex; 
            flex-direction: column; 
            gap: 12px; 
            margin-top: 20px; 
        }
        .badge { 
            background: #ff3399; 
            color: #fff; 
            padding: 4px 10px; 
            font-size: 0.75rem; 
            border-radius: 10px; 
            display: inline-block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .badge.mandatory { background: #ff3333; }
        .status-tag { font-weight: bold; text-transform: uppercase; font-size: 0.9rem; text-align: right; display: block;}
        .settings-actions { display: flex; gap: 8px; width: 100%; }
        .settings-actions .btn { flex: 1; padding: 8px 10px; font-size: 0.85rem; }
    </style>
</head>
<body>

    <div class="navbar">
        <a href="{{ url_for('tasks_page') }}" class="{{ 'active' if page == 'tasks' else '' }}">Задания</a>
        <a href="{{ url_for('rewards_page') }}" class="{{ 'active' if page == 'rewards' else '' }}">Награды</a>
        <a href="{{ url_for('punishments_page') }}" class="{{ 'active' if page == 'punishments' else '' }}">Наказания</a>
        <a href="{{ url_for('settings_page') }}" class="{{ 'active' if page == 'settings' else '' }}">Настройки</a>
    </div>

    <div class="container">
        <div class="streak-counter">
            🌸 ДНЕЙ ПОСЛУШАНИЯ ПОДРЯД: {{ progress.current_streak }} 🌸
        </div>

        {# ---------------- СТРАНИЦА ЗАДАНИЙ ---------------- #}
        {% if page == 'tasks' %}
            <h1>Твои Директивы</h1>
            
            <h2>Обязательный Протокол</h2>
            {% if mandatory_assignments|length == 0 %}
                <p style="color: #888; text-align: center; font-style: italic;">Постоянных обязательных задач на сегодня нет.</p>
            {% else %}
                <ul>
                    {% for assign in mandatory_assignments %}
                    <li class="card-item {{ 'completed' if assign.is_completed else '' }}" style="border-left-color: #ff3333;">
                        <div>
                            <span class="badge mandatory">ПОСТОЯННО</span>
                            <div class="task-desc">{{ assign.task.description }}</div>
                        </div>
                        {% if not assign.is_completed %}
                            <a href="{{ url_for('complete_task', assign_id=assign.id) }}" class="btn btn-success">Выполнено</a>
                        {% else %}
                            <span class="status-tag" style="color: #00ffcc;">ПРИНЯТО ✓</span>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
            {% endif %}

            <h2>Случайные Поручения</h2>
            {% if random_assignments|length == 0 %}
                <p style="color: #ff3333; text-align: center;">Нет доступных заданий. Активируй пулл в настройках!</p>
            {% else %}
                <ul>
                    {% for assign in random_assignments %}
                    <li class="card-item {{ 'completed' if assign.is_completed else '' }}">
                        <div>
                            <span class="badge">{{ assign.task.category }}</span>
                            <div class="task-desc">{{ assign.task.description }}</div>
                        </div>
                        {% if not assign.is_completed %}
                            <a href="{{ url_for('complete_task', assign_id=assign.id) }}" class="btn btn-success">Выполнено</a>
                        {% else %}
                            <span class="status-tag" style="color: #00ffcc;">ПРИНЯТО ✓</span>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
            {% endif %}

        {# ---------------- СТРАНИЦА НАГРАД ---------------- #}
        {% elif page == 'rewards' %}
            <h1>Доступные Поощрения</h1>
            <p style="text-align: center; font-style: italic; font-size: 0.9rem;">Каждые {{ progress.reward_milestone }} дней идеального выполнения открывают поблажку.</p>
            <ul>
                {% for reward in rewards %}
                <li class="card-item" style="border-left-color: #00ffcc; border-color: #00cc99;">
                    <div>
                        <span style="font-size: 0.8rem; color: #a6fff2;">[Открыто {{ reward.date_unlocked }}]</span>
                        <div style="margin-top: 5px;">{{ reward.text }}</div>
                    </div>
                    {% if not reward.is_claimed %}
                        <a href="{{ url_for('claim_reward', reward_id=reward.id) }}" class="btn btn-success">Использовать</a>
                    {% else %}
                        <span class="status-tag" style="color: #777;">АКТИВИРОВАНО</span>
                    {% endif %}
                </li>
                {% else %}
                    <p style="text-align: center; color: #888; font-style: italic; margin-top: 20px;">Пока нет доступных наград. Продолжай соблюдать режим.</p>
                {% endfor %}
            </ul>

        {# ---------------- СТРАНИЦА НАКАЗАНИЙ ---------------- #}
        {% elif page == 'punishments' %}
            <h1>Штрафы и Пенальти</h1>
            <p style="text-align: center; color: #ff6666; font-style: italic; font-size: 0.9rem;">Срыв ежедневной серии послушания активирует автоматическое наказание.</p>
            <ul>
                {% for punishment in punishments %}
                <li class="card-item" style="border-left-color: #ff3333; background: #1c050a; border-color: #ff6666;">
                    <div>
                        <span style="font-size: 0.8rem; color: #ff9999; font-weight: bold;">[Наложено {{ punishment.date_triggered }}]</span>
                        <div style="margin-top: 5px; color: #fff;">{{ punishment.text }}</div>
                    </div>
                    {% if not punishment.is_served %}
                        <a href="{{ url_for('serve_punishment', punishment_id=punishment.id) }}" class="btn">Исполнить</a>
                    {% else %}
                        <span class="status-tag" style="color: #00ffcc;">ОТРАБОТАНО ✓</span>
                    {% endif %}
                </li>
                {% else %}
                    <p style="text-align: center; color: #00ffcc; font-style: italic; margin-top: 20px;">Твое досье чисто. Нет активных штрафов.</p>
                {% endfor %}
            </ul>

        {# ---------------- СТРАНИЦА НАСТРОЕК ---------------- #}
        {% elif page == 'settings' %}
            <h1>Управление Режимом</h1>
            
            <h2>Настройка Поощрений</h2>
            <form action="{{ url_for('update_milestone') }}" method="POST" class="form-block">
                <label>Дней до разблокировки награды:</label>
                <input type="number" name="milestone" value="{{ progress.reward_milestone }}" min="1">
                <button type="submit" class="btn">Сохранить</button>
            </form>

            <h2>Напоминания Протокола</h2>
            <p style="font-size: 0.85rem; color: #aaa; margin: 0;">Добавь напоминания, чтобы телефон слал пуши.</p>
            
            <form action="{{ url_for('add_reminder') }}" method="POST" class="form-block">
                <input type="text" name="text" placeholder="Текст (например: Проверить пояс)" required>
                <input type="time" name="time" required>
                <button type="submit" class="btn">Создать пуш</button>
            </form>

            <ul style="margin-top: 15px;">
                {% for rem in reminders %}
                <li style="background:#1c0916; padding:12px; margin-bottom:8px; border-radius:12px; display:flex; justify-content:space-between; align-items:center; border: 1px solid #ff99cc;">
                    <span>🔔 <b>[{{ rem.time_str }}]</b> {{ rem.text }}</span>
                    <a href="{{ url_for('delete_reminder', reminder_id=rem.id) }}" style="color:#ff6666; text-decoration:none; font-weight:bold; padding: 5px 10px;">X</a>
                </li>
                {% endfor %}
            </ul>

            <h2>Список Заданий ({{ task_pool|length }})</h2>
            <ul>
                {% for task in task_pool %}
                <li class="card-item" style="border-left-color: {{ '#ff3333' if task.is_mandatory else ('#ff3399' if task.is_enabled else '#444') }}; background: #12030d;">
                    <div>
                        {% if task.is_mandatory %}
                            <span class="badge mandatory">Постоянное</span>
                        {% else %}
                            <span class="badge" style="background: #401433;">{{ task.category }}</span>
                        {% endif %}
                        <div style="color: {{ '#fff' if task.is_enabled else '#777' }}; font-size: 0.95rem;">{{ task.description }}</div>
                    </div>
                    <div class="settings-actions">
                        {% if task.is_enabled %}
                            <a href="{{ url_for('toggle_task', task_id=task.id) }}" class="btn btn-danger">Выкл</a>
                        {% else %}
                            <a href="{{ url_for('toggle_task', task_id=task.id) }}" class="btn btn-success">Вкл</a>
                        {% endif %}
                        
                        {% if task.is_mandatory %}
                            <a href="{{ url_for('toggle_mandatory', task_id=task.id) }}" class="btn btn-info">Рандом</a>
                        {% else %}
                            <a href="{{ url_for('toggle_mandatory', task_id=task.id) }}" class="btn btn-warning">Закрепить</a>
                        {% endif %}
                    </div>
                </li>
                {% endfor %}
            </ul>

            <h2>Добавить свое правило</h2>
            <form action="{{ url_for('add_custom_task') }}" method="POST" class="form-block">
                <select name="category">
                    <option value="Тренировка">Тренировка</option>
                    <option value="Внешность">Внешность</option>
                    <option value="Послушание">Послушание</option>
                </select>
                <input type="text" name="description" placeholder="Введи условия задания..." required>
                <button type="submit" class="btn">Добавить</button>
            </form>
        {% endif %}
    </div>

    <!-- ДВИЖОК МОБИЛЬНЫХ НАПОМИНАНИЙ И ПУШЕЙ -->
    <script>
        const remindersData = {{ reminders_json|safe if reminders_json else '[]' }};
        
        // Запрос разрешений на пуши в мобильном браузере
        if (window.Notification && Notification.permission !== "granted" && Notification.permission !== "denied") {
            Notification.requestPermission();
        }

        function checkReminders() {
            const now = new Date();
            const currentHours = String(now.getHours()).padStart(2, '0');
            const currentMinutes = String(now.getMinutes()).padStart(2, '0');
            const currentTimeStr = `${currentHours}:${currentMinutes}`;

            remindersData.forEach(rem => {
                if (rem.time === currentTimeStr) {
                    // Чтобы пуш не дублировался каждую секунду внутри этой минуты
                    if (!window[`notified_${rem.id}_${currentTimeStr}`]) {
                        window[`notified_${rem.id}_${currentTimeStr}`] = true;
                        
                        if (Notification.permission === "granted") {
                            new Notification("Протокол Напоминает!", {
                                body: rem.text,
                                icon: "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100"
                            });
                        } else {
                            alert(`🔔 НАПОМИНАНИЕ: ${rem.text}`);
                        }
                    }
                }
            });
        }

        if (remindersData.length > 0) {
            setInterval(checkReminders, 15000); // Проверка каждые 15 сек
        }
    </script>
</body>
</html>
"""

# ----------------------------------------------------
# ЛОГИКА ПРИЛОЖЕНИЯ
# ----------------------------------------------------

def run_daily_checks():
    today = date.today()
    progress = UserProgress.query.first()
    
    if not progress:
        progress = UserProgress(current_streak=0)
        db.session.add(progress)
        db.session.commit()

    if progress.last_completed_date:
        days_missed = (today - progress.last_completed_date).days
        if days_missed > 1:
            if progress.current_streak > 0:
                punishment_text = f"Срыв дисциплины! Серия из {progress.current_streak} дней потеряна. Наказание: +2 дополнительных дня строгого режима в поясе верности либо принудительная сессия катания на дилдо длительностью 45 минут."
                db.session.add(PunishmentLog(text=punishment_text, date_triggered=today))
            progress.current_streak = 0
            db.session.commit()

    current_assignments = DailyAssignment.query.filter_by(date_assigned=today).all()
    if not current_assignments:
        # 1. Постоянный протокол
        mandatory_tasks = TaskPool.query.filter_by(is_enabled=True, is_mandatory=True).all()
        for t in mandatory_tasks:
            db.session.add(DailyAssignment(task_id=t.id, date_assigned=today))

        # 2. 3 рандомных задания
        random_pool = TaskPool.query.filter_by(is_enabled=True, is_mandatory=False).all()
        if len(random_pool) >= 3:
            selected_randoms = random.sample(random_pool, 3)
        else:
            selected_randoms = random_pool
            
        for t in selected_randoms:
            db.session.add(DailyAssignment(task_id=t.id, date_assigned=today))
            
        db.session.commit()

def get_reminders_json():
    rems = Reminder.query.all()
    return json.dumps([{"id": r.id, "text": r.text, "time": r.time_str} for r in rems])

@app.route('/')
@app.route('/tasks')
def tasks_page():
    run_daily_checks()
    progress = UserProgress.query.first()
    all_today = DailyAssignment.query.filter_by(date_assigned=date.today()).all()
    mandatory_assignments = [a for a in all_today if a.task.is_mandatory]
    random_assignments = [a for a in all_today if not a.task.is_mandatory]
    return render_template_string(
        MASTER_TEMPLATE, page='tasks', progress=progress, 
        mandatory_assignments=mandatory_assignments, random_assignments=random_assignments,
        reminders_json=get_reminders_json()
    )

@app.route('/complete_task/<int:assign_id>')
def complete_task(assign_id):
    assign = DailyAssignment.query.get_or_404(assign_id)
    assign.is_completed = True
    db.session.commit()

    today = date.today()
    all_today = DailyAssignment.query.filter_by(date_assigned=today).all()
    
    if all(item.is_completed for item in all_today):
        progress = UserProgress.query.first()
        if progress.last_completed_date == today - timedelta(days=1):
            progress.current_streak += 1
        elif progress.last_completed_date != today:
            progress.current_streak = 1
        
        progress.last_completed_date = today

        if progress.current_streak > 0 and (progress.current_streak % progress.reward_milestone == 0):
            reward_text = f"За отличную покорность в течение {progress.current_streak} дней! Разрешается: 24 часа без пояса верности ИЛИ контролируемый сиссигазм по твоему выбору."
            db.session.add(RewardLog(text=reward_text, date_unlocked=today))
            
        db.session.commit()

    return redirect(url_for('tasks_page'))

@app.route('/rewards')
def rewards_page():
    progress = UserProgress.query.first()
    rewards = RewardLog.query.order_by(RewardLog.date_unlocked.desc()).all()
    return render_template_string(MASTER_TEMPLATE, page='rewards', progress=progress, rewards=rewards, reminders_json=get_reminders_json())

@app.route('/claim_reward/<int:reward_id>')
def claim_reward(reward_id):
    reward = RewardLog.query.get_or_404(reward_id)
    reward.is_claimed = True
    db.session.commit()
    return redirect(url_for('rewards_page'))

@app.route('/punishments')
def punishments_page():
    progress = UserProgress.query.first()
    punishments = PunishmentLog.query.order_by(PunishmentLog.date_triggered.desc()).all()
    return render_template_string(MASTER_TEMPLATE, page='punishments', progress=progress, punishments=punishments, reminders_json=get_reminders_json())

@app.route('/serve_punishment/<int:punishment_id>')
def serve_punishment(punishment_id):
    punishment = PunishmentLog.query.get_or_404(punishment_id)
    punishment.is_served = True
    db.session.commit()
    return redirect(url_for('punishments_page'))

@app.route('/settings')
def settings_page():
    progress = UserProgress.query.first()
    task_pool = TaskPool.query.all()
    reminders = Reminder.query.all()
    return render_template_string(MASTER_TEMPLATE, page='settings', progress=progress, task_pool=task_pool, reminders=reminders, reminders_json=get_reminders_json())

@app.route('/toggle_task/<int:task_id>')
def toggle_task(task_id):
    task = TaskPool.query.get_or_404(task_id)
    task.is_enabled = not task.is_enabled
    db.session.commit()
    return redirect(url_for('settings_page'))

@app.route('/toggle_mandatory/<int:task_id>')
def toggle_mandatory(task_id):
    task = TaskPool.query.get_or_404(task_id)
    task.is_mandatory = not task.is_mandatory
    db.session.commit()
    return redirect(url_for('settings_page'))

@app.route('/add_custom_task', methods=['POST'])
def add_custom_task():
    desc = request.form.get('description')
    cat = request.form.get('category', 'Тренировка')
    if desc:
        db.session.add(TaskPool(description=desc, category=cat, is_custom=True, is_enabled=True, is_mandatory=False))
        db.session.commit()
    return redirect(url_for('settings_page'))

@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    text = request.form.get('text')
    time_str = request.form.get('time')
    if text and time_str:
        db.session.add(Reminder(text=text, time_str=time_str))
        db.session.commit()
    return redirect(url_for('settings_page'))

@app.route('/delete_reminder/<int:reminder_id>')
def delete_reminder(reminder_id):
    rem = Reminder.query.get_or_404(reminder_id)
    db.session.delete(rem)
    db.session.commit()
    return redirect(url_for('settings_page'))

@app.route('/update_milestone', methods=['POST'])
def update_milestone():
    val = request.form.get('milestone')
    if val:
        progress = UserProgress.query.first()
        progress.reward_milestone = int(val)
        db.session.commit()
    return redirect(url_for('settings_page'))

# ----------------------------------------------------
# ИНИЦИАЛИЗАЦИЯ И ИМПОРТ 100 ЗАДАНИЙ (НА РУССКОМ)
# ----------------------------------------------------

def seed_initial_tasks():
    if TaskPool.query.count() > 0:
        return
        
    russian_tasks = [
        ("Катание на дилдо (Райдинг) — 30 минут", "Тренировка"),
        ("Катание на дилдо — 15 минут", "Тренировка"),
        ("Катание на дилдо — 45 минут", "Тренировка"),
        ("Катание на дилдо — 10 минут в интенсивном быстром темпе", "Тренировка"),
        ("Катание на дилдо — 60 минут с постоянным эджингом", "Тренировка"),
        ("Ношение анальной пробки — 2 часа в процессе дня", "Тренировка"),
        ("Ношение анальной пробки — 4 часа непрерывно", "Тренировка"),
        ("Ношение анальной пробки — 8 часов (включая ночной сон)", "Тренировка"),
        ("Ношение анальной пробки — 1 час во время домашних дел", "Тренировка"),
        ("Ношение анальной пробки — 30 минут совмещая с упражнениями Кегеля", "Тренировка"),
        ("Практика глубокого горла на дилдо — 10 минут", "Тренировка"),
        ("Практика глубокого горла — 20 минут", "Тренировка"),
        ("Практика глубокого горла — 5 минут с акцентом на подавление рвотного рефлекса", "Тренировка"),
        ("Фейсфаккинг с дилдо на присоске — 15 минут", "Тренировка"),
        ("Фейсфаккинг с дилдо на присоске — 25 минут", "Тренировка"),
        ("Очищение клизмой — 500 мл", "Послушание"),
        ("Очищение клизмой — 1000 мл (полный объем)", "Послушание"),
        ("Удержание воды после клизмы — 15 минут", "Послушание"),
        ("Удержание воды после клизмы — 30 минут", "Послушание"),
        ("Ношение пояса верности (Chastity) — 12 часов", "Послушание"),
        ("Ношение пояса верности — 24 часа", "Послушание"),
        ("Ношение пояса верности — 3 дня подряд", "Послушание"),
        ("Ношение пояса верности — 7 дней (с еженедельным очищением)", "Послушание"),
        ("Замок пояса верности во льду — ждать до полного таяния (около 30 минут)", "Послушание"),
        ("Ходьба на высоких каблуках — 20 минут внутри дома", "Внешность"),
        ("Ходьба на каблуках — 45 минут по твердому полу", "Внешность"),
        ("Ношение туфель на каблуках — 2 часа без возможности сидеть (только стоя)", "Внешность"),
        ("Нахождение только в женских трусиках (без другой одежды) — 1 час дома", "Внешность"),
        ("Комплект: трусики + бюстгальтер + чулки — носить 3 часа", "Внешность"),
        ("Полный комплект женского белья — 6 часов (включая выход на улицу под обычной одеждой)", "Внешность"),
        ("Практика макияжа: нанесение полного лица — 30 минут", "Внешность"),
        ("Макияж: яркие тени + помада — носить в течение 2 часов", "Внешность"),
        ("Обновление макияжа 3 раза за один день (каждая сессия по 15 минут)", "Внешность"),
        ("Бритье: полное удаление волос на теле (ноги, грудь, подмышки, пах) — 45 минут", "Внешность"),
        ("Бритье ног до абсолютной гладкости", "Внешность"),
        ("Удаление волос кремом в зоне бикини", "Внешность"),
        ("Коррекция бровей или удаление волос над губой восковыми полосками", "Внешность"),
        ("Тренировка женского голоса — 15 минут на высокой частоте", "Тренировка"),
        ("Голосовая тренировка — повторение сисси-фраз вслух в течение 20 минут", "Тренировка"),
        ("Подпевание женским поп-хитам в высокой тональности (1 час на репите)", "Тренировка"),
        ("Женская походка — практика покачивания бедрами 10 минут", "Тренировка"),
        ("Прогулка в общественном месте в женском белье под одеждой — 30 минут", "Послушание"),
        ("Справлять нужду только сидя в течение всего дня (24 часа)", "Послушание"),
        ("Сисси-диета: употреблять только фрукты и йогурты целый день", "Послушание"),
        ("Пить воду/молоко только из бутылочки с соской — 1 полная бутылка (500 мл)", "Послушание"),
        ("Ношение юбки дома — 4 часа", "Внешность"),
        ("Ношение платья дома — 2 часа (включая легкий макияж)", "Внешность"),
        ("Сделать хвостики или использовать женские заколки для волос на весь день", "Внешность"),
        ("Яркий лак на ногтях рук — держать минимум 2 дня", "Внешность"),
        ("Педикюр: яркий лак на ногтях ног — держать 7 дней", "Внешность"),
        ("Легкое самосвязывание с фиксацией рук — 20 минут (безопасные ножницы рядом)", "Послушание"),
        ("Минент дилдо с завязанными глазами — 15 минут", "Тренировка"),
        ("Наручники + ножные кандалы — носить 1 час во время уборки дома", "Послушание"),
        ("Просмотр сисси-гипно видео — 10 минут концентрации", "Тренировка"),
        ("Просмотр сисси-гипно — 30 минут строго в наушниках", "Тренировка"),
        ("Просмотр сисси-гипно — 60 минут (допускается эджинг, оргазм запрещен)", "Тренировка"),
        ("Чтение сисси-капшенов (эротических подписей) — 20 минут", "Тренировка"),
        ("Написать сисси-аффирмации 10 раз вручную (например, 'Я послушная девочка')", "Послушание"),
        ("Прописать в блокноте 50 строчек с правилами твоего послушания", "Послушание"),
        ("Сделать и отправить анонимное сисси-фото (без лица) на тематическую площадку", "Послушание"),
        ("Общение в чате с доминантной личностью в роли сисси в течение 30 минут", "Послушание"),
        ("Выполнение аудио-инструкций по феминизации (JOI) — полная сессия (около 25 минут)", "Тренировка"),
        ("Попытка испорченного оргазма (ruined orgasm) в поясе верности с вибратором — 10 минут", "Тренировка"),
        ("Массаж простаты пальцем — 15 минут", "Тренировка"),
        ("Использование массажера простаты — 30 минут (без рук)", "Тренировка"),
        ("Ношение анальной пробки во время сна — всю ночь", "Тренировка"),
        ("Анальная пробка во время тренировки — 20 приседаний + 30 минут ходьбы", "Тренировка"),
        ("Клизма с лубрикантом — 250 мл, удерживать внутри 10 минут", "Послушание"),
        ("Введение кубиков льда в анус — 2 кубика по очереди до полного таяния", "Тренировка"),
        ("Прищепки на сосках — 10 минут", "Послушание"),
        ("Прищепки на сосках и интимных зонах — 15 минут", "Послушание"),
        ("Удары канцелярской резинкой по внутренней стороне бедра — всего 20 щелчков", "Послушание"),
        (" Легкая порка шлепанцем/паддлом — по 50 шлепков на каждую ягодицу", "Послушание"),
        ("Ношение ошейника (чокера) весь день — 24 часа", "Внешность"),
        ("Ношение ошейника с бубенчиком — 2 часа дома", "Внешность"),
        ("Практика реверансов и поклонов перед зеркалом — 5 минут (20 повторений)", "Послушание"),
        ("Уборка дома только в кухонном фартуке и на каблуках — 1 час", "Послушание"),
        ("Прием пищи из собачьей миски с пола (без рук) — один раз за день", "Послушание"),
        ("Передвижение по дому только на четвереньках в течение 5 минут", "Послушание"),
        ("Просить мысленное разрешение у Госпожи перед походом в туалет и терпеть 2 минуты", "Послушание"),
        ("Ношение маски на лице с надписью 'SISSY' дома — 1 час", "Послушание"),
        ("Исполнение приватного стриптиза перед зеркалом — 10 минут", "Внешность"),
        ("Стимуляция интимных зон вибратором — 20 минут", "Тренировка"),
        ("Испытание отказом (No-touch challenge) — 3 дня без прикосновений и оргазма", "Послушание"),
        ("Довести себя до грани (эдж) 5 раз подряд и остановиться — сделать дважды за день", "Тренировка"),
        ("Слизывание собственного эякулята с ложки после эджинга — один раз", "Послушание"),
        ("Очищение дилдо языком после анального использования — 30 секунд", "Послушание"),
        ("Ношение мокрого подгузника (смоченного чистой водой) — 30 минут", "Послушание"),
        ("Ношение подгузника и пластиковых трусиков поверх — 2 часа (просто ношение)", "Послушание"),
        ("Повторить вслух фразу 'Я хорошая сисси девочка' ровно 100 раз перед зеркалом", "Послушание"),
        ("Записать аудиосообщение со своим признанием в сисси-желаниях и сохранить в архив", "Послушание"),
        ("Сон в атласной или кружевной ночной сорочке — одна ночь", "Внешность"),
        ("Использование женского геля для душа и лосьона на все тело — 15 минут ухода", "Внешность"),
        ("Использование чисто женского парфюма перед началом дня", "Внешность"),
        ("Выбрить аккуратную форму сердца в интимной зоне паха", "Внешность"),
        ("50 упражнений Кегеля с удерживанием Kegel ball или анального яйца внутри", "Тренировка"),
        ("Ношение стрингов задом наперед (узкой нитью вперед) — 2 часа", "Внешность"),
        ("Использование мягких зажимов на соски — 5 минут", "Послушание"),
        ("Охлаждение сосков кубиками льда по 30 секунд — 3 полных цикла", "Послушание"),
        ("Катание на дилдо с кляпом из скрученных трусиков во рту — 20 минут", "Тренировка")
    ]

    for desc, cat in russian_tasks:
        # По умолчанию ставим одну задачу обязательной для наглядности
        is_mandatory = True if "Пояс верности — 24 часа" in desc else False
        db.session.add(TaskPool(description=desc, category=cat, is_mandatory=is_mandatory))
        
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        # База данных очищается для обновления под русский язык и новые колонки
        db.drop_all() 
        db.create_all()
        seed_initial_tasks()
    app.run(debug=True, host='0.0.0.0') # Доступно локально с мобильного устройства
