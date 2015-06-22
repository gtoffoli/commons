from menu import Menu, MenuItem
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.text import capfirst
# from django.core.urlresolvers import reverse

def oers_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("by source")),
         url='/repos/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("by project")),
         url='/oers/by_project/',
         weight=80,
        ))
    children.append (MenuItem(
         capfirst(_("full search")),
         url='/oers/search/',
         weight=80,
        ))
    return children

def rosters_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("repositories by submitter")),
         url='/repositories/contributors/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("resources by submitter")),
         url='/oers/contributors/',
         weight=80,
        ))
    return children

def help_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("site navigation")),
         url='/help/navigation/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         _("OER search"),
         url='/help/search/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         _("OER collection and classification"),
         url='/help/catalog/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("registration and authentication")),
         url='/help/register/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         capfirst(_("editing the user profile")),
         url='/help/profile/',
         weight=80,
         check=True,
        ))
    return children

def info_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("about")),
         url='/info/about/',
         weight=80,
         check=True,
        ))
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

# Add a few items to our main menu
Menu.add_item("main", MenuItem(capfirst(_("find OERs")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=oers_children,
                               separator=True))
Menu.add_item("main", MenuItem(capfirst(_("rosters")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=rosters_children,
                               separator=True))
Menu.add_item("main", MenuItem(capfirst(_("help")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=help_children,
                               separator=True))
Menu.add_item("main", MenuItem(capfirst(_("info")),
                               url='/p',
                               weight=30,
                               check=True,
                               children=info_children,
                               separator=True))     
