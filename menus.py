from menu import Menu, MenuItem
from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils.text import capfirst
# from django.core.urlresolvers import reverse

def community_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("about")),
         url='/info/about/',
        ))
    children.append (MenuItem(
         capfirst(_("all communities")),
         url='/cops/',
        ))
    children.append (MenuItem(
         capfirst(_("browse people")),
         url='/browse_people/',
        ))
    children.append (MenuItem(
         capfirst(_("search people")),
         url='/people/search/',
        ))
    children.append (MenuItem(
         capfirst(_("blog")),
         url='/weblog/',
        ))
    children.append (MenuItem(
         capfirst(_("forums")),
         url='/forum/',
        ))
    children.append (MenuItem(
         capfirst(_("the platform")),
         url='/info/platform/',
         ))
    return children

def projects_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("all projects")),
         url='/projects/',
        ))
    children.append (MenuItem(
         capfirst(_("top contributors")),
         url='/resources/contributors/',
        ))
    return children

def search_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("all resources")),
         # url='/repos/',
         url='/browse/',
        ))
    children.append (MenuItem(
         string_concat(capfirst(_("learning paths")), ' - ', _("advanced search")),
         url='/lps/search/',
        ))
    children.append (MenuItem(
         string_concat(capfirst(_("open resources")), ' - ', _("advanced search")),
         url='/oers/search/',
        ))
    children.append (MenuItem(
         string_concat(capfirst(_("source repositories")), ' - ', _("advanced search")),
         url='/repos/search/',
        ))
    return children

def help_children(request):
    children = []
    children.append (MenuItem(
         capfirst(_("tutorials")),
         url='/help/tutorials/',
        ))
    children.append (MenuItem(
         capfirst(_("registration and authentication")),
         url='/help/register/',
        ))
    children.append (MenuItem(
         capfirst(_("user profile and user roles")),
         url='/help/profile/',
        ))
    children.append (MenuItem(
         capfirst(_("site navigation")),
         url='/help/navigation/',
        ))
    children.append (MenuItem(
         capfirst(_("communities and projects")),
         url='/help/community/',
        ))
    children.append (MenuItem(
         capfirst(_("searching the catalogued resources")),
         url='/help/search/',
        ))
    children.append (MenuItem(
         capfirst(_("cataloguing and evaluating resources")),
         url='/help/catalog/',
        ))
    children.append (MenuItem(
         capfirst(_("learning paths")),
         url='/info/learn/',
        ))
    children.append (MenuItem(
         capfirst(_("translations of the user interface")),
         url='/info/translation/',
        ))
    children.append (MenuItem(
         capfirst(_("the site administration interface")),
         url='/help/backoffice/',
        ))
    return children

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
