#!/usr/bin/env python3

"""
Display JSON files with NER tag information using spacy.
B-I tags are merged into start/end character ranges.

When used from the command line, a <div>...</div> is printed out for a JSON input file.
"""


import os, sys
import spacy
from spacy import displacy
import json
import pandas as pd
import numpy as np

def tokenized_json_to_startend_ranges(jdict):
    """Concatenate tokenized text and combine entity tags with
    corresponding start/end character offset ranges.
    """
    texts_tagged = []
    for sjdict in jdict['sentences']:
        text = ' '.join(sjdict['content'])
        words = pd.Series(sjdict['content'])
        offsets = np.concatenate([[0], np.cumsum(words.apply(len).values+1)])
        texts_tagged += [{'text': text,
                          'ents': [dict(start=s,end=e,label=l) 
                                   for s,e,l in zip(offsets[:-1],
                                                    offsets[1:],
                                                    sjdict['ner']) if l != 'O'],
                          'title': None}]
    return texts_tagged

def read_email_json(emailpath):
    """Read JSON from file and convert tokenized entity labels to
    start/end notation.
    """
    with open(emailpath, 'r') as fh:
        jsonstr = fh.read()
        jdict = json.loads(jsonstr)
        return tokenized_json_to_startend_ranges(jdict)

ne_map = dict(PER='PERSON')

def map_ne_label(tag):
    try:
        return ne_map[tag]
    except:
        return tag

def merge_BI_ents(texts_tagged):
    """Convert B,I tags into tags with ranges"""
    texts_merged = []
    for text_tagged in texts_tagged:
        ents = text_tagged['ents']
        ents_merged = []
        last_b = None
        last_i = None
        for e in ents:
            if e['label'][0] != 'I':
                if last_b:
                    if last_i:
                        last_b['end'] = last_i['end']-1
                        last_i = None
                    last_b['label'] = map_ne_label(last_b['label'][2:])
                    ents_merged.append(last_b)
                last_b = e
            else:
                last_i = e
        if last_b:
            if last_i:
                last_b['end'] = last_i['end']-1
            last_b['label'] = map_ne_label(last_b['label'][2:])
            ents_merged.append(last_b)
        else:
            assert not last_i
        text_tagged['ents'] = ents_merged
        texts_merged.append(text_tagged)
    return texts_merged

def jdict_to_html(jdict):
    texts_tagged = tokenized_json_to_startend_ranges(jdict)
    texts_tagged = merge_BI_ents(texts_tagged)
    html = displacy.render(texts_tagged, style='ent', manual=True)
    return html

def json_file_to_html(emailpath):
    texts_tagged = read_email_json(emailpath)
    texts_tagged = merge_BI_ents(texts_tagged)
    html = displacy.render(texts_tagged, style='ent', manual=True)
    return html

if __name__ == '__main__':
    #jsonfiles = os.path.join('..','jsons','enron_mail_20150507')
    #emailpath = os.path.join(jsonfiles,'bass-e','inbox','249.json')
    for emailpath in sys.argv[1:]:
        print(json_file_to_html(emailpath))
