from io import BytesIO

from dictionary import render_word, render_reading, render_definition

def output_anki_tsv(definitions):
    """ Returns a StringIO file of the Anki TSV file.
    """
    tempf = BytesIO()
    for definition in definitions:
        line = render_word(definition) + '\t' + render_reading(definition) + '\t' + render_definition(definition) + '\n'
        tempf.write(line.encode())
    tempf.seek(0)
    return tempf
