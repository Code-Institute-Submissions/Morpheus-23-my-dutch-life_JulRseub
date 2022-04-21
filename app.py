import os
import logging
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
    offers = list(mongo.db.offers.find())
    # maybe format the date

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
        flash("Your registration is successful, welcome to the Sharing-is-Caring community!")
        return redirect(url_for("profile", username=session["username"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_member = mongo.db.members.find_one(
            {"username": request.form.get("username").lower()})

        if existing_member:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_member["password"], request.form.get("password")):
                    session["username"] = request.form.get("username").lower()
                    flash("Welcome {}".format(request.form.get("username")))
                    return redirect(url_for("profile", username=session["username"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # get the logged in user's username from database
    username = mongo.db.members.find_one(
        {"username": session["username"]})["username"]

    if session["username"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out.....goodbye")
    session.pop("username")
    return redirect(url_for("login"))


@app.route("/add_offer", methods=["GET", "POST"])
def add_offer():
    if request.method == "POST":
        is_hot_product = "on" if request.form.get(
            "is_hot_product") else "off"
        is_frozen_product = "on" if request.form.get(
            "is_frozen_product") else "off"

        collection_date_start = request.form.get("offer_collection_date")
        collection_time_start = request.form.get("offer_collection_start_time")
        collection_time_end = request.form.get("offer_collection_expiry_time")

        collection_start = collection_date_start + " " + collection_time_start
        collection_end = collection_date_start + " " + collection_time_end

        offer = {
            "category_name": request.form.get("category_name"),
            "name": request.form.get("offer_name"),
            "description": request.form.get("offer_description"),
            "collection_date_start": collection_start,
            "collection_date_end": collection_end,
            "collection_point": request.form.get("offer_collection_point"),
            "is_hot_product": is_hot_product,
            "is_frozen_product": is_frozen_product,
        }
        mongo.db.offers.insert_one(offer)
        flash("Thank you, your offer has been successfully added")
        return redirect(url_for("get_offers"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_offer.html", categories=categories)


@app.route("/edit_offer/<offer_id>", methods=["GET", "POST"])
def edit_offer(offer_id):

    if request.method == "POST":
        is_hot_product = "on" if request.form.get(
            "is_hot_product") else "off"
        is_frozen_product = "on" if request.form.get(
            "is_frozen_product") else "off"

        collection_date_start = request.form.get("offer_collection_date")
        collection_time_start = request.form.get("offer_collection_start_time")
        collection_time_end = request.form.get("offer_collection_expiry_time")

        collection_start = collection_date_start + " " + collection_time_start
        collection_end = collection_date_start + " " + collection_time_end

        updated_offer = {
            "category_name": request.form.get("category_name"),
            "name": request.form.get("offer_name"),
            "description": request.form.get("offer_description"),
            "collection_date_start": collection_start,
            "collection_date_end": collection_end,
            "collection_point": request.form.get("offer_collection_point"),
            "is_hot_product": is_hot_product,
            "is_frozen_product": is_frozen_product,
            "member_username": session["username"]
        }
        # todo fix update - 
        # mongo.db.offers.update_one({"_id": ObjectId(offer_id)}, updated_offer)
        # flash("Task Successfully Updated")
        return redirect(url_for("get_offers")) 

    offer = mongo.db.offers.find_one({"_id": ObjectId(offer_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_offer.html", offer=offer, categories=categories)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)