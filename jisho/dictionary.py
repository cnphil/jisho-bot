import urllib.request, json
import urllib.parse
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def extract_def(definition_data):
    word = ''
    reading = ''
    parts_of_speech = ''
    english_definition_datas = ''
    if 'word' in definition_data['japanese'][0]:
        word = definition_data['japanese'][0]['word']
    if 'reading' in definition_data['japanese'][0]:
        reading = definition_data['japanese'][0]['reading']
    if 'parts_of_speech' in definition_data['senses'][0]:
        parts_of_speech = ', '.join(definition_data['senses'][0]['parts_of_speech'])
    if 'english_definitions' in definition_data['senses'][0]:
        english_definitions = ', '.join(definition_data['senses'][0]['english_definitions'])
    # TODO(philhu): Use namedtuple instead of dict.
    return {'word':word, 'reading':reading, 'parts_of_speech':parts_of_speech, 'english_definitions':english_definitions}

def render_def(definition):
    return definition['word'] + '（' + definition['reading'] + '）\n' + definition['parts_of_speech'] + ': ' + definition['english_definitions']

def render_word(definition):
    """ Renders the definition to be Anki's word field
    """
    if definition['word'] == '':
        return definition['reading']
    return definition['word']

def render_reading(definition):
    """ Renders the definition to be Anki's reading field
    """
    return definition['reading']

def render_definition(definition):
    """ Renders the definition to be Anki's definition field
    """
    return definition['parts_of_speech'] + ': ' + definition['english_definitions']

def query_jisho(query):
    """ Returns (rendering_of_defition, definition)
    """
    query_url = "https://jisho.org/api/v1/search/words?keyword=" + urllib.parse.quote(query)
    logger.info(query_url)
    with urllib.request.urlopen(query_url) as url:
        data = json.loads(url.read().decode())
        if (data['meta']['status'] != 200) or (len(data['data']) == 0):
            return '見つからない。', None
        else:
            definition = extract_def(data['data'][0])
            return render_def(definition), definition
