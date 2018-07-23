# commons
**Platform for the communities of the CommonS Erasmus+ Project**

CommonS (= Common Spaces) was an [*Erasmus+*](http://ec.europa.eu/programmes/erasmus-plus/index_en.htm) project funded by the EU, aimed at experimenting new forms of co-learning, e-tutoring and e-mentoring.

Among the main results of the Erasmus+ project CommonS (September 2014 - August 2017) there are:
- the *Commons Platform* (a software and its deployment)
- *CommonSpaces*, a federation of Communities and Projects hosted and supported by the CommonS Platform (at http://www.commonspaces.eu).
We often use the term CommonSpaces to denote both things

CommonSpaces supports Communities of Practice (CoPs) in their activities. CoPs comprise teachers, students, young and senior professionals; they work mainly to the retrieval, adaptation (including translation), reuse and remix of available educational contents, to be used as building blocks of learning pathways.

The CommonSpaces provides functions for
- authentication and user management
- management of Projects (ako work groups), which are grouped in Communities
- collaborative cataloguing of OERs
- OER search based on a rich set of metadata
- prototyping of Learning Pathways
- support to mentoring: the Mentoring relationship is modeled as a special type of Project
- multi-language support.
A User Guide is available online as a number of help pages under the Help menu of CommonSpaces. A deployment guide was also produced.

Previously, my organization had much experience in developing applications and tools with OS software, but this was our first attempt at using Git and GitHub.
We started by developing a [Django](https://www.djangoproject.com) project customizing and wrapping the [*Mayan-EDMS*](https://github.com/mayan-edms) application, in order to be able to create a sample *OER library* (OER = open educational resources). Currently, only some low level code from this first experiment remains; on the other hand, now CommonSpaces integrates dozens of other valuable Django extensions.

In practice, CommonSpaces is a multiplatform application: the production version runs on Linux-Ubuntu, while we are performing most of the development on Windows.
The current deployment is based on Python 2.7, Django 1.8 and PostgreSQL 9.2. An upgrade based on Pyton 3.6, Django 2.0.6 and PostgreSQL 9.5 is under testing.
