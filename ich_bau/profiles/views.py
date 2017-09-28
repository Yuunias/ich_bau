from django.core.urlresolvers import reverse
from django.views.generic import UpdateView, DetailView, ListView

from django.contrib import messages

from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext

from account.mixins import LoginRequiredMixin

from .forms import ProfileForm
from .models import Profile
from account.decorators import login_required
from reversion.models import Version

class ProfileEditView(LoginRequiredMixin, UpdateView):

    form_class = ProfileForm
    model = Profile

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return reverse("profiles_list")

    def form_valid(self, form):
        response = super(ProfileEditView, self).form_valid(form)
        messages.success(self.request, "You successfully updated your profile.")
        return response

class ProfileDetailView(DetailView):

    model = Profile
    slug_url_kwarg = "profile_id"
    slug_field = "id"
    context_object_name = "profile"

class ProfileListView(ListView):

    model = Profile
    context_object_name = "profiles"
    
from .models import Notification, GetUserNoticationsQ

@login_required
def notifications_view_prepare(request, arg_new):    
    context = RequestContext(request)
    u = request.user
    if u is None:
        raise Http404
        
    notifications = GetUserNoticationsQ( u, arg_new )    
        
    context_dict = { 'notifications' : notifications, 'filter_new' : arg_new }
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
        Http404    
