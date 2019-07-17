from flask import Flask, render_template, request, redirect, session, flash, get_flashed_messages
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
from datetime import datetime
import re
import os
import my_utils
app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = 'darksecret'

dbname = 'login_users'
not_logged_in = "You're not logged in"

sql = {'db': connectToMySQL(dbname)}
EDITPASSWORD = sql['db'].query_db("SELECT * FROM editpassword_form ORDER BY itemid;")
REGISTRATION = sql['db'].query_db("SELECT * FROM registration_form ORDER BY itemid;")
EDITPROFILE  = sql['db'].query_db("SELECT * FROM editprofile_form ORDER BY itemid;")
LANGUAGES    = sql['db'].query_db("SELECT * FROM languages ORDER BY itemid;")
del sql['db']

@app.route("/")
def mainpage():
    if 'id' in session:
        return redirect("/success")
    print(get_flashed_messages())
    if 'reg' not in session:
        session['reg'] = {
            'firstname': "",
            'lastname': "",
            'email': ""
        }
    return render_template("index.html", REGISTRATION=REGISTRATION, LANGUAGES=LANGUAGES)

@app.route("/login", methods=["POST"])
def login():
    mysql = connectToMySQL(dbname)
    users = mysql.query_db("SELECT * FROM users WHERE email = %(loginemail)s;", request.form)
    if len(users) > 0:
        if bcrypt.check_password_hash(users[0]['pswdhash'], request.form['loginpassword']):
            session['id'] = users[0]['id']
            session['logged_in'] = True
            session['firstname'] = users[0]['firstname']
            flash("You've been logged in", "success")
            return redirect("/success")
    flash("You could not be logged in", "error")
    return redirect("/")

def get_selected_languages(fields):
    langs = []
    for language in LANGUAGES:
        if language['name'] in fields:
            langs.append(language['name'])
    return langs

def validate_nonpassword(fields):
    is_valid = True
    if not my_utils.EMAIL_REGEX.match(fields['email']):
        flash("Not a valid email", "email")
        is_valid = False
    if len(fields['firstname']) < 2:
        flash("First name must have at least two characters", "firstname")
        is_valid = False
    if len(fields['lastname']) < 2:
        flash("Last name must have at least two characters", "lastname")
        is_valid = False
    if not my_utils.is_age_over(10, fields['dob']):
        is_valid = False
        flash("You're too young to register", "dob")
    if len(get_selected_languages(fields)) < 2:
        flash("Select at least two languages", "languages")
        is_valid = False
    return is_valid

def gen_lang_str():
    langstr = ""
    for language in LANGUAGES:
        if language['name'] in request.form:
            if len(langstr) > 0:
                langstr += " "
            langstr += language['name']
    return langstr

def validate_all_fields(fields):
    return (validate_nonpassword(fields) and my_utils.validate_password(fields))

@app.route("/register", methods=["POST"])
def register():
    print(request.form)
    is_valid = validate_all_fields(request.form)
    if is_valid:
        mysql = connectToMySQL(dbname)
        if len(mysql.query_db("SELECT * FROM users WHERE email = %(email)s", request.form)) == 0:
            dob = datetime.strptime(request.form['dob'], "%Y-%m-%d")
            data = dict()
            for name in request.form.keys():
                data[name] = request.form[name]
            data['pswdhash'] = bcrypt.generate_password_hash(request.form['password'])
            data['dob'] = dob
            data['languages'] = ', '.join(get_selected_languages(request.form))
            if mysql.query_db("INSERT INTO users ( firstname, lastname, email, pswdhash, created_at, updated_at, dob, languages ) VALUES ( %(firstname)s, %(lastname)s, %(email)s, %(pswdhash)s, NOW(), NOW(), %(dob)s, %(languages)s ) ;", data):
                flash("Successfully registered "+request.form['email']+". Try logging in!", "success")
                if 'reg' in session:
                    del session['reg']
            else:
                flash("Something went wrong. It is us, not you! Try in a few hours", "error")
        else:
            flash(request.form['email']+" is already a user. Please login instead.", "error")
    else:
        session['reg'] = {
            'firstname': request.form['firstname'],
            'lastname': request.form['lastname'],
            'email': request.form['email']
        }
    return redirect("/")

@app.route("/success")
def success():
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    mysql = connectToMySQL(dbname)
    rec_msgs = mysql.query_db("SELECT users.firstname AS firstname, users.lastname AS lastname, sender_id, message_id, content, TIMEDIFF(NOW(), sent_at) AS message_age FROM messages JOIN users ON messages.sender_id = users.id WHERE messages.recipient_id = %(id)s AND messages.recipient_del = 0 ORDER BY sent_at DESC;", {'id': session['id']})
    sent_msgs = mysql.query_db("SELECT * FROM messages WHERE sender_id = %(id)s AND sender_del = 0;", {'id': session['id']})
    other_users = mysql.query_db("SELECT * FROM users WHERE id != %(id)s;", {'id': session['id']})
    return render_template("success.html", rec_msgs=rec_msgs, other_users=other_users, sent_msgs=sent_msgs)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/viewprofile")
def viewprofile():
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    mysql = connectToMySQL(dbname)
    users = mysql.query_db("SELECT id, firstname, lastname, email, created_at, dob, languages FROM users WHERE id = %(id)s", {'id': session['id']})
    if len(users) > 0:
        return render_template("profile.html", user=users[0], user_age=my_utils.get_age(users[0]['dob'].strftime('%Y-%m-%d')))
    else:
        flash("Aw snap! Something went wrong. Try again in a few hours", "error")
        return redirect("/success")

@app.route("/viewprofile/<user_id>")
def viewprofile_user_id(user_id):
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    mysql = connectToMySQL(dbname)
    users = mysql.query_db("SELECT id, firstname, lastname, email, created_at, dob, languages FROM users WHERE id = %(id)s", {'id': user_id})
    if len(users) > 0:
        return render_template("profile.html", user=users[0], user_age=my_utils.get_age(users[0]['dob'].strftime('%Y-%m-%d')))
    else:
        flash("Aw snap! Something went wrong. Try again in a few hours", "error")
        return redirect("/success")


@app.route("/editprofile")
def editprofile():
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    mysql = connectToMySQL(dbname)
    users = mysql.query_db("SELECT id, firstname, lastname, email, created_at, languages, dob FROM users WHERE id = %(id)s", {'id': session['id']})
    userdata = dict()
    for key in users[0].keys():
        userdata[key] = users[0][key]
    userdata['dob'] = userdata['dob'].strftime("%Y-%m-%d")
    print(userdata)
    checkedlanguages = userdata['languages'].split(', ')
    if len(users) > 0:
        return render_template("editprofile.html", user = userdata, EDITPROFILE=EDITPROFILE, LANGUAGES=LANGUAGES, checkedlanguages=checkedlanguages)
    else:
        flash("Aw snap! Something went wrong. Try again in a few hours", "error")
        return redirect("/success")

@app.route("/updateprofile", methods=['POST'])
def updateprofile():
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    if validate_nonpassword(request.form):
        mysql = connectToMySQL(dbname)
        data = dict()
        for key in request.form.keys():
            data[key] = request.form[key]
        data['dob'] = datetime.strptime(request.form['dob'], '%Y-%m-%d')
        data['languages'] = ', '.join(get_selected_languages(request.form))
        data['id'] = session['id']
        if mysql.query_db("UPDATE users SET firstname = %(firstname)s, lastname = %(lastname)s, email = %(email)s, dob = %(dob)s, languages = %(languages)s, updated_at = NOW() WHERE id = %(id)s;", data):
            flash("Updated your profile", "success")
        else:
            flash("Something went wrong. It's us, not you. Try again later.", "error")
        return redirect("/success")
    else:
        return redirect("/editprofile")

@app.route("/changepasswd")
def changepasswd():
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    return render_template("change_password.html", EDITPASSWORD=EDITPASSWORD)

@app.route("/updatepassword", methods=['POST'])
def updatepassword():
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    mysql = connectToMySQL(dbname)
    rows = mysql.query_db("SELECT id, pswdhash FROM users WHERE id = %(id)s", {'id': session['id']})
    is_valid = True
    if len(rows) == 0:
        is_valid = False
        flash("Passwords cannot be updated now. Please try again later", "error")
        return redirect("/success")
    if not bcrypt.check_password_hash(rows[0]['pswdhash'], request.form['currentpassword']):
        is_valid = False
        flash('Current password does not match', 'currentpassword')
        return redirect("/changepasswd")
    if not my_utils.validate_password(request.form, categories=['newpassword', 'confirm']):
        is_valid = False
    if not is_valid:
        return redirect("/changepasswd")
    else:
        pswdhash = bcrypt.generate_password_hash(request.form['newpassword'])
        status = mysql.query_db("UPDATE users SET pswdhash = %(pswdhash)s WHERE id = %(id)s", {'id': rows[0]['id'], 'pswdhash': pswdhash})
        if status:
            flash('Password changed', 'success')
        else:
            flash("Something went wrong in saving your new password. Password did not change.", "error")
        return redirect("/success")

@app.route("/deleteprofile")
def deleteprofile():
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    mysql = connectToMySQL(dbname)
    mysql.query_db("DELETE FROM users WHERE id = %(id)s", {'id': session['id']})
    return redirect("/logout")

@app.route("/delmsg/<id>")
def delmsg(id):
    if 'id' not in session:
        flash(not_logged_in, 'error')
        return redirect("/")
    mysql = connectToMySQL(dbname)
    data = {'message_id': id, 'recipient_id': session['id']}
    messages = mysql.query_db("SELECT * FROM messages WHERE message_id = %(message_id)s AND recipient_id = %(recipient_id)s;", data)
    if bool(messages) == 0:
        if 'mischief' not in session:
            session['mischief'] = datetime.now()
            flash("You can't delete that message", "error")
            return redirect("/hacker_alert")
        else:
            return redirect("/logout")
    elif not mysql.query_db("UPDATE messages SET recipient_del = 1 WHERE message_id = %(message_id)s AND recipient_id = %(recipient_id)s;", data):
        flash("Something went wrong in deleting the message. Server error.", "error")
    return redirect("/success")

@app.route("/hacker_alert")
def hacker_alert():
    if 'id' not in session:
        flash(not_logged_in, 'error')
        return redirect("/")
    mysql = connectToMySQL(dbname)
    users = mysql.query_db("SELECT * FROM users WHERE id = %(id)s", {'id': session['id']})
    return render_template("mischief.html", user=users[0], ip_address=request.remote_addr)

@app.route("/sendmsg", methods=['POST'])
def sendmsg():
    if 'id' not in session:
        flash(not_logged_in, "error")
        return redirect("/")
    mysql = connectToMySQL(dbname)
    data = dict()
    for key in request.form.keys():
        data[key] = request.form[key]
    data['sender_id'] = session['id']
    if not mysql.query_db("INSERT INTO messages (content, recipient_id, sender_id, sent_at, recipient_del, sender_del) VALUES ( %(content)s, %(recipient_id)s, %(sender_id)s, NOW(), 0, 0 );", data):
        flash("Aw snap! Something is wrong at our end. Try in a few hours. Message was not sent", "error")
    else:
        users = mysql.query_db("SELECT firstname FROM users WHERE id = %(recipient_id)s", request.form)
        if len(users) < 0:
            flash("There was an error when you tried to send a message", "error")
        else:
            flash("Message sent to "+users[0]['firstname']+' successfully.', 'success')
    return redirect("/success")

if __name__ == "__main__":
    app.run(debug=True)