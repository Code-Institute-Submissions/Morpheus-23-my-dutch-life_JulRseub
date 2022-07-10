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
@app.route("/welcome")
def welcome():
# the landing page providing info about site
    return render_template("welcome.html")

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
        flash("Your registration is successful, welcome!")
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
                return redirect(url_for(
                    "profile", username=session["username"]))
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
    # get the logged in user's profile from database
    member = mongo.db.members.find_one({"username": username})

    if request.method == "POST":
        # check if member exists in database

        updated_member = {
            "username": request.form.get("username").lower(),
            "firstname": request.form.get("firstname"),
            "surname": request.form.get("surname"),
            "postal_code": request.form.get("postal_code").upper(),
            "ruleschecked": request.form.get("ruleschecked"),
            "password": generate_password_hash(request.form.get("password"))
        }

        mongo.db.members.replace_one(member, updated_member, True)

        return redirect(url_for("get_offers"))

    return render_template("profile.html", member=member)



@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out.....goodbye")
    session.pop("username")
    return redirect(url_for("login"))

@app.route("/add_offer", methods=["GET", "POST"])
def add_offer():
    if request.method == "POST":

        offer = populate_offer(request.form)

        mongo.db.offers.insert_one(offer)
        flash("Thank you, your offer has been successfully added")
        return redirect(url_for("get_offers"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_offer.html", categories=categories)


@app.route("/edit_offer/<offer_id>", methods=["GET", "POST"])
def edit_offer(offer_id):

    categories = mongo.db.categories.find().sort("category_name", 1)

    if request.method == "POST":

        updated_offer = populate_offer(request.form)

        # https://stackoverflow.com/questions/69950552/mongodb-update-i-cant-update-my-documents-in-mongodb-with-flask-api
        offer = {"_id": ObjectId(offer_id)}
        mongo.db.offers.replace_one(offer, updated_offer, True)

        flash("Great, your offer has been successfully updated")
        offers = list(mongo.db.offers.find())
        return render_template("offers.html", offers=offers, categories=categories)

    offer = mongo.db.offers.find_one({"_id": ObjectId(offer_id)})
    return render_template("edit_offer.html", offer=offer, categories=categories)


@app.route("/delete_offer/<offer_id>")
def delete_offer(offer_id):
    # https://www.youtube.com/watch?v=dQ2niRl2Lek

    try:
        mongo.db.offers.delete_one({"_id": ObjectId(offer_id)})
        flash("Offer successfully deleted")
    except Exception:
        flash("Could not delete offer")

    return redirect(url_for("get_offers"))

@app.route("/get_offers")
def get_offers():
    # https://stackoverflow.com/questions/11774265/how-do-you-access-the-query-string-in-flask-routes

    selected_categories = request.args.getlist('selected_categories')
    my_offers = "checked" if request.args.get("my_offers") else ""
 
    filters = {
        "selected_categories": selected_categories,
        "my_offers": my_offers
    }

    # populate dropdown
    categories = list(mongo.db.categories.find())
    # TODO: figure out how to mark the categories as selected after filtering

    filter_criteria = ""

    # https://www.freecodecamp.org/news/python-list-length-how-to-get-the-size-of-a-list-in-python/
    # https://stackoverflow.com/questions/23577172/mongodb-pymongo-querying-multiple-criteria-unexpected-results
    if len(selected_categories) > 0 and my_offers == "":
        filter_criteria = { "category_name": { "$in": selected_categories} }
    elif len(selected_categories) == 0 and my_offers == "checked":
        filter_criteria = { "offered_by": { "$eq": session["username"]} }
    elif len(selected_categories) > 0 and my_offers == "checked":
        filter_criteria = { "$and": [{ "category_name": { "$in": selected_categories} }, { "offered_by": { "$eq": session["username"]} }] }
    
    offers = list(mongo.db.offers.find(filter_criteria))

    return render_template("offers.html", offers=offers, categories=categories, filters=filters)


@app.route("/contact_admin")
def contact_admin():
     # the last page, being contact admin
    return render_template("contact_admin.html")

def populate_offer(request_form):
    is_hot_product = "on" if request_form.get(
        "is_hot_product") else "off"
    is_frozen_product = "on" if request_form.get(
        "is_frozen_product") else "off"

    new_offer = {
        "category_name": request_form.get("category_name"),
        "name": request_form.get("offer_name"),
        "description": request_form.get("offer_description"),
        "offered_by": session["username"],
        "collection_start_date": request_form.get("offer_collection_date"),
        "collection_start_time": request_form.get("offer_collection_start_time"),
        "collection_end_time": request_form.get("offer_collection_expiry_time"),
        "collection_point": request_form.get("offer_collection_point"),
        "is_hot_product": is_hot_product,
        "is_frozen_product": is_frozen_product
    }

    return new_offer


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)