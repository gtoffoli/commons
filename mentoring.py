from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
# from django.shortcuts import render, render_to_response, get_object_or_404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django_messages.models import Message

from roles.utils import add_local_role, remove_local_role, grant_permission, get_local_roles
from roles.models import Role
from django.contrib.auth.models import User

from .models import UserProfile, ProjType, Project, ProjectMember, ProjectMessage
from .models import PROJECT_SUBMITTED, PROJECT_OPEN, PROJECT_DRAFT, PROJECT_CLOSED, PROJECT_DELETED
from .models import NO_MENTORING, MENTORING_MODEL_A, MENTORING_MODEL_B, MENTORING_MODEL_C, MENTORING_MODEL_DICT
from .forms import ProjectMentoringModelForm, AcceptMentorForm, ProjectMentoringPolicyForm, one2oneMessageComposeForm, MatchMentorForm, SelectMentoringJourneyForm

# from .analytics import notify_event, track_action
from .tracking import notify_event, track_action


def get_all_mentors():
    proj_type_roll = ProjType.objects.filter(name='roll')
    all_memberships = ProjectMember.objects.filter(state=1, project__proj_type__name='roll', project__state=PROJECT_OPEN).order_by('user__last_name','user__first_name','user_id').distinct('user__last_name','user__first_name','user_id')
    mentors = []
    for m in all_memberships:
        if m.user.is_active:
            mentors.append(m.user)
    return mentors

def get_all_candidate_mentors(user, community):
    community_candidate_mentors = communities_candidate_mentors = None
    proj_type_roll = ProjType.objects.get(name='roll')
    roll = community.get_roll_of_mentors(states=[PROJECT_OPEN])
    rolls = Project.objects.filter(proj_type_id=proj_type_roll, state__in=[PROJECT_OPEN])
    if roll:
        memberships = roll.get_memberships(state=1).order_by('user__last_name','user__first_name')
        members = [membership.user for membership in memberships if not membership.user == user]
        community_mentors = UserProfile.objects.filter(user__in=members, mentor_unavailable = False)
        if community_mentors:
            community_candidate_mentors = User.objects.filter(id__in=[mentor.user_id for mentor in community_mentors], is_active=True).order_by('last_name','first_name')
        rolls = rolls.exclude(pk=roll.id)
    # if rolls:
    other_candidate_mentors = None
    if rolls and community.allow_external_mentors:
        members = []
        # other_candidate_mentors = None
        for roll in rolls:
            memberships = roll.get_memberships(state=1).order_by('user__last_name','user__first_name')
            for membership in memberships:
                if membership.user.is_active and not membership.user == user:
                    members.append(membership.user)
        if members:
            other_candidate_mentors = UserProfile.objects.filter(user__in=members, mentor_for_all = True, mentor_unavailable = False)
    if other_candidate_mentors:
        communities_candidate_mentors = User.objects.filter(id__in=[mentor.user_id for mentor in other_candidate_mentors], is_active=True).order_by('last_name','first_name')
    if community_candidate_mentors and communities_candidate_mentors:
        return (community_candidate_mentors | communities_candidate_mentors)
    elif community_candidate_mentors:
        return community_candidate_mentors
    elif communities_candidate_mentors:
        return communities_candidate_mentors
    return None

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
    mm = ProjectMember.objects.filter(project__proj_type__name='com', project__state=PROJECT_OPEN, project__mentoring_model__in=[MENTORING_MODEL_A,MENTORING_MODEL_C], user=user)
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

def get_mentoring_requests_waiting(user):
    """ return all mentoring projects in the state of request where the user is the community administrator """
    role_admin = Role.objects.get(name='admin')
    # find the community-admin memberships of the user
    mm = ProjectMember.objects.filter(project__proj_type__name='com', project__state=PROJECT_OPEN, user=user)
    admin_memberships = [m for m in mm if role_admin in get_local_roles(m.project, user)]
    requests = []
    for m in admin_memberships:
        community = m.project
        mentoring_projects = community.get_children(proj_type_name='ment', states=[PROJECT_SUBMITTED])
        if mentoring_projects:
            for project in mentoring_projects:
                mentors = ProjectMember.objects.filter(project=project, state=0, refused=None)
                if mentors.count():
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

def project_mentoring_policy_edit(request, project_slug):
     user = request.user
     project = get_object_or_404(Project, slug=project_slug)
     if request.POST:
        form = ProjectMentoringPolicyForm(request.POST, instance=project)
        if form.is_valid():
            allow_external_mentors = request.POST.get('allow_external_mentors','')
            if allow_external_mentors:
                project.allow_external_mentors = True
            else:
                project.allow_external_mentors = False
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

def A_send_delegate_msg(community_admins):
    subject = 'A mentee has delegated the choice of the mentor.'
    body = """A mentee has filled the request for a mentor and asks that you makes the choice. Please, look at your user dashboard for more specific information."""
    notify_event(community_admins, subject, body)

def project_delegate_admin (request, project_id):
    project = Project.objects.get(pk=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    if project.can_propose(user):
       project.state = PROJECT_SUBMITTED
       project.save()
       memberships = ProjectMember.objects.filter(project=project, state=0)
       for membership in memberships:
           membership.modified = project.modified
           membership.editor = user
           membership.save()
       community = project.get_parent()
       parent_mentoring_model = community.mentoring_model
       if ((parent_mentoring_model == MENTORING_MODEL_A) or (parent_mentoring_model == MENTORING_MODEL_C and self.mentoring_model == MENTORING_MODEL_A)):
           A_send_delegate_msg(community.get_admins())
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
        delegate = post.get('delegate', '')
        community = project.get_parent()
        parent_mentoring_model = community.mentoring_model
        project_mentoring_model = project.mentoring_model
        community_admins = community.get_admins()
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
                if ((parent_mentoring_model == MENTORING_MODEL_A) or (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_A)):
                    mentor_member = project.add_member(mentor_user,request.user)
                    message = post.get('message', '')
                    # NOTIFICA AL MENTORE SELEZIONATO 
                    recipients = [mentor_user]
                    subject = 'You have been chosen to answer a request for a mentor.'
                    body = """The Administrator of a community thinks that you are a good fit to fulfil the request of a would be mentee, and left the following notice for you:
"%s".
Please, look at your user dashboard for more specific information.""" % message or "empty notice"
                    notify_event(recipients, subject, body)
                elif ((parent_mentoring_model == MENTORING_MODEL_B) or (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_B)):
                    mentors_selected = ProjectMember.objects.filter(project=project, state=0, refused=None)
                    if mentors_selected:
                        mentor_selected = mentors_selected[0]
                        if not (mentor_selected == mentor_user):
                            user_selected = get_object_or_404(User, id=mentor_selected.user_id)
                            project.remove_member(user_selected)
                    mentor_member = project.add_member(mentor_user,request.user)
                    project.state = PROJECT_SUBMITTED
                    project.editor = request.user
                    project.save()
                    # NOTIFICA AL MENTORE SELEZIONATO E ALL'AMMINISTRATORE DELLE COMUNITA'
                    recipients = community_admins + [mentor_user]
                    subject = 'A mentee has chosen a mentor.'
                    body = """A mentee has chosen a mentor and is asking his/her consent. In your user dashboard you will find more specific information from your point of view (as mentor or community administrator)."""
                    notify_event(recipients, subject, body)
        elif delegate:
            project.mentoring_model = MENTORING_MODEL_A
            project.state = PROJECT_SUBMITTED
            project.editor = request.user
            project.save()
            A_send_delegate_msg(community_admins)
    return HttpResponseRedirect('/project/%s/' % project.slug)

def mentoring_project_accept_mentor(request, project_detail):
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
                track_action(request, user, 'Accept', membership, target=project, description=description)
                project.state=PROJECT_OPEN
                project.editor=user
                project.save()
                track_action(request, user, 'Approve', project)
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
                track_action(request, user, 'Reject', membership, target=project, description=data['description'])
                subject = "The chosen mentor didn't accept the request"
                if ((community.mentoring_model == MENTORING_MODEL_B) or (community.mentoring_model == MENTORING_MODEL_C and project.mentoring_model == MENTORING_MODEL_B)):
                    project.state = PROJECT_DRAFT
                    project.editor = user
                    project.save()
                    # send notification
                    recipients = [mentee]
                    body = """The mentor you sent a request didn't accept and left the following notice for you:
"%s".

Possibly you are willing to try another choice.
Please, look at your user dashboard for more specific information.""" % description
                elif ((community.mentoring_model == MENTORING_MODEL_A) or (community.mentoring_model == MENTORING_MODEL_C and project.mentoring_model == MENTORING_MODEL_A)):
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
    if type_name == 'ment' and request.POST.get('draft_back',''):
        parent_mentoring_model = project.get_parent().mentoring_model
        project_mentoring_model = project.mentoring_model
        message = request.POST.get('message','')
        mm = ProjectMember.objects.filter(project=project,state=0,refused=None)
        last_selected_mentor = None
        if mm:
            for m in mm:
                last_selected_mentor = m.user
                if ((parent_mentoring_model == MENTORING_MODEL_A) or (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_A)):
                    m.history = "The mentor didn't accept within time limits. The community administrator wrote: %s" % message
                elif ((parent_mentoring_model == MENTORING_MODEL_B) or (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_B)):
                    m.history = "The mentor didn't accept within time limits. The mentee wrote: %s" % message
                m.editor = user
                m.refused = timezone.now()
                m.save()
        if (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_A):
            project.mentoring_model = MENTORING_MODEL_B
        project.state = PROJECT_DRAFT
        project.editor = user
        project.save()
        if ((parent_mentoring_model == MENTORING_MODEL_A) or (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_A)):
            # INVIARE NOTIFICA AL MENTEE
            mentee = project.get_mentee(state=1)
            recipients = mentee and [mentee.user]
            subject = 'Cannot fulfil your request for a mentor'
            body = """Sorry, the Administrator of your community wasn't able to find a mentor for you and left the following notice:
"%s".
By accessing your request you could find more specific information.""" % message
            notify_event(recipients, subject, body)
            if last_selected_mentor:
                # INVIARE NOTIFICA AL MENTOR
                recipients = [last_selected_mentor]
                subject = "A request by a mentee wasn't answered within time limits"
                body = """You didn't answer a request by a mentee within the time limits; the Administrator of the community has returned the request to the mentee and left the following notice:
"%s".
""" % message
                notify_event(recipients, subject, body)

        elif ((parent_mentoring_model == MENTORING_MODEL_B) or (parent_mentoring_model == MENTORING_MODEL_C and project_mentoring_model == MENTORING_MODEL_B)):
            # INVIARE NOTIFICA AL MENTOR
            recipients = [last_selected_mentor]
            subject = "A request by a mentee wasn't answered within time limits"
            body = """You didn't answer a request by a mentee within the time limits; the mentee has withdrawn the request and left the following notice:
"%s".
""" % message

            notify_event(recipients, subject, body)

        return HttpResponseRedirect('/my_home')
    return HttpResponseRedirect('/project/%s/' % project.slug)


def mentoring_project_select_mentoring_journey(request, project_detail):
    user = request.user
    post = request.POST
    project_slug = post.get('slug')
    project = get_object_or_404(Project, slug=project_slug)
    if not project.can_access(user):
        raise PermissionDenied
    if project.is_admin(user):
        form = SelectMentoringJourneyForm(post, instance=project)
        if form.is_valid():
            data = form.cleaned_data
            pathnodes=data['prototype'].get_roots()
            pathnode = pathnodes[0]
            n_children = pathnode.has_text_children()
            if n_children:
                project.prototype=data['prototype']
                project.editor=data['editor']
                project.save()
                children = pathnode.get_ordered_text_children()
                track_action(request, user, 'Enabled', children[0], target=project)
        else:
            return project_detail(request, project.id, project=project, select_mentoring_journey={'post': post})
    return HttpResponseRedirect('/project/%s/' % project_slug)

def set_prototype_state(request,project_id):
    project = Project.objects.get(pk=project_id)
    user = request.user
    if not project.can_access(user):
        raise PermissionDenied
    if project.is_admin(user):
        post = request.POST
        if post:
            next = post.get('next', '')
            prev = post.get('prev', '')
            prototype_current_state = post.get('prototype_current_state')
            if prototype_current_state:
                pathnodes=project.prototype.get_roots()
                pathnode = pathnodes[0]
                n_children = pathnode.has_text_children()
                if n_children:
                    i = 0
                    children = pathnode.get_ordered_text_children()
                    for child in children:
                        if child.id == int(prototype_current_state):
                            if next and i < (n_children - 1):
                                track_action(request, user, 'Enabled', children[i+1], target=project)
                                break
                            elif prev and i > 0:
                                track_action(request, user, 'Enabled', children[i-1], target=project)
                                break
                        i += 1
    return HttpResponseRedirect('/project/%s/' % project.slug)