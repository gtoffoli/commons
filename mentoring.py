from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, render_to_response, get_object_or_404
from django.utils import timezone

from roles.utils import add_local_role, remove_local_role, grant_permission, get_local_roles
from roles.models import Role
from django.contrib.auth.models import User
from models import ProjType, Project, ProjectMember, ProjectMessage
from models import PROJECT_SUBMITTED, PROJECT_OPEN, PROJECT_DRAFT, PROJECT_CLOSED, PROJECT_DELETED
from models import NO_MENTORING, MENTORING_MODEL_A, MENTORING_MODEL_B, MENTORING_MODEL_C, MENTORING_MODEL_DICT
from forms import ProjectMentoringModelForm, AcceptMentorForm, one2oneMessageComposeForm, MatchMentorForm
from analytics import notify_event, track_action

def get_mentor_memberships(user, state=None):
    role_admin = Role.objects.get(name='admin')
    mm = ProjectMember.objects.filter(project__proj_type__name='ment', user=user)
    if state is not None:
        mm = mm.filter(state=state)
    if state == 1:
        mm = [m for m in mm if role_admin in get_local_roles(m.project, user)]
    elif state == 0:
        mm=mm.filter(refused=None).exclude(project__state=PROJECT_DRAFT)
    return mm

def get_mentee_memberships(user, state=None):
    role_admin = Role.objects.get(name='admin')
    mm = ProjectMember.objects.filter(project__proj_type__name='ment', user=user)
    if state is not None:
        mm = mm.filter(state=state)
    mm = [m for m in mm if role_admin not in get_local_roles(m.project, user)]
    return mm 

def get_mentoring_requests(user):
    """ return all mentoring projects in the state of request where the user is the community administrator """
    role_admin = Role.objects.get(name='admin')
    # find the community-admin memberships of the user
    mm = ProjectMember.objects.filter(project__proj_type__name='com', project__state=PROJECT_OPEN, project__mentoring_model=MENTORING_MODEL_A, user=user)
    admin_memberships = [m for m in mm if role_admin in get_local_roles(m.project, user)]
    requests = []
    for m in admin_memberships:
        community = m.project
        mentoring_projects = community.get_children(proj_type_name='ment', states=[PROJECT_SUBMITTED])
        if mentoring_projects:
            for project in mentoring_projects:
                mentors = ProjectMember.objects.filter(project=project, state=0, refused=None)
                if not mentors.count():
                    requests.append(project)
    return requests

def project_mentoring_model_edit(request, project_slug):
     user = request.user
     project = get_object_or_404(Project, slug=project_slug)
     if request.POST:
        form = ProjectMentoringModelForm(request.POST, instance=project)
        if form.is_valid():
            project.mentoring_model = request.POST.get('mentoring_model','')
            project.editor = user
            project.save()
     return HttpResponseRedirect('/project/%s/' % project.slug)

def project_send_one2one_message(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    post = request.POST
    if post and post.get('send',''):
        form = one2oneMessageComposeForm(post)
        if form.is_valid():
            data = form.cleaned_data
            sender = User.objects.get(username=data['sender'])
            recipient = User.objects.get(username=data['recipient'])
            subject = data['subject']
            body = data['body']
            message = Message(sender=sender, recipient=recipient, subject=subject, body=body)
            message.save()
            project_message = ProjectMessage(project=project, message=message)
            project_message.save()
    return HttpResponseRedirect('/project/%s/' % project.slug)

def project_set_mentor(request):
    post=request.POST
    if post:
        project_id = post.get('project')
        project = get_object_or_404(Project, id=project_id)
        if not project.can_access(request.user):
            raise PermissionDenied
        mentor_id = post.get('mentor', None)
        save = post.get('save', '')
        submit = post.get('submit', '')
        parent_mentoring_model = project.get_parent().mentoring_model
        if save:
            if mentor_id:
                mentor_user = get_object_or_404(User, id=mentor_id)
                mentors_selected = ProjectMember.objects.filter(project=project, state=0, refused=None)
                if mentors_selected:
                   mentor_selected = mentors_selected[0]
                   if not (mentor_selected == mentor_user):
                      if (parent_mentoring_model == MENTORING_MODEL_B) and (project_state == PROJECT_DRAFT):
                          user_selected = get_object_or_404(User, id=mentor_selected.user_id)
                          project.remove_member(user_selected)
                   else:
                       return HttpResponseRedirect('/project/%s/' % project.slug)
                mentor_member = project.add_member(mentor_user,request.user)
        elif submit:
            if mentor_id:
                mentor_user = get_object_or_404(User, id=mentor_id)
                if (parent_mentoring_model == MENTORING_MODEL_A):
                    mentor_member = project.add_member(mentor_user,request.user)
                    message = post.get('message', '')
                    # NOTIFICA AL MENTORE SELEZIONATO 
                    print "================= INVIO EMAIL AL MENTORE SELEZIONATO ==========="
                    recipients = [mentor_user]
                    subject = 'You have been chosen to answer a request for a mentor.'
                    body = """The Administrator of a community thinks that you are a good fit to fulfil the request of a would be mentee, and left the following notice for you:
"%s".
Please, look at your user dashboard for more specific information.""" % message or "empty notice"
                    notify_event(recipients, subject, body)
                elif (parent_mentoring_model == MENTORING_MODEL_B):
                    mentors_selected = ProjectMember.objects.filter(project=project, state=0, refused=None)
                    if mentors_selected:
                        mentor_selected = mentors_selected[0]
                        if not (mentor_selected == mentor_user):
                            user_selected = get_object_or_404(User, id=mentor_selected.user_id)
                            project.remove_member(user_selected)
                            mentor_member = project.add_member(mentor_user,request.user)
                    else:
                        mentor_member = project.add_member(mentor_user,request.user)
                    project.state = PROJECT_SUBMITTED
                    project.save()
    return HttpResponseRedirect('/project/%s/' % project.slug)

def project_accept_mentor(request):
    user = request.user
    post = request.POST
    project_id = post.get('project')
    project = get_object_or_404(Project, id=project_id)
    if post:
        if not project.can_access(request.user):
            raise PermissionDenied
        form = AcceptMentorForm(post, instance=project)
        if form.is_valid():
            membership = ProjectMember.objects.get(project=project, user=user, state=0, refused=None)
            data = form.cleaned_data
            accept = int(data['accept'])
            membership.editor=user
            description = data['description']
            membership.history = description
            community = project.get_parent()
            community_admins = community.get_admins()
            mentee = project.get_mentee().user
            if accept == 1:
                membership.state = 1
                membership.accepted=timezone.now()
                membership.save()
                role_admin = Role.objects.get(name='admin')
                add_local_role(project, user, role_admin)
                track_action(user, 'Accept', membership, target=project, description=description)
                project.state=PROJECT_OPEN
                project.editor=user
                project.save()
                track_action(user, 'Approve', project)
                # send notification
                recipients = community_admins + [mentee]
                subject = 'The chosen mentor has accepted the request'
                body = """The mentor chosen has accepted the request of the mentee, and left the following notice for you:
"%s".

The mentoring project is now on.
Please, look at your user dashboard for more specific information.""" % description
                notify_event(recipients, subject, body)
            else: # refusal
                membership.refused=timezone.now()
                membership.save()
                track_action(user, 'Reject', membership, target=project, description=data['description'])
                subject = "The chosen mentor didn't accept the request"
                if community.mentoring_model == MENTORING_MODEL_B:
                    project.state = PROJECT_DRAFT
                    project.editor = user
                    project.save()
                    # send notification
                    recipients = [mentee]
                    body = """The mentor you sent a request didn't accept and left the following notice for you:
"%s".

Possibly you are willing to try another choice.
Please, look at your user dashboard for more specific information.""" % description
                elif community.mentoring_model == MENTORING_MODEL_A:
                    # send notification
                    recipients = community_admins
                    body = """The mentor chosen for the mentee by a community administrator didn't accept and left the following notice for you:
"%s".

You could tell the mentee and/or try another choice.
Please, look at your user dashboard for more specific information.""" % description
                notify_event(recipients, subject, body)
                return HttpResponseRedirect('/my_home/')
        else:
            return project_detail(request, project_id, project=project, accept_mentor_form={'post': post})
    return HttpResponseRedirect('/project/%s/' % project.slug)

def project_draft_back(request, project_id):
    project = Project.objects.get(pk=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    type_name = project.proj_type.name
    mentoring_model = project.get_parent().mentoring_model
    if type_name == 'ment':
        if mentoring_model == MENTORING_MODEL_A:
            mm = ProjectMember.objects.filter(project=project,state=0,refused=None)
            if mm:
                for m in mm:
                    m.history = 'mentore non ha risposto'
                    m.editor = user
                    m.refused = timezone.now()
                    m.save()
            message = request.POST.get('message',None)
            if message:
                project.state = PROJECT_DRAFT
                project.editor = user
                project.save()
                # INVIARE NOTIFICA AL MENTEE
                print "=============RIPORTA PROGETTO A DRAFT INVIARE NOTIFICA AL MENTEE ===="
                mentee = project.get_mentee(state=1)
                recipients = mentee and [mentee.user]
                subject = 'Cannot fulfil your request for a mentor.'
                body = """Sorry, the Administrator of your community wasn't able to find a mentor for you and left the following notice:
"%s".
By accessing your request you could find more specific information.""" % message
                notify_event(recipients, subject, body)
                return HttpResponseRedirect('/my_home')
    return HttpResponseRedirect('/project/%s/' % project.slug)
