import os
import tempfile
from contextlib import contextmanager

from dictionary import render_word, render_reading, render_definition

@contextmanager
def output_anki_tsv(definitions):
    """ Returns a StringIO file of the Anki TSV file.
    """
    tempf = tempfile.NamedTemporaryFile(mode='w', delete=False)
    for definition in definitions:
        line = f'{render_word(definition)}\t{render_reading(definition)}\t{render_definition(definition)}\n'
        tempf.write(line)
    tempf.close()
    try:
        yield tempf.name
    finally:
        os.unlink(tempf.name)

