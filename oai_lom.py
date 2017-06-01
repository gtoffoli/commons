from oaipmh.metadata import MetadataReader

oai_lom_reader = MetadataReader(
    fields={
    'UID':         ('textList', 'lom:lom/lom:general/lom:identifier/lom:entry/text()'),
    'title':       ('textList', 'lom:lom/lom:general/lom:title/text()'),
    'language':    ('textList', 'lom:lom/lom:general/lom:language/text()'),
    'keywords':    ('textList', 'lom:lom/lom:general/lom:keyword/lom:string/text()'),
    'description': ('textList', 'lom:lom/lom:general/lom:description/text()'),
    'materialtype':('textList', 'lom:lom/lom:educational/lom:description/text()'),
    'audience':    ('textList', 'lom:lom/lom:educational/lom:description/text()'),
    'location':    ('textList', 'lom:lom/lom:technical/lom:location/text()'),
    'thumbnail':   ('textList', 'lom:lom/lom:technical/lom:thumbnail/text()'),
    'format':      ('textList', 'lom:lom/lom:technical/lom:format/text()'),
    'provider':    ('textList', 'lom:lom/lom:lifeCycle/lom:contribute/lom:entity/text()'),
    'rights':      ('textList', 'lom:lom/lom:lifeCycle/lom:contribute/lom:entity/text()'),
    'license':     ('textList', 'lom:lom/lom:rights/lom:description/lom:string/text()'),
    },
    namespaces={
    'lom' : 'http://ltsc.ieee.org/xsd/LOM'}
    )
