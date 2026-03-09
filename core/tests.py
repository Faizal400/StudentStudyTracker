from django.test import TestCase

from django.test import TestCase
from django.contrib.auth.models import User
from .models import Subject, Module, SubModule, StudySession
import json

class StudyTrackerTests(TestCase):
    def setUp(self):
        # Create two users
        self.user_a = User.objects.create_user(username="usera", password="testpass123")
        self.user_b = User.objects.create_user(username="userb", password="testpass123")

        # Create User A's data
        self.subject = Subject.objects.create(user=self.user_a, name="Subject A")
        self.module = Module.objects.create(subject=self.subject, name="Module A")
        self.submodule = SubModule.objects.create(module=self.module, name="SubModule A")

        # Create User B's data
        self.other_subject = Subject.objects.create(user=self.user_b, name="Subject B")

        def test_unauthenticated_cannot_add_subject(self):
            res = self.client.post("/api/subjects/add/", 
                content_type="application/json",
                data={"name": "Hacked", "dataType": "subject", "ParentId": ""}
            )
            self.assertEqual(res.status_code, 302)  # 302 = redirect to login
        
        def test_user_a_add_subject(self):
            self.client.login(username="usera", password="testpass123")
            res = self.client.post("/api/subjects/add/", 
                content_type="application/json",
                data={"name": "New Subject", "dataType": "subject", "ParentId": ""}
            )
            self.assertEqual(res.status_code, 200)
            data = json.loads(res.content)
            self.assertTrue(data["ok"]) # check response indicates success
            
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
            session_id = data["session_id"]
            session = StudySession.objects.get(id=session_id)
            self.assertEqual(session.duration_seconds, 300)