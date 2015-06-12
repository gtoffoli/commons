from menu import Menu, MenuItem
from django.utils.translation import ugettext as _, ugettext_lazy
# from django.core.urlresolvers import reverse

def oers_children(request):
    children = []
    children.append (MenuItem(
         _("By source"),
         url='/repos/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         _("By project"),
         url='/oers/by_project/',
         weight=80,
        ))
    children.append (MenuItem(
         _("By submitter"),
         url='/oers/by_user/',
         weight=80,
        ))
    children.append (MenuItem(
         _("Full search"),
         url='/oers/search/',
         weight=80,
        ))
    return children

def rosters_children(request):
    children = []
    children.append (MenuItem(
         _("Repositories by submitter"),
         url='/repository/contributors/',
         weight=80,
         check=True,
        ))
    return children

def help_children(request):
    children = []
    children.append (MenuItem(
         _("Site navigation"),
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
         _("Registration and authentication"),
         url='/help/register/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         _("Editing the user profile"),
         url='/help/profile/',
         weight=80,
         check=True,
        ))
    return children

def info_children(request):
    children = []
    children.append (MenuItem(
         _("About"),
         url='/info/about/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         _("Community and projects"),
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
         _("External repositories"),
         url='/info/repos/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         _("The user profile"),
         url='/info/profile/',
         weight=80,
         check=True,
        ))
    return children

# Add a few items to our main menu
Menu.add_item("main", MenuItem(ugettext_lazy("Find OERs"),
                               url='/p',
                               weight=30,
                               check=True,
                               children=oers_children,
                               separator=True))
Menu.add_item("main", MenuItem(ugettext_lazy("Rosters"),
                               url='/p',
                               weight=30,
                               check=True,
                               children=rosters_children,
                               separator=True))
Menu.add_item("main", MenuItem(ugettext_lazy("Help"),
                               url='/p',
                               weight=30,
                               check=True,
                               children=help_children,
                               separator=True))
Menu.add_item("main", MenuItem(ugettext_lazy("Info"),
                               url='/p',
                               weight=30,
                               check=True,
                               children=info_children,
                               separator=True))     
