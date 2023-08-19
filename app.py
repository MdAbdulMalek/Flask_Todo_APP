from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Todo_DB.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.app_context().push()

class Todo_DB(db.Model):
    sn = db.Column(db.Integer, primary_key = True)
    tittle = db.Column(db.String(100), nullable = False)
    desc = db.Column(db.String(300), nullable = False)
    date_created = db.Column(db.DateTime, default = datetime.now())

    def __repr__(self) -> str:
        return f"{self.sn} -> {self.tittle} -> {self.date_created}"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        tittle = request.form['tittle']
        desc = request.form['desc']

        add_db = Todo_DB(tittle=tittle, desc=desc)
        db.session.add(add_db)
        db.session.commit()
    all_list = Todo_DB.query.all()
    return render_template("index.html", all_list=all_list)


@app.route('/delete/<int:sn>')
def delete(sn):
    db.session.query(Todo_DB).filter(Todo_DB.sn==sn).delete()
    db.session.commit()
    return redirect("/")

@app.route('/update/<int:sn>', methods=['GET', 'POST'])
def update(sn):
    if request.method == 'POST':
        tittle = request.form['tittle']
        desc = request.form['desc']
        add_db = Todo_DB.query.filter_by(sn=sn).first()
        add_db.tittle = tittle
        add_db.desc = desc
        add_db.date_created = datetime.now()
        db.session.add(add_db)
        db.session.commit()
        return redirect("/")
    
    context = Todo_DB.query.filter_by(sn=sn).first()
    return  render_template("update.html", context=context)


@app.route('/details/<int:sn>')
def details(sn):
    context = Todo_DB.query.filter_by(sn=sn).first()
    return  render_template("details.html", context=context)

if __name__ == "__main__":
    app.run(debug=True)