# commons
**A Collaborative Learning platform: cataloging and remixing of Open Educational Resources (OER), e-mentoring and e-tutoring, Learning Analytics (LA), and more**

*CommonS* (= common spaces) was an *[Erasmus+](http://ec.europa.eu/programmes/erasmus-plus/index_en.htm)* project (September 2014 - August 2017) funded by the EU, aimed at experimenting new forms of co-learning, e-tutoring and e-mentoring.
Among the main results of the *CommonS* project there are:
- the *Commons Platform* (this software);
- *[CommonSpaces](https://www.commonspaces.eu)*, a federation of Communities and Projects hosted and supported by the *CommonS Platform*.

Often, the term *CommonSpaces* is used to denote both things.

***Origin***

We started by developing a **[Django](https://www.djangoproject.com) project** customizing and wrapping the [*Mayan-EDMS*](https://github.com/mayan-edms) application, in order to be able to create a sample *OER library* (OER = open educational resource).
Currently, only some low level code from this first experiment remains; on the other hand, now *CommonSpaces* integrates dozens of other valuable Django extensions.

To exploit the work of people with greater experience in the field, from the very beginning we adopted, as far as possible, the classification scheme and the metadata terminology proposed by the **[OER Commons](https://www.oercommons.org/)** initiative.

***Functionality***

*CommonSpaces* supports *Communities of Practice* (CoPs) in their activities. CoPs comprise teachers, students, young and senior professionals; they work mainly to the retrieval, adaptation (including translation), reuse and remix of available educational contents, to be used as building blocks of *learning pathways*.

Among the functions that the **Commons Platform** provides, we can mention:
- authentication and *user management*;
- management of *Projects* (ako work groups), which are grouped in *Communities*;
- collaborative cataloguing of *OERs*;
- OER search based on a rich set of *metadata*;
- prototyping of *Learning Pathways* (LP);
- forums and blogs;
- support to *mentoring*: the mentoring relationship is modeled as a special type of private Project;
- *content analysis*: we provide Django extensions exploiting the *spaCy* NLP library (more below);
- a few native LA functions, based on *activity streams*;
- *xAPI* support providing an interface to a *Learning Record Store* (LRS);
- *multi-language support for the UI*; currrently the UI strings and the metadata terminology are available in **9 languages**: English, Italian, Spanish, Portuguese, French, Greek, Croatian, Russian and Arabic (but the translation in the last two languages needs substancial revision);
- *multi-language support for the UGC* (user-generated content): textual metadata values, including those of titles and descriptions, and plain or rich-text fields of some content types, can be translated to each of the configured languages by means of dedicated multi-pane forms.

A **User Guide** is available online as a number of *help pages*, under the *Help* menu of *CommonSpaces*. A *deployment guide* was also produced.

***Core architecture***

*CommonSpaces* is a **multiplatform** application: the *production* version runs on *Linux-Ubuntu*, while we are performing most of the development on Windows.
The current deployment is based on Python 3.10, Django 4 and PostgreSQL 14.

The following *Django apps* are in large part autonomous, but were initially developed as extensions of *CommonSpaces*:
- *[commons-language](/gtoffoli/commons-language)* provides basic NLP services by  integrating **[spaCy](https://spacy.io/)**, with the associated language resources, extends someway its functionality and runs as a distict service exposing *HTTP API*;
- *[commons-textanalysis](/gtoffoli/commons-textanalysis)* implements a repertoire of *Text Analysis* functions with general objectives of linguistic education, to be used in the context of both L1 and L2, by learners and teachers and by editors of text resources; it relies on *commons-language*;
 
We provide here a non-exhaustive list of the valuable Django extensions that *CommonSpaces* integrates from their official releases on [Pypi](https://pypi.org/):
- django-mptt: "Utilities for implementing Modified Preorder Tree Traversal with your Django Models and working with trees of Model instances";
- django-allauth: "Integrated set of Django applications addressing authentication, registration, account management as well as 3rd party (social) account authentication";
- django-haystack: "Haystack provides modular search for Django; it features a unified, familiar API that allows you to plug in different search backends";
- django_autocomplete_light: the autocomplete feature provides suggestions to the searcher by completing the entered text;
- django-dag: "a small reusable app which implements a Directed Acyclic Graph";
- django-rest-framework: "Awesome web-browsable Web APIs";
- django-actstream: "Django Activity Stream is a way of creating activities generated by the actions on your sit";
- rdflib-django3: "A store implementation for rdflib that uses Django as its backend";
- django-scheduler: "A calendaring app for Django".

We keep in distinct GitHub repositories other important Django extensions which we had to customize for some reasons, by forking them from their original version; among them:
- pybbm: "PyBBM is a full-featured django forum solution";
- django-blog-zinnia: "Simple yet powerful and really extendable application for managing a blog within your Django Web site".

Finally, there are some Django extensions that the original developers no more are actively maintaining (or were maintaining when we wanted to integrate them); among them:
- django-datatrans; "Translate Django models without changing anything to existing applications and their underlying database";
- hierarchical_auth: "It allows to hierarchically organize the groups, allowing easy permissions management for complex systems";
- django-xapi-client: "A set of functions to put, get and process xapi statements".

***Support of mini-sites***

At present, *CommonSpaces* hosts a few *mini-sites* dedicated to the communities of various international research projects.

In CommonSpaces, *restricted* top-level communities can be given the special status of *mini-site*. A mini-site:
- can be accessed with a dedicated internet address;
- allows a finer control of the access rights;
- allows easier navigation and search within its dedicated spaces, due to the fact that the contents of the other communities are shielded.

Examples of mini-sites are:
- *[EuroIdentitis](http://www.euroidentities.eu/)*: contains the current results of the project *The States of the European Union: Identity as self-representation*, funded by *Sapienza University of Rome*; this is also the result of an experiment in augmenting the *data model* of the Commons Platform with support of *RDF triples* and direct links to *[Wikidata](https://www.wikidata.org) entities*;
- *[WE-COLLAB](https://www.we-collab.eu/)*: this is the site of the *Erasmus+* project *Collaborative and transparent use of Learning Analytics in online university courses, valuing the learner role and exploiting advanced monitoring equipment*;
- *[SUCCESS](https://success4all.commonspaces.eu/)*: this is the collaboration site and a component of the learning platorm of the *Erasmus+* project *Supporting success for all – Universal Design Principles in Digital Learning for students with disabilities*;
- *[HEALTH](https://health.commonspaces.eu/)*: this is the collaboration site of the international project *Health emergency in Asia and Africa: societal implications, narratives on media, political issues*.

***Plans***

Main activities planned are:
- complete the restructuring of the software stack, in order to make *commons-textanalysis* completely independent from the software of the *Commons Platform*, of wich originally it was part;
- document the API anf better document the architecture
- revise the configuration support, also to remove stuff too dependent on ephemeral extensions related to past projects / collaborations; 
- clean up the code, also to make easier possible contributions.