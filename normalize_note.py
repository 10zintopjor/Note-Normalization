from email import charset
import re
from pathlib import Path
from utils import get_notes,get_syls
from botok import WordTokenizer

#ISSUES
#(༤) <«པེ་»«སྣར་»དྲི་མ་སྲེག> །དེ་ཉིད་འོད་གསལ་མ་ཡིན་ནོ། shey after space
#།ཆོས་ཉིད་སྟོང་པ་མཐོང་གྱུར་ནས།(༤) <«པེ་»«སྣར་»+པདྨ་ཆེན་པོའི་རང་བཞིན་གྱིས།> shey in note
#།བརྟེན་ནས་འབྱུང་བར་གྱུར་པ་(༥) <«པེ་»«སྣར་»འགྱུར་བ་>དང་། : not present,default word error

wt = WordTokenizer()


def resolve_ms_with(collated_text,prev_end,note):
    if "+" in note["real_note"] or "-" in note["real_note"]:
        return False
    start,end = note["span"]  
      
    if ":" in collated_text[prev_end:start]:
        index_set = set()
        left_syls = get_syls(note["left_context"])
        note_options = note["alt_options"]
        new_note = collated_text[start:end]
        for note_option in note_options:
            option_start,option_end = note_option["span"]
            tup = get_left_context_valid_word_v1(note,note_option["note"])
            if tup!=False:
                word,i = tup
                new_note = new_note[:option_start-start]+word+new_note[option_end-start:]
                index_set.add(i)

        if new_note != collated_text[start:end] and len(list(index_set)) == 1:
            left_syls = [token.text for token in get_tokens(note["left_context"])]
            before_default_word = convert_syl_to_word(left_syls[i:])
            new_default_word = before_default_word+note["default_option"]
            normalized_chunk=collated_text[prev_end:start-len(new_default_word)-1]+":"+new_default_word+new_note
            prev_end = end
            return normalized_chunk,prev_end
    return False    


def resolve_msword_without(collated_text,prev_end,note):
    start,end = note["span"]
    if "+" in note["real_note"] or "-" in note["real_note"] or ":" in collated_text[prev_end:start]:
        return False
    index_minus = set()
    index_plus = set()
    right_syls = get_syls(note["right_context"])
    left_syls = get_syls(note["left_context"])
    note_options = note["alt_options"]
    new_note = collated_text[start:end]
    for note_option in note_options:  
        ret_val = get_valid_word(note,note_option,new_note)
        if ret_val != False:   
            new_note,char_walker = ret_val
            if char_walker < 0:
                index_minus.add(char_walker)
            else:
                index_plus.add(char_walker)
    
    if new_note != collated_text[start:end] and len(index_plus) <= 1 and len(index_minus) <= 1:
        before_default_word = convert_syl_to_word(left_syls[list(index_minus)[0]:]) if len(list(index_minus)) != 0 else ""
        after_default_word = convert_syl_to_word(right_syls[:list(index_plus)[0]+1]) if len(list(index_plus)) != 0 else ""
        after_default_word = after_default_word.replace("།","")
        new_default_word = before_default_word+note["default_option"]+after_default_word
        default_minus = len(before_default_word)+len(note["default_option"]) 
        normalized_chunk =collated_text[prev_end:start-default_minus]+":"+new_default_word+new_note
        prev_end = end+len(after_default_word)
        return normalized_chunk,prev_end

    return False

    
def resolve_full_word_addition(collated_text,prev_end,note):
    if "+" in note["real_note"] and "-" not in note["real_note"]:     
        note_options = get_note_alt(note)
        start,end = note['span']
        new_note = collated_text[start:end]
        left_syls = get_syls(re.sub(f'{note["default_option"]}$', '', note["left_context"]))
        index_set = set()
        for note_option in note_options:
            if "+" in note_option:
                tup = get_left_context_valid_word_v1(note,note_option,"")
                if tup != False:
                    word,char_walker = tup
                    option_start,option_end = get_option_span(note,note_option)
                    new_note = new_note[:option_start-start]+word+note_option.replace("+","")+new_note[option_end-start:]
                    index_set.add(char_walker)
                    
        if new_note != collated_text[start:end] and len(list(index_set)) == 1:
            left_syls = [token.text for token in get_tokens(note["left_context"])]
            new_default_word = convert_syl_to_word(left_syls[char_walker:])
            if collated_text[start-len(note["default_option"])-1] == ":":
                dem_text = collated_text[prev_end:start].replace(":","")
                normalized_chunk = dem_text[:-len(word)]+":"+dem_text[len(word):]+new_note
            else:
                normalized_chunk =collated_text[prev_end:start-len(new_default_word)]+":"+collated_text[start-len(new_default_word):start]+new_note
            prev_end = end
            return normalized_chunk,prev_end

    return False   


def resolve_omission_with_sub(collated_text,prev_end,note):
    note_options = get_note_alt(note)
    if "-" in note["real_note"] and "+" not in note["real_note"] and len(note_options) == 1 and "(" not in note["real_note"]:
        word = ""
        before_note = ""
        after_note = ""

        i_plus = 10
        i_sub = -10
        right_syls = get_syls(note["right_context"])
        left_syls = get_syls(note["left_context"])
        start,end = note["span"]
        tup = get_right_context_valid_word_v1(note,note_options[0],word)
        if tup != False:
            after_note,i_plus = tup
        tup = get_left_context_valid_word_v1(note,note_options[0],word)
        if tup != False:
            before_note,i_sub = tup

        left_syls = [token.text for token in get_tokens(note["left_context"])]
        right_syls = [token.text for token in get_tokens(note["right_context"])]

        if (i_plus < len(right_syls) and i_plus<3) or (i_sub > -len(left_syls) and i_sub >= -3):
            pyld_start,_ = get_payload_span(note)    
            new_default_word = before_note+note["default_option"]
            normalized_before_note = before_note[:-1] if collated_text[end] == "།" else before_note
            if collated_text[start-len(note["default_option"])-1] == ":":
                if before_note != "" and before_note != '།':
                    normalized_chunk =collated_text[prev_end:start-len(note["default_option"])-len(before_note)-1]+":"+collated_text[start-len(note["default_option"])-len(before_note)-1:start].replace(":","")+after_note+collated_text[start:pyld_start]+normalized_before_note+after_note+">" 
                else:    
                    normalized_chunk =collated_text[prev_end:start]+after_note+collated_text[start:pyld_start]+normalized_before_note+after_note+">" 
            else:
                normalized_chunk = collated_text[prev_end:start-len(new_default_word)]+":"+collated_text[start-len(new_default_word):start]+after_note+collated_text[start:pyld_start]+normalized_before_note+after_note+">" 
            prev_end = end+len(after_note)
            return normalized_chunk,prev_end

    return False    



def resolve_long_omission_with_sub(collated_text,prev_end,note):
    if re.search("\.+",note['real_note']) and "-" in note["real_note"] and "(" not in note["real_note"]:
        _,end = note["span"]
        pyld_start,_ = get_payload_span(note)
        z = re.match("(.*<)(«.*»)+\-([^.]+).....(.*)>",note['real_note'])
        first_word = z.group(3)
        last_word = z.group(4)
        normalized_chunk = collated_text[prev_end:pyld_start]+first_word+"<ཅེས་/ཞེས་/ཤེས་>པ་ནས་"+last_word+"<ཅེས་/ཞེས་/ཤེས་>པའི་བར་ཆད།>"
        prev_end = end
        return normalized_chunk,prev_end
    return False
    


def resolve_long_add_with_sub(collated_text,prev_end,cur_note,next_note,notes_iter):
    if notes_iter == None:
        return False   
    cur_note_options = get_note_alt(cur_note)
    next_note_options = get_note_alt(next_note)    
    cur_start,cur_end = cur_note["span"]
    next_start,next_end = next_note["span"]  
    left_syls = get_syls(cur_note["left_context"])
    
    if next_start != cur_end:
        return False  
    if 1 in {len(cur_note_options),len(next_note_options)}:
        if '-' in cur_note_options[0] and '+' in next_note_options[0]:
            word = ""
            tup = get_left_context_valid_word_v1(cur_note,cur_note_options[0],word)
            if tup!=False:
                word,char_walker = tup
                next_pyld_start,next_pyld_end = get_payload_span(next_note)
                left_syls = [token.text for token in get_tokens(cur_note["left_context"])]
                before_default_word = convert_syl_to_word(left_syls[char_walker:])
                new_default_word = before_default_word+cur_note["default_option"]
                normalized_chunk = collated_text[prev_end:cur_start-len(new_default_word)]+":"+collated_text[cur_start-len(new_default_word):cur_start]+collated_text[next_start:next_pyld_start]+word+collated_text[next_pyld_start+1:next_pyld_end]+">"
                prev_end = next_end
                next(notes_iter)
                return normalized_chunk,prev_end
                     
    return False         

def get_valid_word(note,note_option,new_note):
    start,_ = note["span"]
    option_start,option_end = note_option["span"]
    tup_minus = get_left_context_valid_word(note,note_option["note"])
    tup_plus = get_right_context_valid_word(note,note_option["note"])
    if tup_minus == False and tup_plus == False:
        return False
    elif tup_plus == False:
        word,char_walker = tup_minus
        new_note = new_note[:option_start-start]+word+new_note[option_end-start:]
        return new_note,char_walker
    elif tup_minus == False:
        word,char_walker = tup_plus
        new_note = new_note[:option_start-start]+word+new_note[option_end-start:]
        return new_note,char_walker

    return False


def is_word(word):
    tokens = get_tokens(word.replace("།",""))
    if len(tokens) == 1:
        return True
    return False

def get_left_context_valid_word(note,note_option,word=None):
    char_walker=-1
    if word == None:
        word = note_option.replace("+","")
    left_syls = get_syls(note["left_context"])
    if left_syls[-1][-1].strip() in ("།"):
        return False
    while char_walker >= -len(left_syls) and char_walker>=-3:
        word=left_syls[char_walker]+word
        if is_word(word):
            if left_syls[char_walker][-1].strip() in ("།"):
                return word[1:],char_walker
            return word,char_walker
        char_walker-=1
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

def get_token_pos(syl):
    tokens = get_tokens(syl) 
    for token in tokens:
        return token.pos

def get_right_context_valid_word(note,note_option,word=None):
    char_walker=0
    if word == None:
        word = note_option.replace("།","་")
    right_syls = get_syls(note["right_context"])
    while char_walker < len(right_syls) and char_walker<3:
        word = word+right_syls[char_walker]          
        if is_word(word):
            if right_syls[char_walker][-1] == "།":
                return word[:-1],char_walker
            else:
                return word,char_walker
        char_walker+=1
    return False

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
    start,_ = note["span"]
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

def get_tokens(text):
    tokens = wt.tokenize(text, split_affixes=False)
    return tokens

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

def is_mono_syllable(note):
    global normalized_collated_text,prev_end
    note_options = note["alt_options"]
    bool_set = set()
    for note_option in note_options:
        tup = get_left_context_valid_word(note,note_option["note"])
        tup2 = get_right_context_valid_word(note,note_option["note"])
        #tup4 = get_left_context_valid_word_v1(note,note_option["note"])
        #tup3 = get_right_context_valid_word_v1(note,note_option["note"])
        bool_set.add(tup)
        bool_set.add(tup2)
        #bool_set.add(tup3)
        #bool_set.add(tup4)

    if len(bool_set) == 1 and False in bool_set:
        return True 
    
    return False



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


def get_normalized_text(collated_text):
    normalized_collated_text = ""
    prev_end = 0
    notes = get_notes(collated_text)
    notes_iter = iter(enumerate(notes,0))
    
    for note_iter in notes_iter:
        index,cur_note = note_iter
        if index <len(notes)-1:
            next_note = notes[index+1]
            normalized_chunk,cur_end = normalize_note(collated_text,prev_end,cur_note,next_note,notes_iter)     
        else:
            normalized_chunk,cur_end = normalize_note(collated_text,prev_end,cur_note)  
        normalized_collated_text+=normalized_chunk
        prev_end=cur_end

    normalized_collated_text+=collated_text[prev_end:]

    return normalized_collated_text  


if __name__ == "__main__":
    collated_text = Path('./test.txt').read_text(encoding='utf-8')
    normalized_collated_text = get_normalized_text(collated_text)
    Path("./gen_test.txt").write_text(normalized_collated_text)