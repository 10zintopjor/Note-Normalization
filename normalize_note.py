import re
from pathlib import Path
from pyparsing import col
from requests import patch
from utils import get_notes
from botok import WordTokenizer


normalized_collated_text = ""
prev_end = 0

def normalize_note(cur_note,next_note=None):
    global normalized_collated_text,prev_end
    if resolve_long_omission_with_sub(cur_note):
        pass
    elif resolve_omission_with_sub(cur_note):
        pass
    elif resolve_full_word_addition(cur_note):
        pass
    elif resolve_long_add_with_sub(cur_note,next_note):
        pass
    else:
        start,end = cur_note["span"]
        normalized_collated_text+=collated_text[prev_end:end]
        prev_end = end

def resolve_full_word_addition(note):
    global normalized_collated_text,prev_end
    note_options = get_note_alt(note)
    if len(note_options) == 1 and '+' in note_options[0]:
        start,end = note['span']
        pyld_start,pyld_end = get_payload_span(note)
        index_sub = start-len(note_options[0])-1
        while collated_text[index_sub] != "་":
            index_sub-=1
        new_pyld =  collated_text[index_sub+1:start] + collated_text[pyld_start+1:pyld_end]   
        normalized_collated_text+=collated_text[prev_end:index_sub+1]+":"+collated_text[index_sub+1:start]+collated_text[start:pyld_start]+new_pyld+">"
        prev_end=end
        return True
    return False        
        


def resolve_omission_with_sub(note):
    global normalized_collated_text,prev_end
    note_options = get_note_alt(note)
    if len(note_options) == 1 and '-' in note_options[0]:
        start,end = note['span']
        pyld_start,pyld_end = get_payload_span(note)
        index_sub = start-len(note_options[0])-1
        while collated_text[index_sub] != "་":
            index_sub-=1
        index_plus = end    
        while collated_text[index_plus] != "་":
            index_plus+=1
        new_payload = collated_text[index_sub+1:start-len(note_options[0])+1]+collated_text[end:index_plus+1]
        normalized_collated_text+=collated_text[prev_end:index_sub+1]+":"+collated_text[index_sub+1:start]+collated_text[end:index_plus+1]+collated_text[start:pyld_start]+new_payload+">"
        prev_end = end+len(collated_text[end:index_plus+1])
        return True

    return False    


def resolve_long_omission_with_sub(note):
    global normalized_collated_text,prev_end
    if '.....' in note['real_note']:
        _,end = note["span"]
        pyld_start,pyld_end = get_payload_span(note)
        z = re.match("(.*<)(«.*»)+([^.]+).....(.*)>",note['real_note'])
        first_word = z.group(3)
        last_word = z.group(4)
        normalized_collated_text += collated_text[prev_end:pyld_start]+first_word+"<ཅེས་/ཞེས་/ཤེས་>པ་ནས་"+last_word+"<ཅེས་/ཞེས་/ཤེས་>པ་ནས་>"
        prev_end = end
        return True
    
    return False
    


def resolve_long_add_with_sub(cur_note,next_note):
    global normalized_collated_text,prev_end
    if next_note == None:
        return False
    cur_note_options = get_note_alt(cur_note)
    next_note_options = get_note_alt(next_note)    
    cur_start,cur_end = cur_note["span"]
    next_start,next_end = next_note["span"]    
    if next_start != cur_end:
        return False  

    if 1 in {len(cur_note_options),len(next_note_options)}:
        if '-' in cur_note_options[0] and '+' in next_note_options[0]:
            normalized_collated_text += collated_text[prev_end:cur_start-len(cur_note_options[0])+1]+collated_text[next_start:next_end]
            prev_end = next_end
            return True
            
    return False         

def get_payload_span(note):
    real_note = note['real_note']
    z = re.match("(.*<)(«.*»)+(.*)>",real_note)
    start,end = note["span"]
    pyld_start = start+len(z.group(1))+len(z.group(2))
    pyld_end = pyld_start + len(z.group(3))

    return pyld_start,pyld_end

def get_note_alt(note):
    note_parts = re.split('(«པེ་»|«སྣར་»|«སྡེ་»|«ཅོ་»|«པེ»|«སྣར»|«སྡེ»|«ཅོ»)',note['real_note'])
    notes = note_parts[2::2]
    options = []

    for note in notes:
        if note != "":
            options.append(note.replace(">",""))

    return options

def get_tokens(wt, text):
    tokens = wt.tokenize(text, split_affixes=False)
    return tokens

def is_valid_token():
    wt = WordTokenizer()
    text = "བཀྲ་ཤིས་བདེ་ལེགས་ཞུས་རྒྱུ་ཡིན་ སེམས་པ་སྐྱིད་པོ་འདུག།"
    tokens = get_tokens(wt, text)   

def main():
    global collated_text,normalized_collated_text
    collated_text = Path("./test.txt").read_text(encoding="utf-8")
    notes = get_notes(collated_text)
    for index,note in enumerate(notes,0):
        if len(notes) > index+1:
            normalize_note(notes[index],notes[index+1])
        else:
            normalize_note(notes[index]) 
            normalized_collated_text+=collated_text[prev_end:]   


if __name__ == "__main__":
    main()
    Path("./gen_test.txt").write_text(normalized_collated_text)

    
