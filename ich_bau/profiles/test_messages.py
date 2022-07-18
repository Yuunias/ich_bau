from django.contrib.auth.models import User
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.db import connection, connections
from django.urls import reverse_lazy
from django.db import models


from .views import *
from .models import *
from .messages import *
from .notification_helper import *

from django.conf import settings
from django.core import mail

TEST_USER_NAME_1 = 'USER_1'
TEST_USER_NAME_2 = 'USER_2'
TEST_USER_NAME_3 = 'USER_3'
TEST_USER_NAME = 'USER'
TEST_USER_PW = 'USER_PW'
TEST_USER_EMAIL = 'email@mail.mail'

SERVER_EMAIL = 'server@mail.mail'

class Message_Test(TestCase):
    def test_Encode_Decode_Project_MSG(self):
        s = project_msg2json_str( MSG_NOTIFY_TYPE_PROJECT_CHANGED_ID, arg_project_name = 'some project' )
        self.assertEqual( s, '{"msg_type": 20, "project_name": "some project"}' )
        self.assertEqual( decode_json2msg(s), "Changes in the 'some project' project." )

    def test_decode_json2msg_Fail(self):
        self.assertEqual( decode_json2msg( '-' ), None )

    def test_decode_json2title_Fail(self):
        self.assertEqual( decode_json2title( '-' ), None )

    def test_decode_json_some_task(self):
        s = '{"msg_type": 50, "project_name": "test", "task_name": "some task"}'
        self.assertEqual( decode_json2title( s ), 'some task' )

    def test_decode_json2title_is_a_part_of_decode_json2msg_some_project(self):
        s = '{"msg_type": 20, "project_name": "some project"}'
        self.assertIn( decode_json2title( s ), decode_json2msg( s ) )

    def test_decode_json2title_is_a_part_of_decode_json2msg_some_milestone(self):
        s = '{"msg_type": 30, "project_name": "some project", "milestone_name": "some milestone"}'
        self.assertIn( decode_json2title( s ), decode_json2msg( s ) )

    def test_decode_json2title_is_a_part_of_decode_json2msg_some_task(self):
        s = '{"msg_type": 50, "project_name": "test", "task_name": "some task"}'
        self.assertIn( decode_json2title( s ), decode_json2msg( s ) )

    def test_Encode_Project_MSG_Fail(self):
        s = project_msg2json_str( -1, arg_project_name = '*' )
        self.assertFalse( s )

    def test_Get_Users_Profiles(self):
        self.assertEqual( Get_Users_Profiles().count(), 0 )
        test_user = User.objects.create_user( username = TEST_USER_NAME, password = TEST_USER_PW )
        self.assertEqual( Get_Users_Profiles().count(), 1 )

    def test_Send_Notification_Wrong_Arg_MSG_TYPE(self):
        test_user = User.objects.create_user( username = TEST_USER_NAME, password = TEST_USER_PW )
        self.assertEqual( GetUserNoticationsQ( test_user, True).count(), 0 )

        user_type = ContentType.objects.get(app_label='auth', model='user')

        with self.assertRaises(Exception):
            Send_Notification( test_user, test_user, user_type, 1, -1, 'Arg_MsgTxt', 'Arg_Url' ) # try to raise 'Wrong message type'

    def test_Send_Notification(self):
        test_user = User.objects.create_user( username = TEST_USER_NAME, password = TEST_USER_PW )
        self.assertEqual( GetUserNoticationsQ( test_user, True).count(), 0 )

        user_type = ContentType.objects.get(app_label='auth', model='user')

        Send_Notification( test_user, test_user, user_type, 1, MSG_NOTIFY_TYPE_USER_WANT_JOIN_ID, 'Arg_MsgTxt', 'Arg_Url' )
        self.assertEqual( GetUserNoticationsQ( test_user, True).count(), 1 )

    
    def test_Send_Notification_Check_Email_ASK_ACCEPT(self):

        mail.outbox = []
        self.assertEqual(len(mail.outbox), 0)

        settings.EMAIL_HOST_USER = SERVER_EMAIL

        test_user = User.objects.create_user( username = TEST_USER_NAME, password = TEST_USER_PW, email = TEST_USER_EMAIL )
        self.assertEqual( GetUserNoticationsQ( test_user, True).count(), 0 )

        user_type = ContentType.objects.get(app_label='auth', model='user')

        msg_str = project_msg2json_str( MSG_NOTIFY_TYPE_ASK_ACCEPT_ID, arg_project_name = 'test' )
        self.assertEqual( msg_str, '{"msg_type": 1, "project_name": "test"}' )

        Send_Notification( test_user, test_user, user_type, 1, MSG_NOTIFY_TYPE_ASK_ACCEPT_ID, msg_str, 'Arg_Url' )
        self.assertEqual( GetUserNoticationsQ( test_user, True).count(), 1 )
        self.assertEqual(len(mail.outbox), 1)

        e_letter = mail.outbox[0]

        self.assertEqual( e_letter.from_email, SERVER_EMAIL )
        self.assertIn( TEST_USER_EMAIL, e_letter.to )
        self.assertEqual( e_letter.subject, 'You are asked to accept the membership of \'test\' project team!' )

        self.assertIn( 'You are asked to accept the membership of &#39;test&#39; project team!', e_letter.body )





















    def test_Delete_Notification(self):
        test_user_1 = User.objects.create_user( username = TEST_USER_NAME_1, password = TEST_USER_PW )
        test_user_2 = User.objects.create_user( username = TEST_USER_NAME_2, password = TEST_USER_PW )
        test_user_3 = User.objects.create_user( username = TEST_USER_NAME_3, password = TEST_USER_PW )
        user_type = ContentType.objects.get(app_label='auth', model='user')

        self.assertEqual( GetUserNoticationsQ( test_user_1, True).count(), 0 )
        self.assertEqual( GetUserNoticationsQ( test_user_2, True).count(), 0 )
        self.assertEqual( GetUserNoticationsQ( test_user_3, True).count(), 0 )

        Send_Notification( test_user_1, test_user_2, user_type, 1, MSG_NOTIFY_TYPE_USER_WANT_JOIN_ID, 'Arg_MsgTxt', 'Arg_Url' )
        Send_Notification( test_user_3, test_user_2, user_type, 1, MSG_NOTIFY_TYPE_USER_WANT_JOIN_ID, 'Arg_MsgTxt', 'Arg_Url' )
        Send_Notification( test_user_2, test_user_1, user_type, 1, MSG_NOTIFY_TYPE_USER_WANT_JOIN_ID, 'Arg_MsgTxt', 'Arg_Url' )
        Send_Notification( test_user_3, test_user_1, user_type, 1, MSG_NOTIFY_TYPE_USER_WANT_JOIN_ID, 'Arg_MsgTxt', 'Arg_Url' )

        self.assertEqual( GetUserNoticationsQ( test_user_1, True).count(), 2 )

        Notification.objects.filter( sender_user=test_user_2).update(readed_at=timezone.now())
        Notification.objects.filter( sender_user=test_user_1).update(readed_at=timezone.now())

        self.assertEqual( GetUserNoticationsQ( test_user_2, False).count(), 1 )
        self.assertEqual( GetUserNoticationsQ( test_user_2, True).count(), 1 )  
        self.assertEqual( GetUserNoticationsQ( test_user_1, True).count(), 1 )
        self.assertEqual( GetUserNoticationsQ( test_user_1, False).count(), 1 )

        c_a=Client()
        c_a.login(username = TEST_USER_NAME_1, password = TEST_USER_PW)
        c_a.get("/notifications/read/read_del/")

        self.assertEqual( GetUserNoticationsQ( test_user_1, True).count(), 1 )
        self.assertEqual( GetUserNoticationsQ( test_user_1, False).count(), 0 )
        self.assertEqual( GetUserNoticationsQ( test_user_2, False).count(), 1 )
        self.assertEqual( GetUserNoticationsQ( test_user_2, True).count(), 1 )






    def test_Send_Notification_Check_Email_TASK_ASSIGN(self):

        mail.outbox = []
        self.assertEqual(len(mail.outbox), 0)

        settings.EMAIL_HOST_USER = SERVER_EMAIL

        test_user = User.objects.create_user( username = TEST_USER_NAME, password = TEST_USER_PW, email = TEST_USER_EMAIL )
        self.assertEqual( GetUserNoticationsQ( test_user, True).count(), 0 )

        user_type = ContentType.objects.get(app_label='auth', model='user')

        msg_str = project_msg2json_str( MSG_NOTIFY_TYPE_PROJECT_TASK_ASSIGNED_ID, arg_project_name = 'test', arg_task_name = 'test_task' )
        self.assertEqual( msg_str, '{"msg_type": 45, "project_name": "test", "task_name": "test_task"}' )

        Send_Notification( test_user, test_user, user_type, 1, MSG_NOTIFY_TYPE_PROJECT_TASK_ASSIGNED_ID, msg_str, 'Arg_Url' )
        self.assertEqual( GetUserNoticationsQ( test_user, True).count(), 1 )
        self.assertEqual(len(mail.outbox), 1)

        e_letter = mail.outbox[0]

        self.assertEqual( e_letter.from_email, SERVER_EMAIL )
        self.assertIn( TEST_USER_EMAIL, e_letter.to )
        self.assertEqual( e_letter.subject, 'You are assigned at a \'test_task\' task of \'test\' project.' )

        self.assertIn( 'You are assigned at a &#39;test_task&#39; task of &#39;test&#39; project', e_letter.body )
