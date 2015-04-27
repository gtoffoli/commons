from menu import Menu, MenuItem
from django.utils.translation import ugettext as _, ugettext_lazy


"""
def project_children(request):
    children = []
    children.append (MenuItem(
         _("About"),
         url='/project/about',
         weight=80,
        ))
    children.append (MenuItem(
         _("Our partners"),
         url='/project/partners',
         weight=80,
        ))
    children.append (MenuItem(
         _("Contacts"),
         url='/project/contacts',
         weight=80,
        ))
    return children
"""

project_children = (
    MenuItem("About",
             url='/project/about',
             weight=10,
             icon="user"),
)


# Add a few items to our main menu
Menu.add_item("main", MenuItem(ugettext_lazy("The project"),
                               url='/p',
                               weight=30,
                               check=True,
                               children=project_children,
                               separator=True))     
