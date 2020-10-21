from django.core.management.base import BaseCommand

from django.utils import timezone

from commons.utils import get_full_site_url
from project.models import Task, Get_User_Tasks, Get_Profile_ScheduleItem_This_Week, Get_Profile_ScheduleItem, ScheduleItem_Task, Get_UnAccepted
from ich_bau.profiles.models import GetUserNoticationsQ
from django.core.mail import send_mail
from django.conf import settings

from django.template.loader import render_to_string

from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'do schedule letters sending'

    def handle(self, *args, **options):

        if not settings.EMAIL_HOST_USER:
            print( "No EMAIL_HOST_USER, can't send mails" )
            return

        users = User.objects.filter( is_active = True )

        for u in users:
            # if users have a mail's
            if ( u.id == 3 ) and u.email:

                schedule = None
                scheduled_task_empty = True
                tasks = None

                # ����� ���
                unaccepted_projects = Get_UnAccepted( u )

                notifications_count = GetUserNoticationsQ(u, True).count()

                # if user has the work schedule item - use it
                schedules = Get_Profile_ScheduleItem_This_Week( Get_Profile_ScheduleItem( u.profile ) )
                if schedules.exists():
                    schedule = schedules.first()
                    tasks = Task.objects.filter( scheduledtask__schedule_item = schedule )
                    scheduled_task_empty = ( tasks.count() == 0 )

                if scheduled_task_empty:
                    tasks = Get_User_Tasks( u )

                context_dict = { 'user' : u,
                                 'current_domain' : get_full_site_url(),
                                 'unaccepted_projects' : unaccepted_projects,
                                 'schedule' : schedule,
                                 'scheduled_task_empty' : scheduled_task_empty,
                                 'tasks' : tasks,
                                 'notifications_count' : notifications_count,
                                 }

                html_message_text = render_to_string( 'project/email_tasks_digest.txt', context_dict )

                try:
                    send_mail( 'Tasks',
                               html_message_text,
                               settings.EMAIL_HOST_USER,
                               [u.email],
                               fail_silently=False,
                               html_message=html_message_text
                             )
                except:
                    print( 'Fail to send email' )