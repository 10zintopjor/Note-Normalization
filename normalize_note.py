from http.client import IM_USED
from operator import truediv
import re
from pathlib import Path
from socket import AI_PASSIVE
from requests import patch
from utils import get_notes,get_syls
from botok import WordTokenizer

wt = WordTokenizer()
normalized_collated_text = ""
prev_end = 0

def normalize_note(cur_note,next_note=None):
    global normalized_collated_text,prev_end
    if resolve_msword_without(cur_note):
        print("11")
        pass
    elif resolve_msword_split_by_marker(cur_note):
        print("10")
        pass
    if resolve_long_omission_with_sub(cur_note):
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

# two ore more options not resolved
#mono syllable word clashing with other condition needed
def resolve_mono_syllable(note):      
    global normalized_collated_text,prev_end
    note_options = note["alt_options"]
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

#Solved
def resolve_msword_without(note):
    global normalized_collated_text,prev_end
    note_options = note["alt_options"]
    if "+" in note["real_note"] or "-" in note["real_note"]:
        return False
    i=-1
    left_syls = get_syls(note["left_context"])
    start,end = note["span"]
    index_minus = set()
    new_note = collated_text[start:end]
    for note_option in reversed(note_options):
        word = note_option["note"]
        option_start,option_end = note_option["span"]
        while i >= -len(left_syls) and i >= -3:
            word=left_syls[i]+word
            if get_token_pos(left_syls[i]) not in ["NON_WORD","PART"]:
                new_note = new_note[:option_start-start]+word+new_note[option_end-start:]
                index_minus.add(i)
                break             
            i-=1
    if new_note != collated_text[start:end] and len(list(index_minus)) == 1:
        before_default_word = convert_syl_to_word(left_syls[i:])
        normalized_collated_text+=collated_text[prev_end:start-len(note["default_option"])-len(before_default_word)]+":"+collated_text[start-len(note["default_option"])-len(before_default_word):start]+new_note
        prev_end = end
        return True

    return False

#resolve_msword_without and resolve_msword_split_by_marker clashing which one to be put first
# almost solved doubt if option_start ==option end 
#can default option be empty?

def resolve_msword_split_by_marker(note):
    global normalized_collated_text,prev_end
    note_options = note["alt_options"]
    if "+" in note["real_note"] or "-" in note["real_note"]:
        return False
    i=0
    right_syls = get_syls(note["right_context"])
    start,end = note["span"]
    new_note = collated_text[start:end]
    index_plus = set()

    for note_option in reversed(note_options):
        word = note_option["note"].replace("།","་")
        option_start,option_end = note_option['span']
        while i < len(right_syls) and i<3:
            word = word+right_syls[i]
            if get_token_pos(right_syls[i]) != "NON_WORD":
                new_note = new_note[:option_start-start]+word+new_note[option_end-start:]
                index_plus.add(i)
                break
            i+=1
            
    if new_note != collated_text[start:end] and len(list(index_plus)) == 1:
        after_note_word = convert_syl_to_word(right_syls[:i+1])
        normalized_collated_text+=collated_text[prev_end:start-len(note["default_option"])]+":"+collated_text[start-len(note["default_option"]):start]+after_note_word+new_note
        prev_end=end+len(after_note_word)
        return True

    return False

#almost done
def resolve_full_word_addition(note):
    global normalized_collated_text,prev_end
    if "+" in note["real_note"] and "-" not in note["real_note"]:     
        note_options = get_note_alt(note)
        start,end = note['span']
        new_note = collated_text[start:end]
        index_minus = set()
        for note_option in reversed(note_options):
            left_syls = get_syls(note["left_context"])
            word = note_option.replace("+","")
            if "+" in note_option:
                i=-1
                while i > -len(left_syls) and i >= -3:
                    word=left_syls[i]+word
                    if get_token_pos(left_syls[i]) not in ["NON_WORD","PART"]:
                        option_start,option_end = get_option_span(note,note_option)
                        new_note = new_note[:option_start-start]+word+new_note[option_end-start:]
                        index_minus.add(i)
                        break
                    i-=1
        if new_note != collated_text[start:end] and len(list(index_minus)) == 1:
            before_default_word = convert_syl_to_word(left_syls[i:])
            normalized_collated_text+=collated_text[prev_end:start-len(before_default_word)]+":"+collated_text[start-len(before_default_word):start]+new_note
            prev_end = end
        return True

    return False   

#almost done
def resolve_omission_with_sub(note):
    global normalized_collated_text,prev_end
    note_options = get_note_alt(note)
    if "-" in note["real_note"] and "+" not in note["real_note"] and len(note_options) == 1:
        i_plus=0
        berfore_note=""
        after_note=""
        right_syls = get_syls(note["right_context"])
        left_syls = get_syls(note["left_context"])
        start,end = note["span"]
        while i_plus < len(right_syls) and i_plus<3:
            if get_token_pos(right_syls[i_plus]) != "NON_WORD":
                after_note = after_note+right_syls[i_plus]
                break
            i_plus+=1
        i_minus=-1
        while i_minus > -len(left_syls) and i_minus >= -3:
            if get_token_pos(left_syls[i_minus]) not in ["NON_WORD","PART"]:
                berfore_note=left_syls[i_minus]+berfore_note
                break
            i-=1
        pyld_start,_ = get_payload_span(note)    
        if (i_plus < len(right_syls) and i_plus<3) or (i_minus > -len(left_syls) and i_minus >= -3):
            normalized_collated_text+= collated_text[prev_end:start]+after_note+collated_text[start:pyld_start]+berfore_note+after_note+">" 
            prev_end = end+len(after_note)
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

def is_mono_syll(words):
    bool_set =set()
    for word in words:
        syl = get_syls(word['note'])
        if len(syl) == 1:
            bool_set.add(True)
    if False in bool_set:
        return False
    else:
        return True         


def convert_syl_to_word(syls):
    word = ""
    for syl in syls:
        word += syl
    return word


def is_valid_word(word):
    tokens = get_tokens(wt, word['note'])
    for token in tokens:
        if token.pos != "NON_WORD":
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

def get_option_span(note,option):
    start,end = note["span"]
    z = re.search(f"\{option}",note["real_note"])
    option_start = start+z.start()
    option_end = start+z.end()
    return option_start,option_end

def get_tokens(wt, text):
    tokens = wt.tokenize(text, split_affixes=False)
    return tokens

def get_token_pos(sylb):
    tokens = get_tokens(wt, sylb)
    for token in tokens:
        return token.pos


def replace_tsek(removed_tsek_altword,default_option):
    if removed_tsek_altword[-1] == "།" and default_option[-1] == "་":
        removed_tsek_altword = removed_tsek_altword[:-1]+"་"
    elif removed_tsek_altword[-1] != "་" and default_option[-1] == "་":
        removed_tsek_altword+="་"
    return removed_tsek_altword   


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

    

