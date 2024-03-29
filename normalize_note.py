from email import charset
from importlib.resources import read_text
import re
from pathlib import Path
from utils import *
import logging

logging.basicConfig(filename="err.log",format='%(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def resolve_ms_with(collated_text,prev_end,note):
    if "+" in note["real_note"] or "-" in note["real_note"]:
        return

    note_start,note_end = note["span"]  
    if ":" in collated_text[prev_end:note_start]:
        index_set = set()
        left_syls = get_syls(note["left_context"])
        note_options = note["alt_options"]
        new_note = collated_text[note_start:note_end]
        for note_option in note_options:
            option_start,option_end = note_option["span"]
            tup = get_left_context_valid_word(note,note_option["note"])
            if tup:
                word,i = tup
                new_note = new_note[:option_start-note_start]+word+new_note[option_end-note_start:]
                index_set.add(i)

        if new_note != collated_text[note_start:note_end] and len(list(index_set)) == 1:
            left_syls = [token.text for token in get_tokens(note["left_context"])]
            before_default_word = convert_syl_to_word(left_syls[i:])
            new_default_word = before_default_word+note["default_option"]
            normalized_chunk=collated_text[prev_end:note_start-len(new_default_word)-1]+":"+new_default_word+new_note
            prev_end = note_end
            return normalized_chunk,prev_end
    return 


def resolve_msword_without(collated_text,prev_end,note):
    note_start,note_end = note["span"]
    if "+" in note["real_note"] or "-" in note["real_note"] or ":" in collated_text[prev_end:note_start]:
        return
    left_index = set()
    right_index = set()
    right_syls = get_syls(note["right_context"])
    left_syls = get_syls(note["left_context"])
    note_options = note["alt_options"]
    new_note = collated_text[note_start:note_end]
    for note_option in note_options:  
        tup = get_valid_word(note,note_option,new_note)
        if tup:   
            new_note,char_walker = tup
            if char_walker < 0:
                left_index.add(char_walker)
            else:
                right_index.add(char_walker)
    
    if new_note != collated_text[note_start:note_end] and len(right_index) <= 1 and len(left_index) <= 1:
        before_default_word = convert_syl_to_word(left_syls[list(left_index)[0]:]) if len(list(left_index)) != 0 else ""
        after_default_word = convert_syl_to_word(right_syls[:list(right_index)[0]+1]) if len(list(right_index)) != 0 else ""
        after_default_word = after_default_word.replace("།","")
        new_default_word = before_default_word+note["default_option"]+after_default_word
        default_minus = len(before_default_word)+len(note["default_option"]) 
        normalized_chunk =collated_text[prev_end:note_start-default_minus]+":"+new_default_word+new_note
        prev_end = note_end+len(after_default_word)
        return normalized_chunk,prev_end

    return 

    
def resolve_full_word_addition(collated_text,prev_end,note):
    if "+" in note["real_note"] and "-" not in note["real_note"]:     
        note_options = get_note_alt(note)
        note_start,note_end = note['span']
        new_note = collated_text[note_start:note_end]
        #left_syls = get_syls(re.sub(f'{note["default_option"]}$', '', note["left_context"]))
        index_set = set()
        for note_option in note_options:
            if "+" in note_option:
                left_syll = get_syls(note["left_context"])
                note["left_context"] = sum_up_syll(left_syll[:-1])
                tup = get_left_context_valid_word(note,note_option,left_syll[-1])
                if tup:
                    word,char_walker = tup
                    option_start,option_end = get_option_span(note,note_option)
                    new_note = new_note[:option_start-note_start]+word+note_option.replace("+","")+new_note[option_end-note_start:]
                    index_set.add(char_walker)
                    
        if new_note != collated_text[note_start:note_end] and len(list(index_set)) == 1:
            #new_left_word = convert_syl_to_word(get_syls(note["left_context"])[char_walker:])
            new_default_word = word
            if collated_text[note_start-len(note["default_option"])-1] == ":":
                dem_text = collated_text[prev_end:note_start].replace(":","")
                normalized_chunk = dem_text[:-len(word)]+":"+dem_text[-len(word):]+new_note
            else:
                new_left_context = collated_text[prev_end:note_start-len(word)]
                new_default_word = collated_text[note_start-len(new_default_word):note_start]
                normalized_chunk =new_left_context+":"+new_default_word+new_note
            prev_end = note_end
            return normalized_chunk,prev_end

    return   


def resolve_omission_with_sub(collated_text,prev_end,note):
    note_options = get_note_alt(note)
    if "-" in note["real_note"] and "+" not in note["real_note"] and len(note_options) == 1 and not re.search(".*<.*\(.*\).*>",note["real_note"]):
        note_start,note_end = note["span"]
        pyld_start,_ = get_payload_span(note)
        tup = side_note_valid_word(note)
        if not tup:
            x=1 if collated_text[note_start-len(note["default_option"])-1] == ":" else 0
            new_option = form_word(note)
            new_default_word = new_option+note["default_option"]
            if not new_default_word:
                return         
            new_left_context = collated_text[prev_end:note_start-len(new_default_word)-x]
            normalized_chunk = new_left_context+":"+new_default_word+collated_text[note_start:pyld_start]+new_option.strip()+">"
            return normalized_chunk,note_end

        left_word,right_word = tup
        new_payload = left_word+right_word
        normalized_payload = new_payload.replace("།","་")
        x=1 if collated_text[note_start-len(note["default_option"])-1] == ":" else 0
        new_left_context = collated_text[prev_end:note_start-len(note["default_option"])-len(left_word)-x]
        new_default_word = collated_text[note_start-len(note["default_option"])-len(left_word)-x:note_start].replace(":","")+right_word
        normalized_chunk =new_left_context +":"+ new_default_word+collated_text[note_start:pyld_start]+normalized_payload+">" 
        prev_end = note_end +len(right_word)
        return normalized_chunk,prev_end

    return


def form_word(note):
    left_context = note["left_context"]
    tokens = get_tokens(left_context)
    new_default_word = ""
    for token in reversed(tokens):
        new_default_word=token.text+new_default_word
        if token.pos not in ["PUNCT","PART"] and token.text.strip() != "།":
            return new_default_word
    return        


def resolve_long_omission_with_sub(collated_text,prev_end,note):
    if re.search("\.+",note['real_note']) and "-" in note["real_note"] and not re.search(".*<.*\(.*\).*>",note["real_note"]):
        _,note_end = note["span"]
        pyld_start,_ = get_payload_span(note)
        z = re.match("(.*<)(«.*»)+\-([^.]+).....(.*)>",note['real_note'])
        first_word = z.group(3)
        last_word = z.group(4)
        normalized_chunk = collated_text[prev_end:pyld_start]+first_word+"<ཅེས་/ཞེས་/ཤེས་>པ་ནས་"+last_word+"<ཅེས་/ཞེས་/ཤེས་>པའི་བར་ཆད།>"
        prev_end = note_end
        return normalized_chunk,prev_end
    return
    


def resolve_long_add_with_sub(collated_text,prev_end,cur_note,next_note,notes_iter):
    if notes_iter == None:
        return   
    cur_note_options = get_note_alt(cur_note)
    next_note_options = get_note_alt(next_note)    
    cur_start,cur_end = cur_note["span"]
    next_start,next_end = next_note["span"]  
    left_syls = get_syls(cur_note["left_context"])
    
    if next_start != cur_end or 1 not in {len(cur_note_options),len(next_note_options)}:
        return

    if '-' in cur_note_options[0] and '+' in next_note_options[0]:
        left_syll = get_syls(cur_note["left_context"])
        cur_note["left_context"] = sum_up_syll(left_syll[:-1])
        tup = get_left_context_valid_word(cur_note,cur_note_options[0],left_syll[-1])
        if tup:
            word,char_walker = tup
            next_pyld_start,next_pyld_end = get_payload_span(next_note)
            left_syls = [token.text for token in get_tokens(cur_note["left_context"])]
            before_default_word = convert_syl_to_word(left_syls[char_walker-1:])
            new_default_word = collated_text[cur_start-len(before_default_word+cur_note["default_option"]):cur_start]
            new_left_context = collated_text[prev_end:cur_start-len(new_default_word)]
            new_next_note = collated_text[next_start:next_pyld_start]+word+collated_text[next_pyld_start+1:next_pyld_end]+">"
            normalized_chunk = new_left_context+":"+new_default_word+new_next_note
            prev_end = next_end
            next(notes_iter)
            return normalized_chunk,prev_end
                     
    return   

def get_valid_word(note,note_option,new_note):
    start,_ = note["span"]
    option_start,option_end = note_option["span"]
    tup_minus = get_left_context_valid_word(note,note_option["note"])
    tup_plus = get_right_context_valid_word(note,note_option["note"])
    if not tup_minus and not tup_plus:
        return False
    elif not tup_plus:
        word,char_walker = tup_minus
        new_note = new_note[:option_start-start]+word+new_note[option_end-start:]
        return new_note,char_walker
    elif not tup_minus:
        word,char_walker = tup_plus
        new_note = new_note[:option_start-start]+word+new_note[option_end-start:]
        return new_note,char_walker
    return 


def side_note_valid_word(note): 
    left_syls = get_syls(note["left_context"])
    right_syls = get_syls(note["right_context"])
    left_index = 3 if len(left_syls) >= 3 else len(left_syls)
    right_index = 3 if len(right_syls) >= 3 else len(right_syls)

    for i in range(left_index-1,-1,-1):
        for j in range(0,right_index):
            left_word = sum_up_syll(left_syls[i+1:])
            right_word = sum_up_syll(right_syls[:j+1])
            word =left_word + right_word
            if is_word(word):
                return left_word,right_word
    return

def get_left_context_valid_word(note,note_option,word=None):
    char_walker=-1
    pass_word = word
    if word == None:
        word = note_option.replace("+","")
    left_syls = get_syls(note["left_context"])
    if len(left_syls) == 0 or left_syls[-1].strip()[-1] == "།":
        return
    while char_walker >= -len(left_syls) and char_walker>=-3:
        word=left_syls[char_walker]+word
        if is_word(word):
            if left_syls[char_walker][-1].strip() in ("།"):
                return word[1:],char_walker
            return word,char_walker
        char_walker-=1
    return



def get_right_context_valid_word(note,note_option,word=None):
    char_walker=0
    pass_word = word
    if word == None:
        word = note_option.replace("།","་")
    right_syls = get_syls(note["right_context"])
    if len(right_syls) == 0 or right_syls[0][0].strip() == "།":
        return
    while char_walker < len(right_syls) and char_walker<3:
        word = word+right_syls[char_walker]          
        if is_word(word):
            if right_syls[char_walker][-1] == "།":
                return word[:-1],char_walker
            else:
                return word,char_walker
        char_walker+=1
    return


def normalize_note(collated_text,prev_end,cur_note,next_note=None,notes_iter=None):
    if tup := resolve_long_add_with_sub(collated_text,prev_end,cur_note,next_note,notes_iter):
        normalized_chunk,prev_end = tup
        print("5")
    elif tup := resolve_ms_with(collated_text,prev_end,cur_note):
        normalized_chunk,prev_end = tup
        print("13")
    elif tup := resolve_msword_without(collated_text,prev_end,cur_note):
        normalized_chunk,prev_end = tup
        print("11")
    elif tup := resolve_long_omission_with_sub(collated_text,prev_end,cur_note):
        normalized_chunk,prev_end = tup
        print("2")
    elif tup := resolve_omission_with_sub(collated_text,prev_end,cur_note):
        normalized_chunk,prev_end = tup
        print("17")
    elif tup := resolve_full_word_addition(collated_text,prev_end,cur_note):
        normalized_chunk,prev_end = tup
        print("4")
    else:
        _,end = cur_note["span"]
        normalized_chunk=collated_text[prev_end:end]
        prev_end = end

    return normalized_chunk,prev_end


def get_right_context_valid_word_v1(note,note_option,word=None):
    char_walker=0
    if word == None:
        word = note_option.replace("།","་")
    right_syls = get_tokens(note["right_context"])
    while char_walker < len(right_syls) and char_walker<3:
        word = word+right_syls[char_walker].text
        if right_syls[char_walker].text == "།":
            break
        elif get_token_pos(right_syls[char_walker].text) not in ["NON_WORD"]:
            return word,char_walker
        char_walker+=1
    return False

def get_left_context_valid_word_v1(note,note_option,word=None):
    char_walker=-1
    if word == None:
        word = note_option.replace("+","")
    left_syls = get_tokens(note["left_context"])
    if left_syls[-1].text in ("།","། །"):
        return False
    while char_walker >= -len(left_syls) and char_walker>=-3:
        prev_word = word
        word=left_syls[char_walker].text+word
        if left_syls[char_walker].text in ("།","། །"):
            return prev_word,char_walker+1
        elif get_token_pos(left_syls[char_walker].text) not in ["NON_WORD","PART"]:
            return word,char_walker
        char_walker-=1
    return False

def get_normalized_text(collated_text):
    normalized_collated_text = ""
    prev_end = 0
    notes = get_notes(collated_text)
    notes_iter = iter(enumerate(notes,0)) 
    for note_iter in notes_iter:
        index,cur_note = note_iter
        start,end = cur_note["span"]
        if index <len(notes)-1:
            next_note = notes[index+1]
            normalized_chunk,prev_end = normalize_note(collated_text,prev_end,cur_note,next_note,notes_iter)     
        else:
            normalized_chunk,prev_end = normalize_note(collated_text,prev_end,cur_note)  
        normalized_collated_text+=normalized_chunk

    normalized_collated_text+=collated_text[prev_end:]

    return normalized_collated_text  


if __name__ == "__main__":
    
    paths = Path("./clean_base_collated_text").iterdir()
    collated_text = Path("./test.txt").read_text(encoding="utf-8")
    normalized_collated_text = get_normalized_text(collated_text)
    Path("./gen_test.txt").write_text(normalized_collated_text)

    """ for path in paths:
        collated_text = path.read_text(encoding='utf-8')
        try:
            normalized_collated_text = get_normalized_text(collated_text)
            logger.info(str(path)+"DONE")
            
        except:
            logger.info(str(path)+"ERR") """
                