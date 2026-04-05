from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, Group, Subject, Teacher, Room, Lesson
from functools import wraps

DAYS = {1: 'Понедельник', 2: 'Вторник', 3: 'Среда', 4: 'Четверг', 5: 'Пятница', 6: 'Суббота'}
TIME_SLOTS = {
    1: '9:00 - 10:30',
    2: '10:40 - 12:10',
    3: '12:20 - 13:50',
    4: '14:30 - 16:00',
    5: '16:10 - 17:40',
    6: '17:50 - 19:20',
    7: '19:30 - 21:00'
}
LESSON_TYPES = ['Лекция', 'Практика', 'Лабораторная']
WEEK_TYPES = ['Каждая', 'Чётная', 'Нечётная']


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Доступ запрещён', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_globals():
    return dict(days=DAYS, time_slots=TIME_SLOTS)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.route('/')
def index():
    stats = {
        'groups': Group.query.count(),
        'teachers': Teacher.query.count(),
        'subjects': Subject.query.count(),
        'lessons': Lesson.query.count()
    }
    return render_template('index.html', stats=stats)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Вы успешно вошли в систему', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    groups = Group.query.order_by(Group.name).all()
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        group_id = request.form.get('group_id')

        if password != password2:
            flash('Пароли не совпадают', 'danger')
            return render_template('register.html', groups=groups)

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким логином уже существует', 'danger')
            return render_template('register.html', groups=groups)

        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован', 'danger')
            return render_template('register.html', groups=groups)

        user = User(username=username, email=email, full_name=full_name, role='student')
        if group_id:
            user.group_id = int(group_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', groups=groups)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/schedule')
def schedule():
    groups = Group.query.order_by(Group.name).all()
    teachers = Teacher.query.order_by(Teacher.full_name).all()
    rooms = Room.query.order_by(Room.number).all()

    group_id = request.args.get('group_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    room_id = request.args.get('room_id', type=int)

    selected = {'group_id': group_id, 'teacher_id': teacher_id, 'room_id': room_id}

    query = Lesson.query
    if group_id:
        query = query.filter_by(group_id=group_id)
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    if room_id:
        query = query.filter_by(room_id=room_id)

    lessons = query.all()

    schedule_data = {}
    for lesson in lessons:
        key = (lesson.day_of_week, lesson.time_slot)
        if key not in schedule_data:
            schedule_data[key] = []
        schedule_data[key].append(lesson)

    return render_template('schedule.html',
                         groups=groups, teachers=teachers, rooms=rooms,
                         schedule_data=schedule_data, selected=selected)


@app.route('/api/schedule')
def api_schedule():
    group_id = request.args.get('group_id', type=int)
    teacher_id = request.args.get('teacher_id', type=int)
    room_id = request.args.get('room_id', type=int)

    query = Lesson.query
    if group_id:
        query = query.filter_by(group_id=group_id)
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    if room_id:
        query = query.filter_by(room_id=room_id)

    lessons = query.all()
    result = []
    for l in lessons:
        result.append({
            'id': l.id,
            'subject': l.subject.name,
            'teacher': l.teacher.full_name,
            'group': l.group.name,
            'room': l.room.number + (', ' + l.room.building if l.room.building else ''),
            'day_of_week': l.day_of_week,
            'time_slot': l.time_slot,
            'lesson_type': l.lesson_type,
            'week_type': l.week_type,
            'time': TIME_SLOTS.get(l.time_slot, ''),
            'day_name': DAYS.get(l.day_of_week, '')
        })
    return jsonify(result)


@app.route('/profile')
@login_required
def profile():
    user_lessons = []
    if current_user.group_id:
        user_lessons = Lesson.query.filter_by(group_id=current_user.group_id)\
            .order_by(Lesson.day_of_week, Lesson.time_slot).all()
    return render_template('profile.html', user_lessons=user_lessons)


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'users': User.query.count(),
        'groups': Group.query.count(),
        'subjects': Subject.query.count(),
        'teachers': Teacher.query.count(),
        'rooms': Room.query.count(),
        'lessons': Lesson.query.count()
    }
    return render_template('admin/dashboard.html', stats=stats)


@app.route('/admin/groups')
@login_required
@admin_required
def admin_groups():
    groups = Group.query.order_by(Group.course, Group.name).all()
    return render_template('admin/groups.html', groups=groups)


@app.route('/admin/groups/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_group_add():
    if request.method == 'POST':
        group = Group(
            name=request.form['name'],
            course=int(request.form['course']),
            faculty=request.form['faculty']
        )
        db.session.add(group)
        db.session.commit()
        flash('Группа добавлена', 'success')
        return redirect(url_for('admin_groups'))
    return render_template('admin/group_form.html', group=None)


@app.route('/admin/groups/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_group_edit(id):
    group = Group.query.get_or_404(id)
    if request.method == 'POST':
        group.name = request.form['name']
        group.course = int(request.form['course'])
        group.faculty = request.form['faculty']
        db.session.commit()
        flash('Группа обновлена', 'success')
        return redirect(url_for('admin_groups'))
    return render_template('admin/group_form.html', group=group)


@app.route('/admin/groups/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_group_delete(id):
    group = Group.query.get_or_404(id)
    db.session.delete(group)
    db.session.commit()
    flash('Группа удалена', 'success')
    return redirect(url_for('admin_groups'))


@app.route('/admin/subjects')
@login_required
@admin_required
def admin_subjects():
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('admin/subjects.html', subjects=subjects)


@app.route('/admin/subjects/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_subject_add():
    if request.method == 'POST':
        subj = Subject(name=request.form['name'])
        db.session.add(subj)
        db.session.commit()
        flash('Дисциплина добавлена', 'success')
        return redirect(url_for('admin_subjects'))
    return render_template('admin/subject_form.html', subject=None)


@app.route('/admin/subjects/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_subject_edit(id):
    subj = Subject.query.get_or_404(id)
    if request.method == 'POST':
        subj.name = request.form['name']
        db.session.commit()
        flash('Дисциплина обновлена', 'success')
        return redirect(url_for('admin_subjects'))
    return render_template('admin/subject_form.html', subject=subj)


@app.route('/admin/subjects/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_subject_delete(id):
    subj = Subject.query.get_or_404(id)
    db.session.delete(subj)
    db.session.commit()
    flash('Дисциплина удалена', 'success')
    return redirect(url_for('admin_subjects'))


@app.route('/admin/teachers')
@login_required
@admin_required
def admin_teachers():
    teachers = Teacher.query.order_by(Teacher.full_name).all()
    return render_template('admin/teachers.html', teachers=teachers)


@app.route('/admin/teachers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_teacher_add():
    if request.method == 'POST':
        t = Teacher(
            full_name=request.form['full_name'],
            department=request.form.get('department', '')
        )
        db.session.add(t)
        db.session.commit()
        flash('Преподаватель добавлен', 'success')
        return redirect(url_for('admin_teachers'))
    return render_template('admin/teacher_form.html', teacher=None)


@app.route('/admin/teachers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_teacher_edit(id):
    t = Teacher.query.get_or_404(id)
    if request.method == 'POST':
        t.full_name = request.form['full_name']
        t.department = request.form.get('department', '')
        db.session.commit()
        flash('Преподаватель обновлён', 'success')
        return redirect(url_for('admin_teachers'))
    return render_template('admin/teacher_form.html', teacher=t)


@app.route('/admin/teachers/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_teacher_delete(id):
    t = Teacher.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    flash('Преподаватель удалён', 'success')
    return redirect(url_for('admin_teachers'))


@app.route('/admin/rooms')
@login_required
@admin_required
def admin_rooms():
    rooms = Room.query.order_by(Room.building, Room.number).all()
    return render_template('admin/rooms.html', rooms=rooms)


@app.route('/admin/rooms/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_room_add():
    if request.method == 'POST':
        r = Room(
            number=request.form['number'],
            building=request.form.get('building', ''),
            capacity=int(request.form.get('capacity', 30)),
            room_type=request.form.get('room_type', 'Лекционная')
        )
        db.session.add(r)
        db.session.commit()
        flash('Аудитория добавлена', 'success')
        return redirect(url_for('admin_rooms'))
    return render_template('admin/room_form.html', room=None)


@app.route('/admin/rooms/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_room_edit(id):
    r = Room.query.get_or_404(id)
    if request.method == 'POST':
        r.number = request.form['number']
        r.building = request.form.get('building', '')
        r.capacity = int(request.form.get('capacity', 30))
        r.room_type = request.form.get('room_type', 'Лекционная')
        db.session.commit()
        flash('Аудитория обновлена', 'success')
        return redirect(url_for('admin_rooms'))
    return render_template('admin/room_form.html', room=r)


@app.route('/admin/rooms/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_room_delete(id):
    r = Room.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    flash('Аудитория удалена', 'success')
    return redirect(url_for('admin_rooms'))


def check_conflicts(day, slot, group_id, teacher_id, room_id, week_type, exclude_id=None):
    conflicts = []
    query = Lesson.query.filter_by(day_of_week=day, time_slot=slot)
    if exclude_id:
        query = query.filter(Lesson.id != exclude_id)
    existing = query.all()
    for les in existing:
        if week_type == 'Каждая' or les.week_type == 'Каждая' or week_type == les.week_type:
            if les.group_id == group_id:
                conflicts.append('У группы ' + les.group.name + ' уже есть занятие в это время')
            if les.teacher_id == teacher_id:
                conflicts.append('У преподавателя ' + les.teacher.full_name + ' уже есть занятие в это время')
            if les.room_id == room_id:
                conflicts.append('Аудитория ' + les.room.number + ' уже занята в это время')
    return conflicts


@app.route('/admin/lessons')
@login_required
@admin_required
def admin_lessons():
    lessons = Lesson.query.order_by(Lesson.day_of_week, Lesson.time_slot).all()
    return render_template('admin/lessons.html', lessons=lessons)


@app.route('/admin/lessons/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_lesson_add():
    if request.method == 'POST':
        day = int(request.form['day_of_week'])
        slot = int(request.form['time_slot'])
        group_id = int(request.form['group_id'])
        teacher_id = int(request.form['teacher_id'])
        room_id = int(request.form['room_id'])
        week_type = request.form.get('week_type', 'Каждая')

        conflicts = check_conflicts(day, slot, group_id, teacher_id, room_id, week_type)
        if conflicts:
            for c in conflicts:
                flash(c, 'danger')
            return render_template('admin/lesson_form.html', lesson=None,
                                 subjects=Subject.query.all(),
                                 teachers=Teacher.query.all(),
                                 groups=Group.query.all(),
                                 rooms=Room.query.all(),
                                 lesson_types=LESSON_TYPES,
                                 week_types=WEEK_TYPES)

        les = Lesson(
            subject_id=int(request.form['subject_id']),
            teacher_id=teacher_id,
            group_id=group_id,
            room_id=room_id,
            day_of_week=day,
            time_slot=slot,
            lesson_type=request.form.get('lesson_type', 'Лекция'),
            week_type=week_type
        )
        db.session.add(les)
        db.session.commit()
        flash('Занятие добавлено', 'success')
        return redirect(url_for('admin_lessons'))

    return render_template('admin/lesson_form.html', lesson=None,
                         subjects=Subject.query.all(),
                         teachers=Teacher.query.all(),
                         groups=Group.query.all(),
                         rooms=Room.query.all(),
                         lesson_types=LESSON_TYPES,
                         week_types=WEEK_TYPES)


@app.route('/admin/lessons/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_lesson_edit(id):
    les = Lesson.query.get_or_404(id)
    if request.method == 'POST':
        day = int(request.form['day_of_week'])
        slot = int(request.form['time_slot'])
        group_id = int(request.form['group_id'])
        teacher_id = int(request.form['teacher_id'])
        room_id = int(request.form['room_id'])
        week_type = request.form.get('week_type', 'Каждая')

        conflicts = check_conflicts(day, slot, group_id, teacher_id, room_id, week_type, exclude_id=les.id)
        if conflicts:
            for c in conflicts:
                flash(c, 'danger')
            return render_template('admin/lesson_form.html', lesson=les,
                                 subjects=Subject.query.all(),
                                 teachers=Teacher.query.all(),
                                 groups=Group.query.all(),
                                 rooms=Room.query.all(),
                                 lesson_types=LESSON_TYPES,
                                 week_types=WEEK_TYPES)

        les.subject_id = int(request.form['subject_id'])
        les.teacher_id = teacher_id
        les.group_id = group_id
        les.room_id = room_id
        les.day_of_week = day
        les.time_slot = slot
        les.lesson_type = request.form.get('lesson_type', 'Лекция')
        les.week_type = week_type
        db.session.commit()
        flash('Занятие обновлено', 'success')
        return redirect(url_for('admin_lessons'))

    return render_template('admin/lesson_form.html', lesson=les,
                         subjects=Subject.query.all(),
                         teachers=Teacher.query.all(),
                         groups=Group.query.all(),
                         rooms=Room.query.all(),
                         lesson_types=LESSON_TYPES,
                         week_types=WEEK_TYPES)


@app.route('/admin/lessons/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_lesson_delete(id):
    les = Lesson.query.get_or_404(id)
    db.session.delete(les)
    db.session.commit()
    flash('Занятие удалено', 'success')
    return redirect(url_for('admin_lessons'))


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/role/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_user_role(id):
    user = User.query.get_or_404(id)
    new_role = request.form.get('role')
    if new_role in ['admin', 'teacher', 'student']:
        user.role = new_role
        db.session.commit()
        flash('Роль пользователя изменена', 'success')
    return redirect(url_for('admin_users'))
