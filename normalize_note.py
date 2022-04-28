import re
from pathlib import Path
from requests import patch
from utils import get_notes,get_syls
from botok import WordTokenizer

wt = WordTokenizer()
normalized_collated_text = ""
prev_end = 0


def normalize_note(cur_note,next_note=None):
    global normalized_collated_text,prev_end
    if resolve_mono_syllable(cur_note):
        pass
    elif resolve_msword_without(cur_note):
        print("1")
        pass
    elif resolve_long_omission_with_sub(cur_note):
        print("2")
        pass
    elif resolve_omission_with_sub(cur_note):
        print("3x")
        pass
    elif resolve_full_word_addition(cur_note):
        print("4")
        pass
    elif resolve_long_add_with_sub(cur_note,next_note):
        print("5")
        pass
    else:
        start,end = cur_note["span"]
        normalized_collated_text+=collated_text[prev_end:end]
        prev_end = end


def resolve_mono_syllable(note):      
    global normalized_collated_text,prev_end
    note_options = get_note_alt(note)
    if not is_mono_syll(note_options):
        return False
    if len(note_options) == 1:
        start,end = note['span']
        pyld_start,pyld_end = get_payload_span(note)
        if is_valid_word(note_options[0]):
            normalized_collated_text+=collated_text[prev_end:start-len(note['default_option'])]+":"+collated_text[start-len(note['default_option']):pyld_start]+note['default_option']+">"
            prev_end = end
            return True
    return False        


def is_mono_syll(word):
    syl = get_syls(word)
    if len(syl) == 1:
        return True
    return False        


def is_valid_word(word):
    tokens = get_tokens(wt, word)
    for token in tokens:
        if token.pos != "NON_WORD":
            return True
    return False        


def resolve_msword_without(note):
    global normalized_collated_text,prev_end
    note_options = get_note_alt(note)
    if "+" in note_options[0] or "-" in note_options[0]:
        return False
    if len(note_options) == 1:
        start,end = note['span']
        pyld_start,pyld_end = get_payload_span(note)
        i=-1
        left_syls = get_syls(note["left_context"])
        right_syls = get_syls(note["right_context"])

        word = ""
        while i > -len(left_syls):
            word=left_syls[i]+word
            if check_token_validity(word,note['default_option']):
                normalized_collated_text+=collated_text[prev_end:start-len(word+note['default_option'])]+":"+word+note['default_option']+collated_text[start:pyld_start]+word+note_options[0]+">"
                prev_end =end
                return True
            i-=1
        i=0
        word = ""
        while i < len(right_syls):
            word = word + right_syls[i]
            if check_token_validity(note["default_option"],word):
                normalized_collated_text+=collated_text[prev_end:start-len(note['default_option'])]+":"+note['default_option']+word+collated_text[start:pyld_start]+note_options[0]+word+">"
                prev_end = end + len(word)
                return True
            i+=1
    return False


def resolve_msword_split_by_marker(note):
    global normalized_collated_text,prev_end
    note_options = get_note_alt(note)
    if len(note_options) == 1:
        start,end = note['span']
        pyld_start,pyld_end = get_payload_span(note)
        index_sub = start-2
        index_plus,index_sub = get_indexes(note,index_sub)
        left_contxt_syl = get_syls(note['left_context'])
        right_contxt_syl = get_syls(note['right_context'])

        after_note_word = collated_text[end:index_plus+1]
        before_note_word = collated_text[index_sub+1:start]
        is_valid_token = check_token_validity(before_note_word,after_note_word)
        if is_valid_token:
            normalized_collated_text+=collated_text[prev_end:index_sub+1]+":"+before_note_word+after_note_word+collated_text[start:pyld_start]+note_options[0]+after_note_word+">"
            prev_end=end+len(after_note_word)
            return True
    return False


def resolve_full_word_addition(note):
    global normalized_collated_text,prev_end
    note_options = get_note_alt(note)
    if len(note_options) == 1 and '+' in note_options[0]:
        start,end = note['span']
        pyld_start,pyld_end = get_payload_span(note)
        index_sub = start-2
        index_plus,index_sub = get_indexes(note,index_sub)
        left_syls = get_syls(note["left_context"])
        word = ""
        i=-1
        while i > -len(left_syls):
            word=left_syls[i]+word
            if check_token_validity(left_syls[i]):
                normalized_collated_text+=collated_text[prev_end:start-len(word)]+":"+word+collated_text[start:pyld_start]+word+note_options[0].replace("+","")+">"
                prev_end =end
                return True
            i-=1
    return False        



def resolve_omission_with_sub(note):
    global normalized_collated_text,prev_end
    note_options = get_note_alt(note)
    if len(note_options) == 1 and '-' in note_options[0]:
        start,end = note['span']
        pyld_start,pyld_end = get_payload_span(note)
        index_sub = start-len(note_options[0])-1
        index_plus,index_sub = get_indexes(note,index_sub)
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


def check_token_validity(word):
    tokens = get_tokens(wt, word)
    for token in tokens:
        print(token.pos)
        if token.pos not in ["NON_WORD","PART"]:
            return True
    return False


def get_indexes(note,index_sub):
    start,end = note['span']
    while collated_text[index_sub] != "་":
            index_sub-=1
    index_plus = end    
    while collated_text[index_plus] != "་":
        index_plus+=1    

    return index_plus,index_sub 


def get_normalized_text(collated_text):
    global normalized_collated_text
    notes = get_notes(collated_text)
    for index,note in enumerate(notes,0):
        if len(notes) > index+1:
            normalize_note(notes[index],notes[index+1])
        else:
            normalize_note(notes[index]) 
            normalized_collated_text+=collated_text[prev_end:]
    return normalized_collated_text  


if __name__ == "__main__":
    collated_text = Path('./test.txt').read_text(encoding='utf-8')
    normalized_collated_text = get_normalized_text(collated_text)
    Path("./gen_test.txt").write_text(normalized_collated_text)

    

