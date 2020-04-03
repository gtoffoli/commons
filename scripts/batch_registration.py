from datetime import date, datetime
import pyexcel as pe
import uuid
from django.utils import timezone
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User, Group
from roles.models import Role
from roles.utils import add_local_role
from commons.models import ProjType, Project, ProjectMember

fn = "/_Progetti/_Up2U/CommonSpaces/support/Italian U-Hub/Gruppi e Iscritti Corso ICT4HER 2019-2020 II semestre.xlsx"
fn = "/home/toffoli/Gruppi e Iscritti Corso ICT4HER 2019-2020 II semestre.xlsx"

def list_to_dict(lst):
    return {k: v for v, k in enumerate(lst)}

NO_MENTORING = 0
project_type = ProjType.objects.get(name='lp')
role_member = Role.objects.get(name='member')
role_admin = Role.objects.get(name='admin')

parent = Project.objects.get(id=374) # 2019/2020 Informatica applicata ai Beni Culturali II Semestre
gt = User.objects.get(id=10)
sl = User.objects.get(username="495162")

f = open(fn, "br")
extension = fn.split(".")[-1]
content = f.read()
f.close()
book = pe.get_book(file_type=extension, file_content=content)
book_dict = book.to_dict()
sheet_list = list(book_dict.keys())

tables_dict = list_to_dict(sheet_list)

group_table = book_dict["Legenda Gruppi"]
student_table = book_dict["Elenco iscritti"]

group_cols = group_table[0]
group_rows = group_table[1:]
group_cols_dict = list_to_dict(group_cols)

student_cols = student_table[0]
student_rows = student_table[1:]
student_cols_dict = list_to_dict(student_cols)

# get senior project Supervisor
parent_admin = parent.get_senior_admin()

def add_member(project, user, make_admin=False):
    if project.get_membership(user):
        return None
    membership = ProjectMember(project=project, user=user, editor=parent_admin, state=1, accepted=timezone.now())
    membership.save()
    group = project.group
    if not group in user.groups.all():
        user.groups.add(group)
    if make_admin and not project.is_admin(user):
        add_local_role(project, user, role_admin)
    return membership

group_project_dict = {}

def create_child(parent, row):
    code = row[group_cols_dict['code']]
    name = row[group_cols_dict['name']]
    if not (code and name):
        return
    description = row[group_cols_dict['description']]
    project = Project(name=name, proj_type=project_type, description=description, state=2, creator=parent_admin, editor=parent_admin, original_language='it')
    group_name = str(uuid.uuid4())
    group = Group(name=group_name)
    group.parent = parent.group
    group.save()
    project.group = group
    group_id = group.id
    project.mentoring_model = NO_MENTORING
    project.save()
    group = Group.objects.get(pk=group_id)
    group.name='%s-%s' % (project.id, slugify(project.name[:50]))
    group.save()
    project.define_permissions(role=role_member)
    add_local_role(project, group, role_member)
    project.create_folder()
    print (code, name, description, project.id, group.id)
    return project

def create_student(row):
    code = row[student_cols_dict['code']]
    if not code:
        return None
    last_name = row[student_cols_dict['last_name']] 
    first_name = row[student_cols_dict['first_name']] 
    email = row[student_cols_dict['email']]
    if not email:
        return None
    username = slugify('%s.%s' % (first_name.lower(), last_name.lower()))
    users = User.objects.filter(email=email)
    if not users.count():
        same_names = User.objects.filter(first_name=first_name, last_name=last_name)
        if same_names.count():
            user = same_names[0]
            print('user exists with same name but other email:', last_name, first_name, user.email)
            if same_names.count() == 1:
                if user.is_completed_profile():
                    print('.... and has profile already')
                    return user
            return None
        elif User.objects.filter(username=username).count():
            print('username exists with other email:', username)
            return None
        else:
            user = User.objects.create_user(username=username, email=email, first_name=first_name, last_name=last_name)
            user.set_unusable_password()
            user.save()
    elif users.count() > 1:
        print('multiple users:', users)
        return None
    else:
        user = users[0]
    if user.is_completed_profile():
        print('user has profile already:', email, user.last_name, user.first_name)
        return user
    profile = user.get_profile()
    profile.country_id = country_id = row[student_cols_dict['country']]
    dob = row[student_cols_dict['dob']]
    if dob:
        dob = datetime.strptime(dob, '%d/%m/%Y').date()
    else:
        dob = date.today()
    profile.dob = dob
    profile.edu_level_id = edu_level_id = row[student_cols_dict['edu_level']]
    profile.pro_status_id = pro_status_id = row[student_cols_dict['pro_status']]
    profile.short = short = row[student_cols_dict['short']]
    print (code, last_name, first_name, email, country_id, dob, edu_level_id, pro_status_id, short)
    profile.save()
    return user

# @transaction.atomic
def do_all():
    for row in group_rows:
        child = create_child(parent, row)
        code = row[group_cols_dict['code']]
        group_project_dict[code] = child
        add_member(child, parent_admin, make_admin=True)
        add_member(child, gt, make_admin=True)
    for row in student_rows:
        user = create_student(row)
        if user:
            code = row[student_cols_dict['code']]
            project = group_project_dict[code]
            membership = add_member(project, user)
