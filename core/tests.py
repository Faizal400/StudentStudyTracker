from django.test import TestCase
from django.contrib.auth.models import User
from .models import Subject, Module, SubModule, StudySession
import json

class StudyTrackerTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="usera", password="testpass123")
        self.user_b = User.objects.create_user(username="userb", password="testpass123")

        self.subject = Subject.objects.create(user=self.user_a, name="Subject A")
        self.module = Module.objects.create(subject=self.subject, name="Module A")
        self.submodule = SubModule.objects.create(module=self.module, name="SubModule A")

        self.other_subject = Subject.objects.create(user=self.user_b, name="Subject B")

    def test_unauthenticated_cannot_add_subject(self):
        res = self.client.post("/api/subjects/add/",
            content_type="application/json",
            data={"name": "Hacked", "dataType": "subject", "ParentId": ""}
        )
        self.assertEqual(res.status_code, 302)

    def test_user_a_add_subject(self):
        self.client.login(username="usera", password="testpass123")
        res = self.client.post("/api/subjects/add/",
            content_type="application/json",
            data={"name": "New Subject", "dataType": "subject", "ParentId": ""}
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertTrue(data["ok"])

    def test_duplicate_subject_returns_not_created(self):
        self.client.login(username="usera", password="testpass123")
        res = self.client.post("/api/subjects/add/",
            content_type="application/json",
            data={"name": "Subject A", "dataType": "subject", "ParentId": ""}
        )
        data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["ok"])
        self.assertFalse(data["created"])

    def test_user_a_cannot_delete_user_b_subject(self):
        self.client.login(username="usera", password="testpass123")
        res = self.client.post("/api/subjects/delete/",
            content_type="application/json",
            data={"id": self.other_subject.id, "type": "subject"}
        )
        data = json.loads(res.content)
        self.assertEqual(res.status_code, 404)
        self.assertFalse(data["ok"])
        self.assertTrue(Subject.objects.filter(id=self.other_subject.id).exists())

    def test_session_saves_correct_duration(self):
        self.client.login(username="usera", password="testpass123")
        res = self.client.post("/api/sessions/create/",
            content_type="application/json",
            data={
                "item_id": self.subject.id,
                "session_type": "subject",
                "duration_seconds": 300
            }
        )
        data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["ok"])
        session = StudySession.objects.get(id=data["session_id"])
        self.assertEqual(session.duration_seconds, 300)

    def test_session_invalid_duration(self):
        self.client.login(username="usera", password="testpass123")
        res = self.client.post("/api/sessions/create/",
            content_type="application/json",
            data={
                "item_id": self.subject.id,
                "session_type": "subject",
                "duration_seconds": -50
            }
        )
        data = json.loads(res.content)
        self.assertEqual(res.status_code, 400)
        self.assertFalse(data["ok"])

    def test_cross_user_session(self):
        self.client.login(username="usera", password="testpass123")
        res = self.client.post("/api/sessions/create/",
            content_type="application/json",
            data={
                "item_id": self.other_subject.id,
                "session_type": "subject",
                "duration_seconds": 360
            }
        )
        data = json.loads(res.content)
        self.assertEqual(res.status_code, 400)
        self.assertFalse(data["ok"])
        self.assertFalse(StudySession.objects.filter(subject=self.other_subject).exists())

    def test_mixing_user_data(self):
        self.client.login(username="userb", password="testpass123")
        res = self.client.get("/")
        userSubjects = res.context["subjects"]
        self.assertIn(self.other_subject, userSubjects)
        self.assertNotIn(self.subject, userSubjects)


