import uuid
from tincan import (
    RemoteLRS,
    Statement,
    Agent,
    Verb,
    Activity,
    Context,
    LanguageMap,
    ActivityDefinition,
    StateDocument,
)
import settings

verbs_dict = {
}

instructor = Agent(
    name='CommonSpaces',
    mbox='mailto:commons@commonspaces.eu',
)

def put_statement(request, verb_id, verb_description=None, activity_id, activity_definition, instructor=None):
    user = request.user

    # construct an LRS
    print "constructing the LRS..."
    lrs = RemoteLRS(
        version = settings.LRS_VERSION,
        endpoint = settings.LRS_ENDPOINT,
        username = settings.LRS_USERNAME,
        password = settings.LRS_PASSWORD,
    )
    print "...done"

    # construct the actor of the statement
    print "constructing the Actor..."
    actor = Agent(
        name=user.get_display_name(),
        mbox='mailto:%s' % user.email,
    )
    print "...done"

    # construct the verb of the statement
    print "constructing the Verb..."
    verb = Verb(
        id='http://adlnet.gov/expapi/verbs/%s' % verb_id,
        display=LanguageMap(verb_description),
    )
    print "...done"

    # construct the object of the statement
    print "constructing the Object..."
    object = Activity(
        id=activity_id,
        definition=activity_definition,
    )

    print "...done"

    # construct a context for the statement
    print "constructing the Context..."
    context = Context(
        registration=uuid.uuid4(),
        instructor=instructor)
    print "...done"

    # construct the actual statement
    print "constructing the Statement..."
    statement = Statement(
        actor=actor,
        verb=verb,
        object=object,
        context=context,
    )
    print "...done"

    # save our statement to the remote_lrs and store the response in 'response'
    print "saving the Statement..."
    response = lrs.save_statement(statement)

    if not response:
        raise ValueError("statement failed to save")
    print "...done"

    # retrieve our statement from the remote_lrs using the id returned in the response
    print "Now, retrieving statement..."
    response = lrs.retrieve_statement(response.content.id)

    if not response.success:
        raise ValueError("statement could not be retrieved")
    print "...done"

    return response.success
