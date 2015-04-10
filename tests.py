'''
Created on 09/apr/2015
@author: giovanni
'''

from commons.models import Language, RepoType, RepoFeature, Repo, ProjType, Project

def populate_languages():
    import mayan.settings.base
    for i in mayan.settings.base.LANGUAGES:
        choice = Language(code=i[0], name=i[1])
        choice.save()

REPO_TYPES = (
  ('repository', 'OER Repository (contents)',),
  ('catalog', 'OER Catalog (metadata only)',),
  ('directory', 'OER Directory / Portal',),
  ('mixed', 'Repository plus Catalog or Directory',),
)

def populate_repo_types():
    for t in REPO_TYPES:
        repo_type = RepoType(name=t[0], description=t[1])
        repo_type.save()

REPO_FEATURES = (
  ('AU', 'AUthors info',),
  ('CC', 'Creative Commons license info',),
  ('DL', 'DownLoad support',),
  ('FT', 'Full-text search',),
  ('ML', 'Multi-Lingual UI support',),
  ('PP', 'Popularity Score',),
  ('PR', 'Pear Review',),
  ('QR', 'Quality Rating',),
  ('SE', 'specialized Search Engine',),
)

def populate_repo_features():
    j = 0
    for i in REPO_FEATURES:
        j += 1
        repo_feature = RepoFeature(code=i[0], name=i[1], order=j)
        repo_feature.save()

PROJ_TYPES = (
  ('com', 'community',),
  ('oer', 'OER cataloguing',),
  ('lp', 'Learning Path creation',),
)

def populate_proj_types():
    for i in PROJ_TYPES:
        repo_type = ProjType(name=i[0], description=i[1])
        repo_type.save()

REPOS = (
  ('repository', 'Youtube', 'https://www.youtube.com/', "Includes mostly videos, organized by channels. Education is a channel.", ('AU', 'CC', 'DL', 'FT', 'ML', 'PP',),),
  ('mixed', 'OER Commons', 'http://www.oercommons.org', "Focused on K-12, curricula and Common Core (US). Uses a large number of metadata.", ('AU', 'CC', 'DL', 'FT', 'QR',),),
  ('directory', 'Audiocast', 'http://www.audiocast.it/', "The reference site for the podcast in Italy, with rich and up-to-date info and technical guides.", ('AU', 'DL',),),
  ('repository', 'Vitruvius', 'http://areeweb.polito.it/didattica/vitruvius/', "A small repository of digital architecture videotutorials from the Turin Polytehcnic", ('CC', 'FT',),),
)

def create_repos():
    for r in REPOS:
        repo_type = RepoType.objects.get(name=r[0])
        repo = Repo(repo_type=repo_type, name=r[1], url=r[2], description=r[3], user_id=1)
        repo.save()
        for f in r[4]:
            feature = RepoFeature.objects.get(code=f)
            repo.features.add(feature)

PROJECTS = (
  ('com', 'Sapienza', 'Sapienza Community',),
  ('com', 'EST', 'European School of Translation',),
  ('oer', 'Employability OERs', 'Cataloguing OERs on Employability',),
)

def create_projects():
    for p in PROJECTS:
        proj_type = ProjType.objects.get(name=p[0])
        proj = Project(proj_type=proj_type, description=p[2], user_id=1)
        proj.group_name = p[1]
        proj.save()

def populate():
    populate_languages()
    populate_repo_types()
    populate_repo_features()
    populate_proj_types()
    create_repos()
    create_projects()
