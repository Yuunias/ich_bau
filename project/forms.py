﻿# project forms

from django import forms
from project.models import Project, Task, TaskComment, Milestone, Member, TaskLink, TaskCheckList

from django.forms.widgets import HiddenInput

from commons.editors import DateTime_Field, TextEditor_Field

class ProjectForm(forms.ModelForm):
    description = TextEditor_Field(arg_required=False)

    class Meta:
        model = Project
        fields = ['fullname', 'private_flag', 'active_flag', 'description' ]

class MilestoneForm(forms.ModelForm):
    planned_at = DateTime_Field( False )
    finished_at = DateTime_Field( False )

    class Meta:
        model = Milestone
        fields = ['fullname', 'planned_at', 'finished_at' ]

from ich_bau.profiles.models import Profile, Get_Users_Profiles

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['member_profile', 'admin_flag' ]

    def __init__(self, *args, **kwargs):
        super(MemberForm, self).__init__(*args, **kwargs)
        # форма работает в режиме создания (смотрим 'initial')
        p = kwargs.pop('initial', None)['project']

        # отображать только свободных людей
        if not ( p is None):
            self.fields['member_profile'].queryset = Get_Users_Profiles().exclude( member_profile__project_id = p.id )

class TaskForm(forms.ModelForm):
    description = TextEditor_Field(arg_required=False)

    class Meta:
        model = Task
        fields = ['fullname', 'milestone', 'assignee', 'holder', 'important', 'description', ]

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        # форма работает в 2х режимах - создания (смотрим 'initial') и редактирования (смотрим 'instance') свойства.
        instance = kwargs.pop('instance', None)
        if (instance is None):
            pop = kwargs.pop('initial', None)
            p = pop['project']
        else:
            p = instance.project

        # отображать вехи и пользователей только этого проекта
        if not ( p is None):
            self.fields['milestone'].queryset = Milestone.objects.filter( project = p, finished_at__isnull = True )
            list = p.GetFullMemberProfiles()
            self.fields['holder'].queryset = list
            self.fields['assignee'].queryset = list

class TaskLinkedForm(forms.ModelForm):
    subtask=forms.ModelChoiceField( Task.objects, help_text="subtask", required=True )

    def __init__(self, *args, **kwargs):
        argmaintaskid = kwargs.pop('argmaintaskid', None)
        super(TaskLinkedForm, self).__init__(*args, **kwargs)

        if (argmaintaskid != "" ):
            main_task = Task.objects.get( id = argmaintaskid )
            self.fields['subtask'].queryset = main_task.project.Get_Tasks( True ).exclude(id=argmaintaskid).exclude( sub__maintask = argmaintaskid )

    class Meta:
        model = TaskLink
        fields = ['subtask']

class TaskCommentForm(forms.ModelForm):
    comment = TextEditor_Field()

    class Meta:
        model = TaskComment
        fields = ['comment' ]

class TaskCheckListForm(forms.ModelForm):
    class Meta:
        model = TaskCheckList
        fields = ['checkname', 'check_flag' ]