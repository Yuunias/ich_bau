from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, ListView

from django.contrib import messages

from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext

from account.mixins import LoginRequiredMixin

from .forms import ProfileForm, ContactProfileForm, Profile_AffiliationForm
from .models import *
from account.decorators import login_required
from reversion.models import Version
from django.http import HttpResponseRedirect, Http404
from project.models import Get_User_Tasks, Get_Profile_Tasks, GetAvailableProjectList, GetMemberedProjectList

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
        view_projects_and_tasks_header = None
        profile_tasks = None
        profile_projects = None

        # affiliated profiles
        context['main_profiles'] = current_profile.main_profiles()
        context['sub_profiles'] =  current_profile.sub_profiles()

        if ( current_profile.profile_type == PROFILE_TYPE_USER ) and ( not( current_profile.user is None ) ):
            context['managed_profiles'] = Profile_Manage_User.objects.filter( manager_user = current_profile.user )
            context['managed_by_user'] = Profile_Manage_User.objects.filter( managed_profile = current_profile )

            if self.request.user == current_profile.user:
                # þçåð ñìîòðèò ñâîé ñîáñòâåííûé ïðîôèëü
                context['user_repo_pw'] = current_profile.repo_pw
                Current_User_Profile = True
                view_projects_and_tasks_header = 'to_you'
                profile_tasks = Get_User_Tasks( self.request.user )
                profile_projects = GetMemberedProjectList( self.request.user )
        if not profile_tasks:
            if current_profile.could_has_task():
                profile_is_managed = Is_User_Manager( self.request.user, current_profile )
                if profile_is_managed:
                    profile_tasks = Get_User_Tasks( current_profile.user )

                    if current_profile.has_account:
                        profile_projects = GetMemberedProjectList( current_profile.user )

                    view_projects_and_tasks_header = 'to_managed'
                else:
                    profile_tasks = Get_Profile_Tasks( current_profile ).filter( project__in = GetAvailableProjectList( self.request.user ) )

                    if current_profile.has_account:
                        profile_projects = GetMemberedProjectList( current_profile.user ).distinct() & GetAvailableProjectList( self.request.user )

                    view_projects_and_tasks_header = 'to_profile'

        context['current_user_profile'] = Current_User_Profile
        context['view_projects_and_tasks_header'] = view_projects_and_tasks_header
        context['profile_tasks'] = profile_tasks
        context['profile_projects'] = profile_projects

        return context

@login_required
def my_profile_view(request):
    return redirect( 'profiles_detail', pk = request.user.profile.id )

# äîñòóï - äëÿ àâòîðèçîâàííûõ
class ProfileListView(LoginRequiredMixin, ListView):

    model = Profile
    context_object_name = "profiles"

    def get_context_data(self, **kwargs):
        context = super(ProfileListView, self).get_context_data(**kwargs)
        context[ 'can_add_profile' ] = self.request.user.is_authenticated
        return context

class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = Profile
    form_class = ContactProfileForm

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ContactProfileForm

class ProfileCreateSubView(LoginRequiredMixin, CreateView):
    model = Profile_Affiliation
    form_class = Profile_AffiliationForm

    def get_initial(self):
        try:
            self.mp = get_object_or_404( Profile, pk = self.kwargs['pk'])

            try:
                level_pk = int( self.kwargs['level_pk'] )
                root_profile = get_object_or_404( Profile, pk = level_pk )
            except:
                level_pk = 0
                root_profile = 0

            level_profiles = Get_Profiles_From_Level( level_pk )

            self.root_profile = root_profile
            self.level_pk = level_pk
            self.level_profiles = level_profiles

            return { 'main_profile': self.mp,
                     'level_pk' : self.level_pk,
                     'sub_profile' : self.level_profiles,
                   }
        except:
            Http404()

    def get_context_data(self, **kwargs):
        context_dict = super(ProfileCreateSubView, self).get_context_data(**kwargs)
        context_dict['main_profile'] = self.mp
        context_dict['level_pk'] = self.level_pk
        context_dict['root_profile'] = self.root_profile
        context_dict['level_profiles'] = self.level_profiles.filter( profile_type__in = PROFILE_TYPE_FOR_TREE )
        return context_dict

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.main_profile = self.mp
        self.object.save()

        messages.success(self.request, "You successfully add the affiliation!")
        return HttpResponseRedirect( self.object.main_profile.get_absolute_url() )

from .models import Notification, GetUserNoticationsQ

VIEW_NOTIFICATIONS_NEW_BY_USER = 1
VIEW_NOTIFICATIONS_NEW_BY_TYPE = 2
VIEW_NOTIFICATIONS_OLD         = 3

@login_required
def notifications_view_prepare(request, arg_kind):
    context = RequestContext(request)
    u = request.user
    if u is None:
        raise Http404

    OLD_NOTIFICATIONS_VIEW_LIMIT = 20
    filter_name = ''

    if arg_kind == VIEW_NOTIFICATIONS_NEW_BY_USER:
        notifications = GetUserNoticationsQ( u, True ).order_by('sender_user', '-created_at' )
        filter_name = 'new_by_user'
    else:
        if arg_kind == VIEW_NOTIFICATIONS_NEW_BY_TYPE:
            notifications = GetUserNoticationsQ( u, True ).order_by(  'content_type', 'object_id', '-created_at' )
            filter_name = 'new_by_type'
        else:
            if arg_kind == VIEW_NOTIFICATIONS_OLD:
                notifications = GetUserNoticationsQ( u, False ).order_by('-created_at')[:OLD_NOTIFICATIONS_VIEW_LIMIT]
                filter_name = 'old'
            else:
                raise Http404

    context_dict = { 'notifications' : notifications, 'filter_name' : filter_name, 'OLD_NOTIFICATIONS_VIEW_LIMIT' : OLD_NOTIFICATIONS_VIEW_LIMIT }
    return render( request, 'profiles/notifications.html', context_dict )

@login_required
def notifications_view_unread(request):
    return notifications_view_prepare( request, VIEW_NOTIFICATIONS_NEW_BY_USER )

@login_required
def notifications_view_unread_by_type(request):
    return notifications_view_prepare( request, VIEW_NOTIFICATIONS_NEW_BY_TYPE )

@login_required
def notifications_view_read(request):
    return notifications_view_prepare( request, VIEW_NOTIFICATIONS_OLD )
@login_required
def del_notifications(request):
    n=request.user.id
    GetUserNoticationsQ( request.user, False ).delete()
    messages.success(request, 'All old notifications have been deleted')
    return redirect("read_notifications_view")


@login_required
def notification_read( request, notification_id ):
    from django.http import HttpResponse
    # ó ñàìîãî óâåäîìëåíèÿ îòäåëüíîé ñòðàíèöû íåò
    n = get_object_or_404( Notification, pk=notification_id )
    # óáåäèìñÿ, ÷òî þçåð - àäðåñàò óâåäîìëåíèÿ
    if n.reciever_user == request.user:
        if n.get_unreaded:
            n.mark_readed()

        if ( n.msg_url is None ) or ( n.msg_url == '' ):
            return redirect( 'unread_notifications_view' )
        else:
            return redirect( n.msg_url )
    else:
        raise Http404()
