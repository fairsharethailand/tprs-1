# เพิ่มรายการคำนามพหูพจน์ไม่ปกติไว้ด้านบนของส่วน Grammar Logic
IRR_PL = ["children", "people", "men", "women", "mice", "teeth", "feet", "geese", "oxen"]

def get_auxiliary(subject, pred_target, pred_other):
    # ถ้าเป็น Perfect Tense ไม่ต้องใช้ Do/Does/Did
    if is_present_perfect(pred_target):
        return None 
    
    tense_target = check_tense_type(pred_target)
    tense_other = check_tense_type(pred_other)
    
    # 1. ถ้าตัวใดตัวหนึ่งเป็น Past ให้ใช้ Did
    if tense_target == "past" or tense_other == "past":
        return "Did"
    
    # 2. กรณี Present Tense
    s = subject.lower().strip()
    
    # ตรวจสอบว่าเป็นพหูพจน์หรือไม่ (รวม Irregular Plural ที่คุณแจ้ง)
    is_plural = (
        s in IRR_PL or 
        'and' in s or 
        s in ['i', 'you', 'we', 'they'] or 
        (s.endswith('s') and s not in ['james', 'charles', 'boss'])
    )
    
    if is_plural:
        return "Do"
    return "Does"
