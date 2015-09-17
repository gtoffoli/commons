from menu import Menu, MenuItem
from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils.text import capfirst
# from django.core.urlresolvers import reverse

def community_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("about")),
         url='/info/about/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("all communities")),
         url='/cops/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("browse people")),
         url='/browse_people/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("search people")),
         url='/people/search/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("blog")),
         url='/weblog/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("forums")),
         url='/forum/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("the platform")),
         url='/info/platform/',
         weight=80,
         check=True,
        ))
    return children

def projects_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("all projects")),
         url='/projects/',
         weight=80,
         check=True,
        ))
    """
    children.append (MenuItem(
         string_concat(capfirst(_("repositories")), ' ', _("by submitter")),
         url='/repositories/contributors/',
         weight=80,
         check=True,
        ))
    """
    children.append (MenuItem(
         capfirst(_("top contributors")),
         url='/resources/contributors/',
         weight=80,
        ))
    return children

def search_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("all resources")),
         # url='/repos/',
         url='/browse/',
         weight=80,
        ))
    """
    children.append (MenuItem(
         string_concat(capfirst(_("OERs")), ' - ', _("by source")),
         url='/repos/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         string_concat(capfirst(_("OERs")), ' - ', _("by project")),
         url='/oers/by_project/',
         weight=80,
        ))
    """
    children.append (MenuItem(
         string_concat(capfirst(_("learning paths")), ' - ', _("advanced search")),
         url='/lps/search/',
         weight=80,
        ))
    children.append (MenuItem(
         string_concat(capfirst(_("open resources")), ' - ', _("advanced search")),
         url='/oers/search/',
         weight=80,
        ))
    children.append (MenuItem(
         string_concat(capfirst(_("source repositories")), ' - ', _("advanced search")),
         url='/repos/search/',
         weight=80,
        ))
    return children

def help_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("registration and authentication")),
         url='/help/register/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("user profile and user roles")),
         url='/help/profile/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("site navigation")),
         url='/help/navigation/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("communities and projects")),
         url='/help/community/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("searching the catalogued resources")),
         url='/help/search/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("cataloguing open resources")),
         url='/help/catalog/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("learning paths")),
         url='/info/learn/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("translations of the user interface")),
         url='/info/translation/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("the site administration interface")),
         url='/help/backoffice/',
         weight=80,
         check=True,
        ))
    return children

"""
def info_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("community and projects")),
         url='/info/projects/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         _("OERs and metadata"),
         url='/info/oers/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("external repositories")),
         url='/info/repos/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("the user profile")),
         url='/info/profile/',
         weight=80,
         check=True,
        ))
    return children
"""

# Add a few items to our main menu
Menu.add_item("main", MenuItem(capfirst(_("community")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=community_children,
                               separator=True))
Menu.add_item("main", MenuItem(capfirst(_("projects")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=projects_children,
                               separator=True))     
Menu.add_item("main", MenuItem(capfirst(_("library")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=search_children,
                               separator=True))
Menu.add_item("main", MenuItem(capfirst(_("help")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=help_children,
                               separator=True))
