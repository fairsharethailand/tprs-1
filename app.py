import streamlit as st
from gtts import gTTS
import base64
import os
import uuid
import random

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="TPRS Magic Wheel V58.3 (Updated Logic)", layout="wide")

# 2. Session State
if 'display_text' not in st.session_state:
    st.session_state.display_text = ""
if 'audio_key' not in st.session_state:
    st.session_state.audio_key = 0

# --- Grammar Data ---
PAST_TO_INF = {
    "went": "go", "ate": "eat", "saw": "see", "bought": "buy", 
    "had": "have", "did": "do", "drank": "drink", "slept": "sleep", 
    "wrote": "write", "came": "come", "ran": "run", "met": "meet",
    "spoke": "speak", "took": "take", "found": "find", "gave": "give",
    "thought": "think", "brought": "bring", "told": "tell", "made": "make",
    "cut": "cut", "put": "put", "hit": "hit", "read": "read", "cost": "cost"
}

IRREGULAR_PLURALS = [
    "children", "people", "men", "women", "mice", "teeth", "feet", "geese", "oxen", "data"
]

# --- Helper Functions ---
def is_present_perfect(predicate):
    words = predicate.lower().split()
    if len(words) >= 2 and words[0] in ['have', 'has', 'had']:
        v2 = words[1]
        if v2.endswith('ed') or v2 in PAST_TO_INF or v2 in ['been', 'done', 'gone', 'seen', 'eaten']:
            return True
    return False

def check_tense_type(predicate):
    words = predicate.split()
    if not words: return "unknown"
    v = words[0].lower().strip()
    if v.endswith("ed") or v in PAST_TO_INF:
        return "past"
    if v.endswith("s") or v.endswith("es") or v in ["go", "eat", "see", "buy", "do", "drink", "sleep", "write", "come", "run", "meet", "speak", "take", "find", "give", "think", "bring", "tell", "make"]:
        return "present"
    return "unknown"

def conjugate_to_singular(predicate):
    """เปลี่ยน Verb ให้เป็นรูปเอกพจน์ (เติม s/es) สำหรับคำถาม Who"""
    words = predicate.split()
    if not words: return ""
    v = words[0].lower()
    rest = " ".join(words[1:])
    
    # ถ้าลงท้ายด้วย s/es อยู่แล้ว หรือเป็น Past ไม่ต้องแก้
    if v.endswith('s') or check_tense_type(v) == "past":
        return predicate

    # กฎการเติม s/es เบื้องต้น
    if v.endswith(('ch', 'sh', 'x', 's', 'z', 'o')):
        v = v + "es"
    elif v.endswith('y') and v[-2] not in 'aeiou':
        v = v[:-1] + "ies"
    else:
        v = v + "s"
    
    return f"{v} {rest}".strip()

def get_auxiliary(subject, pred_target, pred_other):
    if is_present_perfect(pred_target):
        return None 
    
    tense_target = check_tense_type(pred_target)
    tense_other = check_tense_type(pred_other)
    
    if tense_target == "past" or tense_other == "past":
        return "Did"
    
    # Logic สำหรับ Present Tense (Do/Does)
    s = subject.lower().strip()
    # เช็ค Irregular Plural หรือสรรพนามพหูพจน์
    if s in IRREGULAR_PLURALS or 'and' in s or s in ['i', 'you', 'we', 'they'] or (s.endswith('s') and s not in ['james', 'charles', 'boss']):
        return "Do"
    return "Does"

def to_infinitive(predicate, other_predicate):
    words = predicate.split()
    if not words: return ""
    v = words[0].lower().strip()
    rest = " ".join(words[1:])
    is_past = (check_tense_type(predicate) == "past" or check_tense_type(other_predicate) == "past")
    
    if is_past or v in ['had', 'has', 'have']:
        if v in ['had', 'has', 'have']: inf_v = "have"
        elif v in PAST_TO_INF: inf_v = PAST_TO_INF[v]
        elif v.endswith("ed"):
            if v.endswith("ied"): inf_v = v[:-3] + "y"
            else: inf_v = v[:-2]
        else: inf_v = v
    else:
        if v.endswith("es"):
            for suffix in ['sses', 'ches', 'shes', 'xes']:
                if v.endswith(suffix): 
                    inf_v = v[:-2]
                    break
            else: inf_v = v[:-2]
        elif v.endswith("s") and not v.endswith("ss"): inf_v = v[:-1]
        else: inf_v = v
    return f"{inf_v} {rest}".strip()

def has_be_verb(predicate):
    v_low = predicate.lower().split()
    be_and_modals = ['is', 'am', 'are', 'was', 'were', 'can', 'will', 'must', 'should', 'could', 'would']
    return v_low and v_low[0] in be_and_modals

# --- Core Logic ---
def build_logic(q_type, data):
    s1, p1, s2, p2 = data['s1'], data['p1'], data['s2'], data['p2']
    main_sent = data['main_sent']
    subj_real, pred_real = (s1 if s1 else "He"), (p1 if p1 else "is here")
    subj_trick = s2 if s2 != "-" else s1
    pred_trick = p2 if p2 != "-" else p1

    def swap_front(s, p):
        parts = p.split()
        return f"{parts[0].capitalize()} {s} {' '.join(parts[1:])}".strip().replace("  ", " ")

    if q_type == "Statement": return main_sent
    
    if q_type == "Negative":
        if has_be_verb(pred_trick) or is_present_perfect(pred_trick):
            parts = pred_trick.split()
            return f"No, {subj_trick} {parts[0]} not {' '.join(parts[1:])}."
        aux = get_auxiliary(subj_trick, pred_trick, pred_real)
        return f"No, {subj_trick} {aux.lower()} not {to_infinitive(pred_trick, pred_real)}."

    if q_type == "Yes-Q":
        if has_be_verb(pred_real) or is_present_perfect(pred_real): return swap_front(subj_real, pred_real) + "?"
        aux = get_auxiliary(subj_real, pred_real, pred_trick)
        return f"{aux} {subj_real} {to_infinitive(pred_real, pred_trick)}?"

    if q_type == "No-Q":
        if has_be_verb(pred_trick) or is_present_perfect(pred_trick): return swap_front(subj_trick, pred_trick) + "?"
        aux = get_auxiliary(subj_trick, pred_trick, pred_real)
        return f"{aux} {subj_trick} {to_infinitive(pred_trick, pred_real)}?"

    if q_type == "Either/Or":
        if s2 != "-" and s1.lower().strip() != s2.lower().strip():
            if has_be_verb(pred_real) or is_present_perfect(pred_real):
                v_f = pred_real.split()[0].capitalize(); v_r = " ".join(pred_real.split()[1:])
                return f"{v_f} {subj_real} or {subj_trick} {v_r}?"
            aux = get_auxiliary(subj_real, pred_real, pred_trick)
            return f"{aux} {subj_real} or {subj_trick} {to_infinitive(pred_real, pred_trick)}?"
        else:
            p_alt = p2 if p2 != "-" else "something else"
            if has_be_verb(pred_real) or is_present_perfect(pred_real): return f"{swap_front(subj_real, pred_real)} or {p_alt}?"
            aux = get_auxiliary(subj_real, pred_real, p
