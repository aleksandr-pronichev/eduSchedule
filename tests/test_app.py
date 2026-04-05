import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from app.models import User, Group, Subject, Teacher, Room, Lesson


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        self._create_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_test_data(self):
        admin = User(username='admin', full_name='Admin', email='admin@test.ru', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        group = Group(name='ТЕСТ-11', course=1, faculty='Тестовый факультет')
        db.session.add(group)

        subject = Subject(name='Тестовая дисциплина')
        db.session.add(subject)

        teacher = Teacher(full_name='Тестов Тест Тестович', department='Тестовая кафедра')
        db.session.add(teacher)

        room = Room(number='999', building='Корпус Т', capacity=30, room_type='Лекционная')
        db.session.add(room)

        db.session.flush()

        student = User(username='student', full_name='Студент Тестовый', email='student@test.ru', role='student', group_id=group.id)
        student.set_password('student123')
        db.session.add(student)

        lesson = Lesson(subject_id=subject.id, teacher_id=teacher.id, group_id=group.id,
                       room_id=room.id, day_of_week=1, time_slot=1,
                       lesson_type='Лекция', week_type='Каждая')
        db.session.add(lesson)
        db.session.commit()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username, password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)


class TestIndexPage(BaseTestCase):
    def test_index_loads(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_index_contains_title(self):
        resp = self.client.get('/')
        self.assertIn('EduSchedule'.encode(), resp.data)


class TestAuth(BaseTestCase):
    def test_login_page_loads(self):
        resp = self.client.get('/login')
        self.assertEqual(resp.status_code, 200)

    def test_login_success(self):
        resp = self.login('admin', 'admin123')
        self.assertEqual(resp.status_code, 200)

    def test_login_wrong_password(self):
        resp = self.login('admin', 'wrongpass')
        self.assertIn('Неверное'.encode('utf-8'), resp.data)

    def test_register_page_loads(self):
        resp = self.client.get('/register')
        self.assertEqual(resp.status_code, 200)

    def test_register_new_user(self):
        resp = self.client.post('/register', data=dict(
            username='newuser',
            email='new@test.ru',
            full_name='Новый Пользователь',
            password='pass123',
            password2='pass123',
            group_id=''
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)

    def test_register_password_mismatch(self):
        resp = self.client.post('/register', data=dict(
            username='newuser2',
            email='new2@test.ru',
            full_name='Тест',
            password='pass1',
            password2='pass2',
            group_id=''
        ), follow_redirects=True)
        self.assertIn('не совпадают'.encode('utf-8'), resp.data)

    def test_register_duplicate_username(self):
        resp = self.client.post('/register', data=dict(
            username='admin',
            email='dup@test.ru',
            full_name='Дубликат',
            password='pass123',
            password2='pass123',
            group_id=''
        ), follow_redirects=True)
        self.assertIn('уже существует'.encode('utf-8'), resp.data)

    def test_logout(self):
        self.login('admin', 'admin123')
        resp = self.logout()
        self.assertEqual(resp.status_code, 200)


class TestSchedule(BaseTestCase):
    def test_schedule_page_loads(self):
        resp = self.client.get('/schedule')
        self.assertEqual(resp.status_code, 200)

    def test_schedule_with_group_filter(self):
        with app.app_context():
            group = Group.query.first()
        resp = self.client.get(f'/schedule?group_id={group.id}')
        self.assertEqual(resp.status_code, 200)

    def test_api_schedule(self):
        resp = self.client.get('/api/schedule')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_api_schedule_filter(self):
        with app.app_context():
            group = Group.query.first()
        resp = self.client.get(f'/api/schedule?group_id={group.id}')
        data = resp.get_json()
        self.assertIsInstance(data, list)


class TestProfile(BaseTestCase):
    def test_profile_requires_login(self):
        resp = self.client.get('/profile', follow_redirects=True)
        self.assertIn('войти'.encode('utf-8'), resp.data)

    def test_profile_loads_for_student(self):
        self.login('student', 'student123')
        resp = self.client.get('/profile')
        self.assertEqual(resp.status_code, 200)


class TestAdmin(BaseTestCase):
    def test_admin_dashboard_requires_admin(self):
        self.login('student', 'student123')
        resp = self.client.get('/admin', follow_redirects=True)
        self.assertIn('Доступ'.encode('utf-8'), resp.data)

    def test_admin_dashboard_loads(self):
        self.login('admin', 'admin123')
        resp = self.client.get('/admin')
        self.assertEqual(resp.status_code, 200)

    def test_admin_groups_page(self):
        self.login('admin', 'admin123')
        resp = self.client.get('/admin/groups')
        self.assertEqual(resp.status_code, 200)

    def test_admin_add_group(self):
        self.login('admin', 'admin123')
        resp = self.client.post('/admin/groups/add', data=dict(
            name='НОВАЯ-11',
            course=1,
            faculty='Новый факультет'
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        with app.app_context():
            g = Group.query.filter_by(name='НОВАЯ-11').first()
            self.assertIsNotNone(g)

    def test_admin_edit_group(self):
        self.login('admin', 'admin123')
        with app.app_context():
            group = Group.query.first()
            gid = group.id
        resp = self.client.post(f'/admin/groups/edit/{gid}', data=dict(
            name='ИЗМЕНЕНА-11',
            course=2,
            faculty='Другой факультет'
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_admin_subjects_page(self):
        self.login('admin', 'admin123')
        resp = self.client.get('/admin/subjects')
        self.assertEqual(resp.status_code, 200)

    def test_admin_add_subject(self):
        self.login('admin', 'admin123')
        resp = self.client.post('/admin/subjects/add', data=dict(
            name='Новая дисциплина'
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_admin_teachers_page(self):
        self.login('admin', 'admin123')
        resp = self.client.get('/admin/teachers')
        self.assertEqual(resp.status_code, 200)

    def test_admin_rooms_page(self):
        self.login('admin', 'admin123')
        resp = self.client.get('/admin/rooms')
        self.assertEqual(resp.status_code, 200)

    def test_admin_lessons_page(self):
        self.login('admin', 'admin123')
        resp = self.client.get('/admin/lessons')
        self.assertEqual(resp.status_code, 200)

    def test_admin_users_page(self):
        self.login('admin', 'admin123')
        resp = self.client.get('/admin/users')
        self.assertEqual(resp.status_code, 200)

    def test_admin_add_lesson_conflict(self):
        self.login('admin', 'admin123')
        with app.app_context():
            lesson = Lesson.query.first()
            subj_id = lesson.subject_id
            teacher_id = lesson.teacher_id
            group_id = lesson.group_id
            room_id = lesson.room_id
        resp = self.client.post('/admin/lessons/add', data=dict(
            subject_id=subj_id,
            teacher_id=teacher_id,
            group_id=group_id,
            room_id=room_id,
            day_of_week=1,
            time_slot=1,
            lesson_type='Лекция',
            week_type='Каждая'
        ), follow_redirects=True)
        self.assertIn('уже'.encode('utf-8'), resp.data)

    def test_admin_delete_lesson(self):
        self.login('admin', 'admin123')
        with app.app_context():
            lesson = Lesson.query.first()
            lid = lesson.id
        resp = self.client.post(f'/admin/lessons/delete/{lid}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_admin_change_user_role(self):
        self.login('admin', 'admin123')
        with app.app_context():
            student = User.query.filter_by(username='student').first()
            sid = student.id
        resp = self.client.post(f'/admin/users/role/{sid}', data=dict(
            role='teacher'
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        with app.app_context():
            user = User.query.get(sid)
            self.assertEqual(user.role, 'teacher')


class TestErrors(BaseTestCase):
    def test_404(self):
        resp = self.client.get('/nonexistent')
        self.assertEqual(resp.status_code, 404)


if __name__ == '__main__':
    unittest.main()
