import wit
import config


def call_wit(query):

    res = {}
    response = wit.message(config.access_token, query)
    outcome = response['outcomes'][0]

    intent = outcome['intent']
    res['intent'] = intent

    entities = outcome['entities']

    if 'location' in entities:
        location = entities['location'][-1]
        if location['suggested']:
            res['location'] = location['value']

    if 'search_query' in entities:
        search = entities['search_query'][-1]
        if search['suggested']:
            res['search'] = search['value']

    return res

if __name__ == '__main__':
    call_wit("Delhi good hotels with amazing pools")
