"""
=============================================================================
  Flask To-Do API — Test Suite
  Баг: III VI IX  |  Тугулдур · Билгүүн · Мөнхжин · Мөнхбат
  Хэрэгсэл: Python unittest (суулгалт шаардахгүй стандарт сан)
  GitHub: github.com/III-VI-IX/software-quality-testing

  Windows: python -m unittest tests\test_api.py -v
  Linux  : python3 -m unittest tests/test_api.py -v
  Тайлан : python run_tests.py
=============================================================================
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


class BaseTestCase(unittest.TestCase):
    """Бүх тестийн суурь класс — тест бүрт тусдаа :memory: DB."""

    def setUp(self):
        self.app    = create_app({'TESTING': True, 'DATABASE': ':memory:'})
        self.client = self.app.test_client()

    def tearDown(self):
        self.app._db_conn.close()

    # ── Helper methods ──────────────────────────────────────────────────────
    def _register(self, email='test@test.com', password='Pass123!'):
        return self.client.post('/auth/register',
            data=json.dumps({'email': email, 'password': password}),
            content_type='application/json')

    def _login(self, email='test@test.com', password='Pass123!'):
        return self.client.post('/auth/login',
            data=json.dumps({'email': email, 'password': password}),
            content_type='application/json')

    def _token(self, email='u@example.com', password='Pass123!'):
        self._register(email, password)
        return json.loads(self._login(email, password).data)['token']

    def _auth(self, token):
        return {'Authorization': f'Bearer {token}'}

    def _task(self, token, title='Шинэ даалгавар'):
        return self.client.post('/tasks',
            data=json.dumps({'title': title}),
            content_type='application/json',
            headers=self._auth(token))


# =============================================================================
# TC-001 ~ TC-007  AUTH
# =============================================================================
class TestAuth(BaseTestCase):

    def test_TC001_register_success(self):
        """TC-001: Хэрэглэгч амжилттай бүртгүүлэх → 201 Created"""
        res  = self._register('new@test.com', 'Pass123!')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'new@test.com')

    def test_TC002_register_duplicate_email(self):
        """TC-002: Давхардсан имэйлээр бүртгүүлэх → 409 Conflict"""
        self._register('dup@test.com', 'Pass123!')
        res = self._register('dup@test.com', 'Other999!')
        self.assertEqual(res.status_code, 409)
        self.assertIn('error', json.loads(res.data))

    def test_TC003_register_missing_fields(self):
        """TC-003: Хоосон талбараар бүртгүүлэх → 400 Bad Request"""
        res = self.client.post('/auth/register',
            data=json.dumps({'email': ''}),
            content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_TC004_register_short_password(self):
        """TC-004: Богино нууц үг (< 6 тэмдэгт) → 400 Bad Request"""
        res = self._register('short@test.com', '123')
        self.assertEqual(res.status_code, 400)

    def test_TC005_login_success(self):
        """TC-005: Зөв мэдээллээр нэвтрэх → 200 OK + JWT токен"""
        self._register('login@test.com', 'Pass123!')
        res  = self._login('login@test.com', 'Pass123!')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertIn('token', data)
        self.assertGreater(len(data['token']), 20)

    def test_TC006_login_wrong_password(self):
        """TC-006: Буруу нууц үгээр нэвтрэх → 401 Unauthorized"""
        self._register('wp@test.com', 'CorrectPass1!')
        res = self._login('wp@test.com', 'WrongPass99!')
        self.assertEqual(res.status_code, 401)

    def test_TC007_login_nonexistent_user(self):
        """TC-007: Бүртгэлгүй хэрэглэгч → 401 Unauthorized"""
        res = self._login('nobody@test.com', 'Pass123!')
        self.assertEqual(res.status_code, 401)


# =============================================================================
# TC-008 ~ TC-017  TASK CRUD
# =============================================================================
class TestTasks(BaseTestCase):

    def test_TC008_get_tasks_with_token(self):
        """TC-008: Токентой GET /tasks → 200 OK + JSON array"""
        token = self._token()
        res   = self.client.get('/tasks', headers=self._auth(token))
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(json.loads(res.data), list)

    def test_TC009_get_tasks_without_token(self):
        """TC-009: Токенгүйгээр GET /tasks → 401 Unauthorized"""
        res = self.client.get('/tasks')
        self.assertEqual(res.status_code, 401)

    def test_TC010_create_task_success(self):
        """TC-010: Шинэ даалгавар амжилттай үүсгэх → 201 Created"""
        token = self._token()
        res   = self._task(token, 'Дипломын ажил бичих')
        data  = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(data['title'], 'Дипломын ажил бичих')
        self.assertFalse(bool(data['done']))
        self.assertIn('id', data)

    def test_TC011_create_task_empty_title(self):
        """TC-011: Хоосон title-тэй даалгавар → 400 Bad Request"""
        token = self._token()
        res   = self._task(token, '')
        self.assertEqual(res.status_code, 400)

    def test_TC012_create_task_whitespace_title(self):
        """TC-012: Зөвхөн хоосон зай агуулсан title → 400 Bad Request"""
        token = self._token()
        res   = self._task(token, '   ')
        self.assertEqual(res.status_code, 400)

    def test_TC013_update_task_title(self):
        """TC-013: Даалгаврын гарчгийг засах → 200 OK + шинэ гарчиг"""
        token = self._token()
        tid   = json.loads(self._task(token, 'Хуучин нэр').data)['id']
        res   = self.client.put(f'/tasks/{tid}',
            data=json.dumps({'title': 'Шинэ нэр'}),
            content_type='application/json',
            headers=self._auth(token))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['title'], 'Шинэ нэр')

    def test_TC014_mark_task_done(self):
        """TC-014: Даалгаврыг done=True болгох → 200 OK"""
        token = self._token()
        tid   = json.loads(self._task(token, 'Дуусгах ажил').data)['id']
        res   = self.client.put(f'/tasks/{tid}',
            data=json.dumps({'done': True}),
            content_type='application/json',
            headers=self._auth(token))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(bool(json.loads(res.data)['done']))

    def test_TC015_delete_task_success(self):
        """TC-015: Даалгавар амжилттай устгах → 200 OK"""
        token = self._token()
        tid   = json.loads(self._task(token, 'Устгах ажил').data)['id']
        res   = self.client.delete(f'/tasks/{tid}', headers=self._auth(token))
        self.assertEqual(res.status_code, 200)
        # Устгагдсаныг шалгах
        chk = self.client.get(f'/tasks/{tid}', headers=self._auth(token))
        self.assertEqual(chk.status_code, 404)

    def test_TC016_delete_nonexistent_task(self):
        """TC-016: Байхгүй даалгавар устгах → 404 Not Found"""
        token = self._token()
        res   = self.client.delete('/tasks/9999', headers=self._auth(token))
        self.assertEqual(res.status_code, 404)

    def test_TC017_get_single_task(self):
        """TC-017: Тодорхой нэг даалгавар авах → 200 OK + зөв өгөгдөл"""
        token = self._token()
        tid   = json.loads(self._task(token, 'Ганцаарчилсан ажил').data)['id']
        res   = self.client.get(f'/tasks/{tid}', headers=self._auth(token))
        data  = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['id'], tid)
        self.assertEqual(data['title'], 'Ганцаарчилсан ажил')


# =============================================================================
# TC-018 ~ TC-020  ISOLATION & SECURITY
# =============================================================================
class TestIsolation(BaseTestCase):

    def test_TC018_user_cannot_see_others_tasks(self):
        """TC-018: Хэрэглэгч нөгөөгийн даалгаврыг харж чадахгүй"""
        tok1 = self._token('user1@test.com', 'Pass1111!')
        self._task(tok1, 'Хэрэглэгч 1-ийн нууц ажил')
        tok2 = self._token('user2@test.com', 'Pass2222!')
        res  = self.client.get('/tasks', headers=self._auth(tok2))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(json.loads(res.data)), 0)

    def test_TC019_user_cannot_delete_others_task(self):
        """TC-019: Нөгөөгийн даалгаврыг устгах оролдлого → 404"""
        tok1 = self._token('owner@test.com', 'Pass1111!')
        tid  = json.loads(self._task(tok1, 'Эзэмшигчийн ажил').data)['id']
        tok2 = self._token('attacker@test.com', 'Pass2222!')
        res  = self.client.delete(f'/tasks/{tid}', headers=self._auth(tok2))
        self.assertEqual(res.status_code, 404)

    def test_TC020_invalid_token_rejected(self):
        """TC-020: Хуурамч токен → 401 Unauthorized"""
        res = self.client.get('/tasks',
            headers={'Authorization': 'Bearer totally.fake.token'})
        self.assertEqual(res.status_code, 401)


if __name__ == '__main__':
    unittest.main(verbosity=2)
