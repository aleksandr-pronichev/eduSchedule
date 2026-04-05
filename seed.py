from app import app, db
from app.models import User, Group, Subject, Teacher, Room, Lesson

def seed():
    db.drop_all()
    db.create_all()

    admin = User(username='admin', full_name='Администратор Системы', email='admin@university.ru', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    groups_data = [
        ('БИВ-11', 1, 'Информатика и вычислительная техника'),
        ('БИВ-12', 1, 'Информатика и вычислительная техника'),
        ('БИВ-21', 2, 'Информатика и вычислительная техника'),
        ('БИВ-22', 2, 'Информатика и вычислительная техника'),
        ('БПИ-11', 1, 'Программная инженерия'),
        ('БПИ-21', 2, 'Программная инженерия'),
    ]
    groups = []
    for name, course, faculty in groups_data:
        g = Group(name=name, course=course, faculty=faculty)
        db.session.add(g)
        groups.append(g)

    subjects_data = [
        'Математический анализ',
        'Линейная алгебра',
        'Программирование на Python',
        'Базы данных',
        'Web-разработка',
        'Операционные системы',
        'Компьютерные сети',
        'Физика',
        'Дискретная математика',
        'Алгоритмы и структуры данных',
    ]
    subjects = []
    for name in subjects_data:
        s = Subject(name=name)
        db.session.add(s)
        subjects.append(s)

    teachers_data = [
        ('Иванов Алексей Петрович', 'Кафедра высшей математики'),
        ('Петрова Мария Сергеевна', 'Кафедра программной инженерии'),
        ('Сидоров Дмитрий Николаевич', 'Кафедра информатики'),
        ('Козлова Анна Владимировна', 'Кафедра физики'),
        ('Морозов Игорь Александрович', 'Кафедра программной инженерии'),
        ('Новикова Елена Игоревна', 'Кафедра информатики'),
    ]
    teachers = []
    for full_name, dept in teachers_data:
        t = Teacher(full_name=full_name, department=dept)
        db.session.add(t)
        teachers.append(t)

    rooms_data = [
        ('101', 'Корпус А', 120, 'Лекционная'),
        ('205', 'Корпус А', 30, 'Практическая'),
        ('310', 'Корпус Б', 25, 'Компьютерный класс'),
        ('312', 'Корпус Б', 20, 'Лаборатория'),
        ('404', 'Корпус А', 80, 'Лекционная'),
        ('107', 'Корпус Б', 35, 'Практическая'),
    ]
    rooms = []
    for number, building, capacity, rtype in rooms_data:
        r = Room(number=number, building=building, capacity=capacity, room_type=rtype)
        db.session.add(r)
        rooms.append(r)

    db.session.flush()

    lessons_data = [
        (subjects[0], teachers[0], groups[0], rooms[0], 1, 1, 'Лекция', 'Каждая'),
        (subjects[0], teachers[0], groups[0], rooms[1], 1, 2, 'Практика', 'Каждая'),
        (subjects[2], teachers[1], groups[0], rooms[2], 2, 1, 'Лекция', 'Каждая'),
        (subjects[2], teachers[1], groups[0], rooms[2], 2, 2, 'Лабораторная', 'Чётная'),
        (subjects[1], teachers[0], groups[0], rooms[4], 3, 1, 'Лекция', 'Каждая'),
        (subjects[7], teachers[3], groups[0], rooms[0], 4, 1, 'Лекция', 'Каждая'),
        (subjects[7], teachers[3], groups[0], rooms[3], 4, 2, 'Лабораторная', 'Нечётная'),
        (subjects[8], teachers[5], groups[0], rooms[1], 5, 1, 'Практика', 'Каждая'),

        (subjects[0], teachers[0], groups[1], rooms[0], 1, 3, 'Лекция', 'Каждая'),
        (subjects[2], teachers[1], groups[1], rooms[2], 3, 2, 'Лекция', 'Каждая'),
        (subjects[2], teachers[1], groups[1], rooms[2], 3, 3, 'Лабораторная', 'Каждая'),
        (subjects[7], teachers[3], groups[1], rooms[4], 2, 3, 'Лекция', 'Каждая'),
        (subjects[1], teachers[0], groups[1], rooms[1], 4, 3, 'Практика', 'Каждая'),

        (subjects[3], teachers[2], groups[2], rooms[2], 1, 1, 'Лабораторная', 'Нечётная'),
        (subjects[4], teachers[4], groups[2], rooms[2], 1, 2, 'Лекция', 'Каждая'),
        (subjects[5], teachers[5], groups[2], rooms[4], 2, 1, 'Лекция', 'Каждая'),
        (subjects[5], teachers[5], groups[2], rooms[3], 2, 2, 'Лабораторная', 'Чётная'),
        (subjects[6], teachers[2], groups[2], rooms[0], 3, 1, 'Лекция', 'Каждая'),
        (subjects[9], teachers[4], groups[2], rooms[1], 4, 1, 'Практика', 'Каждая'),
        (subjects[9], teachers[4], groups[2], rooms[2], 4, 2, 'Лабораторная', 'Каждая'),

        (subjects[3], teachers[2], groups[4], rooms[2], 2, 3, 'Лабораторная', 'Каждая'),
        (subjects[4], teachers[4], groups[4], rooms[4], 3, 3, 'Лекция', 'Каждая'),
        (subjects[4], teachers[4], groups[4], rooms[2], 3, 4, 'Лабораторная', 'Нечётная'),
        (subjects[9], teachers[1], groups[4], rooms[1], 5, 2, 'Практика', 'Каждая'),
    ]

    for subj, teach, grp, room, day, slot, ltype, wtype in lessons_data:
        les = Lesson(
            subject_id=subj.id,
            teacher_id=teach.id,
            group_id=grp.id,
            room_id=room.id,
            day_of_week=day,
            time_slot=slot,
            lesson_type=ltype,
            week_type=wtype
        )
        db.session.add(les)

    student1 = User(username='student1', full_name='Петров Иван Сергеевич', email='student1@university.ru', role='student', group_id=groups[0].id)
    student1.set_password('student123')
    db.session.add(student1)

    student2 = User(username='student2', full_name='Сидорова Анна Павловна', email='student2@university.ru', role='student', group_id=groups[2].id)
    student2.set_password('student123')
    db.session.add(student2)

    db.session.commit()
    print('База данных заполнена тестовыми данными')
    print('Логин админа: admin / admin123')
    print('Логин студента: student1 / student123')


if __name__ == '__main__':
    with app.app_context():
        seed()
