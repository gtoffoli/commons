'''
Created on 09/apr/2015
@author: giovanni
'''

from models import ProjType, Project, Subject, RepoType, RepoFeature, Repo, OER
from models import DocumentType, Document, DocumentVersion, oer_documents, OerDocument

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
  ('PR', 'Peer Review',),
  ('QR', 'Quality Rating',),
  ('SE', 'specialized Search Engine',),
)

def populate_repo_features():
    j = 0
    for i in REPO_FEATURES:
        j += 1
        repo_feature = RepoFeature(code=i[0], name=i[1], order=j)
        repo_feature.save()

SUBJECTS = (
  ('ART', 'Arts',),
  ('BIZ', 'Business (BIZ)',),
  ('BIZ-ENT', 'BIZ - Enterpreneurship',),
  ('HUM', 'Humanities (HUM)',),
  ('HUM-FR', 'HUM - Foreign Languages',),
  ('HUM-LT', 'HUM - Learning & Teaching',),
  ('STM', 'Science, Technology and Mathematics (STM)',),
  ('STM-ICT', 'STM - ICT Literacy',),
  ('SOC', 'Social Sciences (SOC)',),
  ('SOC-REL', 'SOC - Interpersonal Skills',),
)

def populate_subjects():
    for i in SUBJECTS:
        subject = Subject(code=i[0], name=i[1])
        subject.save()

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
  ('oer', 'Sample Library of OERs', 'Build and test a Sample Library',),
)

def create_projects():
    for p in PROJECTS:
        proj_type = ProjType.objects.get(name=p[0])
        proj = Project(proj_type=proj_type, description=p[2], user_id=1)
        proj.group_name = p[1]
        proj.save()

def populate():
    # populate_languages()
    populate_repo_types()
    populate_repo_features()
    populate_proj_types()
    create_repos()
    create_projects()
    
def repo_subjects():
    repos = Repo.objects.all().order_by('id')
    for repo in repos:
        print repo
        subjects = repo.subjects.all()
        for s in subjects:
            print '-', s.code, s.name

def repo_editor():
    repos = Repo.objects.all().order_by('id')
    for repo in repos:
        print repo, repo.user

def migrate_oer_documents():
    oers = OER.objects.all()
    for oer in oers:
        old_oer_documents = oer_documents.objects.filter(oer=oer).order_by('document__date_added')
        for old_oer_document in old_oer_documents:
            oer_document = OerDocument(oer=old_oer_document.oer, document=old_oer_document.document)
            oer_document.save()
            print oer_document.oer, oer_document.document

