from tkinter import Pack
from flask import Flask, render_template, flash, redirect, request, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
import random
from functools import wraps
from flask_mail import Mail, Message


app = Flask(__name__)
app.secret_key='some secret key'


#Config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='balaaditya'
app.config['MYSQL_DB']='bloodbank'
app.config['MYSQL_CURSORCLASS']='DictCursor'
#init MySQL
#mail= Mail(app)

#app.config['MAIL_SERVER']='smtp.gmail.com'
#app.config['MAIL_PORT'] = 465
#app.config['MAIL_USERNAME'] = 'xyz@gmail.com'
#app.config['MAIL_PASSWORD'] = '*******'
#app.config['MAIL_USE_TLS'] = False
#app.config['MAIL_USE_SSL'] = True
#mail = Mail(app)
mysql =  MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        bgroup = request.form["bgroup"]
        bpackets = request.form["bpackets"]
        fname = request.form["fname"]
        adress = request.form["adress"]

        #create a cursor
        cur = mysql.connection.cursor()

        #Inserting values into tables
        cur.execute("INSERT INTO CONTACT(B_GROUP,C_PACKETS,F_NAME,ADRESS) VALUES(%s, %s, %s, %s)",(bgroup, bpackets, fname, adress))
        cur.execute("INSERT INTO NOTIFICATIONS(NB_GROUP,N_PACKETS,NF_NAMbloodbankbloodbankbloodbankbloodbankE,NADRESS) VALUES(%s, %s, %s, %s)",(bgroup, bpackets, fname, adress))
        #Commit to DB
        mysql.connection.commit()
        #close connection
        cur.close()
        flash('Your request is successfully sent to the Blood Bank','success')
        return redirect(url_for('index'))

    return render_template('contact.html')


class RegisterForm(Form):
    name = StringField('Name', [validators.DataRequired(),validators.Length(min=1,max=25)])
    email = StringField('Email',[validators.DataRequired(),validators.Length(min=10,max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method  == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        e_id = name+str(random.randint(1111,9999))
        #Create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO RECEPTION(E_ID,NAME,EMAIL,PASSWORD) VALUES(%s, %s, %s, %s)",(e_id, name, email, password))
        #Commit to DB
        mysql.connection.commit()
        #close connection
        cur.close()
        flashing_message = "Success! You can log in with Employee ID " + str(e_id)
        flash( flashing_message,"success")

        return redirect(url_for('login'))

    return render_template('register.html',form = form)

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        e_id = request.form["e_id"]
        password_candidate = request.form["password"]

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM RECEPTION WHERE E_ID = %s", [e_id])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['PASSWORD']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['e_id'] = e_id
                session['admin'] = False

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Employee ID not found'
            return render_template('login.html', error=error)

    return render_template('login.html')
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # Get Form Fields
        e_id = request.form["e_id"]
        password_candidate = request.form["password"]

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM ADMIN WHERE E_ID = %s", [e_id])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['PASSWORD']

            # Compare Passwords
            if (password_candidate==password):
                # Passed
                session['logged_in'] = True
                session['e_id'] = e_id
                session['admin'] = True
                flash('You are now logged in', 'success')
                return redirect(url_for('register'))
            else:
                error = 'Invalid login'
                return render_template('admin.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Employee ID not found'
            return render_template('admin.html', error=error)

    return render_template('admin.html')
# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login!', 'danger')
            return redirect(url_for('login'))
    return wrap

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    #result = cur.callproc('BLOOD_DATA')
    #details = cur.fetchall()
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT B_GROUP,TOTAL_PACKETS FROM BLOODBANK GROUP BY B_GROUP")
    details = cur.fetchall()

    if result>0:
        return render_template('dashboard.html',details=details)
    else:
        msg = ' Blood Bank is Empty '
        return render_template('dashboard.html',msg=msg)
    #close connection
    cur.close()

@app.route('/donate', methods=['GET', 'POST'])
@is_logged_in
def donate():
    if request.method  == 'POST':
        # Get Form Fields
        dname = request.form["dname"]
        sex = request.form["sex"]
        age = request.form["age"]
        weight = request.form["weight"]
        address = request.form["address"]
        disease =  request.form["disease"]
        demail = request.form["demail"]

        #create a cursor
        cur = mysql.connection.cursor()

        #Inserting values into tables
        cur.execute("INSERT INTO DONOR(DNAME,SEX,AGE,WEIGHT,ADDRESS,DISEASE,DEMAIL) VALUES(%s, %s, %s, %s, %s, %s, %s)",(dname , sex, age, weight, address, disease, demail))
        #Commit to DB
        mysql.connection.commit()
        #close connection
        cur.close()
        flash('Success! Donor details Added.','success')
        return redirect(url_for('donorlogs'))

    return render_template('donate.html')

@app.route('/donorlogs')
@is_logged_in
def donorlogs():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM DONOR")
    logs = cur.fetchall()

    if result>0:
        return render_template('donorlogs.html',logs=logs)
    else:
        msg = ' No logs found '
        return render_template('donorlogs.html',msg=msg)
    #close connection
    cur.close()


@app.route('/bloodform',methods=['GET','POST'])
@is_logged_in
def bloodform():
    if request.method  == 'POST':
        # Get Form Fields
        d_id = request.form["d_id"]
        blood_group = request.form["blood_group"]
        packets = request.form["packets"]

        #create a cursor
        cur = mysql.connection.cursor()

        #Inserting values into tables
        cur.execute("INSERT INTO BLOOD(D_ID,B_GROUP,PACKETS) VALUES(%s, %s, %s)",(d_id , blood_group, packets))
        cur.execute("SELECT * FROM BLOODBANK")
        records = cur.fetchall()
        cur.execute("UPDATE BLOODBANK SET TOTAL_PACKETS = TOTAL_PACKETS+%s WHERE B_GROUP = %s",(packets,blood_group))
        #Commit to DB
        mysql.connection.commit()
        #close connection
        cur.close()
        flash('Success! Donor Blood details Added.','success')
        return redirect(url_for('dashboard'))

    return render_template('bloodform.html')


@app.route('/notifications',methods=['GET','POST'])
@is_logged_in
def notifications():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM CONTACT")
    requests = cur.fetchall()

    if result>0:
        return render_template('notification.html',requests=requests)
    else:
        msg = ' No requests found '
        return render_template('notification.html',msg=msg)

    #close connection
    cur.close()

@app.route('/notifications/accept')
@is_logged_in
def accept():
    c_id=request.args.get('id')
    pack=request.args.get('pack')
    bgp=request.args.get('bgp')
    pos="+"
    new=bgp+pos
    new.replace(" ","")
    cur = mysql.connection.cursor()
    res=cur.execute("SELECT B_GROUP FROM CONTACT WHERE CONTACT_ID= %s",[c_id])
    requests = cur.fetchall()
    print(requests)
    print(type(requests))
    print(requests[0])
    newval=requests[0]
    print(type(newval))
    req=newval['B_GROUP']
    print(req)
    res2=cur.execute("SELECT TOTAL_PACKETS FROM BLOODBANK WHERE B_GROUP= %s",[req])
    reqe=cur.fetchall()
    print("Hrllo")
    print(res2)
    print(type(req))
    fres=cur.execute("SELECT BLOOD.D_ID,DONOR.DNAME,BLOOD.B_GROUP,DONOR.SEX,DONOR.ADDRESS,DONOR.DEMAIL FROM BLOOD , DONOR WHERE BLOOD.B_GROUP= %s AND BLOOD.D_ID=DONOR.D_ID",[req])
    ddatas=cur.fetchall()
    newval1=reqe[0]
    print(type(newval1))
    req2=newval1['TOTAL_PACKETS']
    print(req2)
    print(type(req2))
    newp=int(pack)
    print(newp)
    print(type(newp))

    isPack = req2-newp
    if(isPack>=0):
        cur.execute("UPDATE BLOODBANK SET TOTAL_PACKETS = TOTAL_PACKETS-%s WHERE B_GROUP = %s",(pack,req))
        cur.execute("DELETE FROM CONTACT WHERE CONTACT_ID = %s",[c_id])
        mysql.connection.commit()
        #msg = Message('Hello', sender = 'xyz@gmail.com', recipients = ['abcd8@gmail.com'])
        #msg.body = "Hello Flask message sent from Flask-Mail"
        #mail.send(msg)
        #return "Sent"
    else:
        print(req)
        
        print(fres)

        print(ddatas)
        return render_template('calldonor.html',ddatas=ddatas)
    #close connection
    cur.close()
    flash('Request Accepted','success')
    return redirect(url_for('notifications'))

@app.route('/notifications/decline')
@is_logged_in
def decline():
    c_id=request.args.get('id')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM CONTACT WHERE CONTACT_ID = %s",[c_id])
    mysql.connection.commit()
    #close connection
    cur.close()
    msg = 'Request Declined'
    flash(msg,'danger')
    return redirect(url_for('notifications'))


@app.route('/blooddata')
def blooddata():
    cur = mysql.connection.cursor()
    #result = cur.callproc('BLOOD_DATA')
    #details = cur.fetchall()
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT B_GROUP,TOTAL_PACKETS FROM BLOODBANK GROUP BY B_GROUP")
    details = cur.fetchall()

    if result>0:
        return render_template('blooddata.html',details=details)
    else:
        msg = ' Blood Bank is Empty '
        return render_template('blooddata.html',msg=msg)
    #close connection
    cur.close()

if __name__ == '__main__':
    app.run(debug=True)
