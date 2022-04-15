import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

@app.route("/")
@app.route("/get_offers")
def get_offers():
    offers = mongo.db.offers.find()
    return render_template("offers.html", offers=offers)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if member exists in database
        existing_member = mongo.db.members.find_one(
            {"username": request.form.get("username").lower()})

        if existing_member:
            flash("Member name already exists")
            return redirect(url_for("register"))

        member = {
            "username": request.form.get("username").lower(),
            "firstname": request.form.get("firstname"),
            "surname": request.form.get("surname"),
            "postal_code": request.form.get("postal_code").upper(),
            "ruleschecked": request.form.get("ruleschecked"),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.members.insert_one(member)

        # add new member to 'session' cookie
        session["username"] = request.form.get("username").lower()
        flash("Registration Successful!")

    return render_template("register.html")

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)