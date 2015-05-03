from menu import Menu, MenuItem
from django.utils.translation import ugettext as _, ugettext_lazy
# from django.core.urlresolvers import reverse

def oers_children(request):
    children = []
    children.append (MenuItem(
         _("About"),
         url='/oers/about/',
         weight=80,
         check=True,
        ))
    children.append (MenuItem(
         _("By source"),
         url='/repos/',
         weight=80,
         check=True,
        ))
    """
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
    """
    return children

# Add a few items to our main menu
Menu.add_item("main", MenuItem(ugettext_lazy("OERs"),
                               url='/p',
                               weight=30,
                               check=True,
                               children=oers_children,
                               separator=True))
""" 
Menu.add_item("main", MenuItem(ugettext_lazy("Project"),
                               url='/p',
                               weight=30,
                               check=True,
                               children=project_children,
                               separator=True))     
"""
