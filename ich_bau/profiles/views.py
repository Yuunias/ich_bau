from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, ListView

from django.contrib import messages

from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext

from account.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin

from .forms import ProfileForm, ContactProfileForm, Profile_AffiliationForm
from .models import *
from account.decorators import login_required
from reversion.models import Version
from django.http import HttpResponseRedirect, Http404
from project.models import Get_User_Tasks, Get_Profile_Tasks, GetAvailableProjectList

class ProfileEditView(LoginRequiredMixin, UpdateView):

    form_class = ProfileForm
    model = Profile

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return reverse_lazy( my_profile_view )

    def form_valid(self, form):
        response = super(ProfileEditView, self).form_valid(form)
        messages.success(self.request, "You successfully updated your profile.")
        return response

class ProfileDetailView(DetailView):

    model = Profile
    slug_url_kwarg = "profile_id"
    slug_field = "id"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        Current_User_Profile = False
        context = super(ProfileDetailView, self).get_context_data(**kwargs)
        current_profile = self.get_object()
        profile_is_managed = False
        view_projects_and_tasks_header = ''
        profile_tasks = None

        # affiliated profiles
        context['main_profiles'] = current_profile.main_profiles()
        context['sub_profiles'] =  current_profile.sub_profiles()

        if ( current_profile.profile_type == PROFILE_TYPE_USER ) and ( not( current_profile.user is None ) ):
            context['managed_profiles'] = Profile_Manage_User.objects.filter( manager_user = current_profile.user )
            context['managed_by_user'] = Profile_Manage_User.objects.filter( managed_profile = current_profile )

            if self.request.user == current_profile.user:
                # ���� ������� ���� ����������� �������
                context['user_repo_pw'] = current_profile.repo_pw
                Current_User_Profile = True
                view_projects_and_tasks_header = 'Task assigned to you'
                profile_tasks = Get_User_Tasks( self.request.user )
        if not profile_tasks:
            profile_is_managed = Is_User_Manager( self.request.user, current_profile )
            if profile_is_managed:
                profile_tasks = Get_User_Tasks( current_profile.user )
                view_projects_and_tasks_header = 'Task assigned to managed profiles'
            else:
                #if ( current_profile.profile_type in PROFILE_TYPE_FOR_TASK ):
                profile_tasks = Get_Profile_Tasks( current_profile ).filter( project__in = GetAvailableProjectList( self.request.user ) )
                view_projects_and_tasks_header = 'Task assigned to profile (for projects available for you)'

        context['current_user_profile'] = Current_User_Profile
        context['view_projects_and_tasks_header'] = view_projects_and_tasks_header
        context['profile_tasks'] = profile_tasks

        return context

@login_required
def my_profile_view(request):
    return redirect( 'profiles_detail', pk = request.user.profile.id )

class ProfileListView(ListView):

    model = Profile
    context_object_name = "profiles"

    def get_context_data(self, **kwargs):
        context = super(ProfileListView, self).get_context_data(**kwargs)
        # check if user has permission to create profile (or super user)
        context[ 'can_add_profile' ] = self.request.user.has_perm('profiles.add_profile')
        return context

class ProfileCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Profile
    form_class = ContactProfileForm
    permission_required = 'profiles.add_profile'
    raise_exception = True

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ContactProfileForm

class ProfileCreateSubView(LoginRequiredMixin, CreateView):
    model = Profile_Affiliation
    form_class = Profile_AffiliationForm

    def get_initial(self):
        try:
            self.mp = get_object_or_404( Profile, pk = self.kwargs['pk'])
            return { 'main_profile': self.mp, }
        except:
            Http404()

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.main_profile = self.mp
        self.object.save()

        messages.success(self.request, "You successfully add the affiliation!")
        return HttpResponseRedirect( self.object.main_profile.get_absolute_url() )

from .models import Notification, GetUserNoticationsQ

@login_required
def notifications_view_prepare(request, arg_new):
    context = RequestContext(request)
    u = request.user
    if u is None:
        raise Http404

    OLD_NOTIFICATIONS_VIEW_LIMIT = 20
    notifications_q = GetUserNoticationsQ( u, arg_new )
    if arg_new:
        notifications = notifications_q.order_by('sender_user')
    else:
        notifications = notifications_q[:OLD_NOTIFICATIONS_VIEW_LIMIT]

    context_dict = { 'notifications' : notifications, 'filter_new' : arg_new, 'OLD_NOTIFICATIONS_VIEW_LIMIT' : OLD_NOTIFICATIONS_VIEW_LIMIT }
    return render( request, 'profiles/notifications.html', context_dict )

@login_required
def notifications_view_unread(request):
    return notifications_view_prepare( request, True )

@login_required
def notifications_view_read(request):
    return notifications_view_prepare( request, False )

@login_required
def notification_read( request, notification_id ):
    from django.http import HttpResponse
    # � ������ ����������� ��������� �������� ���
    n = get_object_or_404( Notification, pk=notification_id )
    # ��������, ��� ���� - ������� �����������
    if n.reciever_user == request.user:
        if n.get_unreaded:
            n.mark_readed()

        if ( n.msg_url is None ) or ( n.msg_url == '' ):
            return redirect( 'unread_notifications_view' )
        else:
            return redirect( n.msg_url )
    else:
        raise Http404()
