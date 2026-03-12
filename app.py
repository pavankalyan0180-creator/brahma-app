from flask import *
import sqlite3

app=Flask(__name__)

app.secret_key='your_secret_key'

def create_db():
    conn=sqlite3.connect("database.db")
    cursor=conn.cursor()
    conn.execute ('''
        create table if not exists users (
                  id integer primary key autoincrement,
                  firstname text not null,
                  lastname text not null,
                  username text not null unique,
                  email text not null unique,
                  phone_number integer not null unique,
                  password varchar(100) not null,
                  confirm_password varchar(100) not null
                  )
                  ''')
    conn.commit()
    conn.close()

create_db()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register',methods=["GET","POST"])

def register():
    if request.method=="POST":
        first_name=request.form["firstname"]
        last_name=request.form["lastname"]
        username=request.form["username"]
        email=request.form["email"]
        phone_number=request.form.get("phone_number")
        password=request.form["password"]   
        confirm_password=request.form.get("confirm_password")
        
        if password != confirm_password:
            return render_template('registration.html', error="Passwords do not match")
        conn=sqlite3.connect("database.db")
        cursor=conn.cursor()
        cursor.execute('''
            insert into users (
            firstname,lastname,username,email,phone_number,password,confirm_password
            ) values (?,?,?,?,?,?,?)
            ''',(first_name, last_name, username, email, phone_number, password, confirm_password))
        conn.commit()
        conn.close()
        return redirect('/login')
        
    return render_template('registration.html')

@app.route('/login',methods=["GET","POST"])
def login():
    if request.method =='POST':
        username=request.form["username"]
        password=request.form["password"]

        conn=sqlite3.connect("database.db")
        cursor=conn.cursor()
        cursor.execute(
        "select * from users where username=? and password=?", 
        (username, password)
        )
        user=cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[3]
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid username or password")
        
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/patients')
def patients():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('patients.html')

@app.route('/medication')
def medication():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('medication.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)