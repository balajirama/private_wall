from flask import flash
from datetime import datetime
import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9]+\.[a-zA-Z]+$")
NUM_REGEX = re.compile(r"^.*[0-9]+.*")
CAP_REGEX = re.compile(r"^.*[A-Z]+.*")

def is_age_over(num, dob):
    if(type(dob) == type('')):
        if dob != '':
            dob = datetime.strptime(dob, '%Y-%m-%d')
        else:
            return False
    elif type(dob) == type(datetime.now()):
        dob = dob
    else:
        return False
    year = dob.year + num
    nth_bday = datetime.strptime(f"{year}-{dob.month}-{dob.day}", "%Y-%m-%d")
    today = datetime.today()
    return (today - nth_bday).days >= 0

def get_age(dob):
    age = -1
    while(is_age_over(age+1, dob)):
        age += 1
    return age

def validate_password(fields, categories=['password', 'confirm']):
    is_valid = True
    if len(fields[categories[0]]) < 8:
        flash("Password must be at least eight characters", categories[0])
        is_valid = False
    if not(NUM_REGEX.match(fields[categories[0]]) and CAP_REGEX.match(fields[categories[0]])):
        flash("Password must contain at least one capital letter and one digit", categories[0])
        is_valid = False
    if (fields[categories[1]] == "") or (fields[categories[0]] != fields[categories[1]]):
        flash("Passwords do not match", categories[1])
        is_valid = False
    return is_valid
