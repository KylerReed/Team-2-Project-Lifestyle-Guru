from flask import Flask, redirect, render_template, request, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("age"))

    return render_template("login.html")


@app.route("/age", methods=["GET", "POST"])
def age():
    if request.method == "POST":
        session['age'] = request.form.get("selected_age")
        print(f"User selected age: {session['age']}")
        return redirect(url_for("weight"))

    return render_template("age.html")


@app.route("/weight", methods=["GET", "POST"])
def weight():
    if request.method == "POST":
        session['weight'] = request.form.get("selected_weight")
        
        print(f"User selected weight: {session['weight']}")
        return redirect(url_for("gender"))

    return render_template("weight.html")


@app.route("/gender", methods=["GET", "POST"])
def gender():
    if request.method == "POST":
        session['gender'] = request.form.get("gender")
        print(f"User selected gender: {session['gender']}")
        return redirect(url_for("height"))

    return render_template("gender.html")


@app.route("/height", methods=["GET", "POST"])
def height():
    if request.method == "POST":
        session['height'] = request.form.get("height_value")
        # Save whether they chose cm or inches (e.g., passing 'cm' or 'in' from your height template form)
        session['height_unit'] = request.form.get("height_unit", "cm") 
        print(f"User selected height: {session['height']} ({session['height_unit']})")
        return redirect(url_for("activity"))

    return render_template("height.html")


@app.route("/activity", methods=["GET", "POST"])
def activity():
    if request.method == "POST":
        session['activity_level'] = request.form.get("activity")
        print(f"User selected activity: {session['activity_level']}")
        return redirect(url_for("goal"))

    return render_template("activity.html")


@app.route("/goal", methods=["GET", "POST"])
def goal():
    if request.method == "POST":
        session['goal'] = request.form.get("goal")
        print(f"User selected goal: {session['goal']}")
        return redirect(url_for("dashboard"))

    return render_template("goal.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    selected_date = request.args.get("date", "09-12")
    return render_template("dashboard.html", selected_date=selected_date)
    
@app.route("/log_meal", methods=["GET", "POST"])
def log_meal():
    return render_template("log_meal.html")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        session['gender'] = request.form.get("gender")
        session['age'] = request.form.get("age")
        session['weight'] = request.form.get("weight")
        session['height'] = request.form.get("height")
        session['activity_level'] = request.form.get("activity_level")
        session['goal'] = request.form.get("goal")
        
        print(f"Profile Updated -> Gender: {session['gender']}, Age: {session['age']}, Weight: {session['weight']}, Height: {session['height']}, Activity: {session['activity_level']}, Goal: {session['goal']}")
        return redirect(url_for("dashboard"))
        
    
    return render_template(
        "profile.html",
        user_gender=session.get('gender', 'Female'),
        user_age=int(session.get('age', 19)),
        user_weight=session.get('weight', '62 kg'),
        user_height=session.get('height', '168 cm'),
        user_height_unit=session.get('height_unit', 'cm'),
        user_activity=session.get('activity_level', 'Moderately Active'),
        user_goal=session.get('goal', 'Gain weight')
    )

@app.route("/add_food", methods=["GET", "POST"])
def add_food():
    if request.method == "POST":
        name = request.form.get("meal_name")
        m_type = request.form.get("meal_type")
        protein = request.form.get("protein")
        fats = request.form.get("fats")
        calories = request.form.get("calories")
        print(f"New Meal Added -> Name: {name}, Type: {m_type}, Protein: {protein}, Fats: {fats}, Kcal: {calories}")
        return redirect(url_for("food_library"))
    return render_template("add_food.html")

@app.route("/food_library", methods=["GET", "POST"])
def food_library():
    return render_template("food_library.html")

@app.route("/set_goals", methods=["GET", "POST"])
def set_goals():
    if request.method == "POST":
        calories = request.form.get("calories")
        fats = request.form.get("fats")
        protein = request.form.get("protein")
        carbs = request.form.get("carbs")
        print(f"Updated Goals Saved -> Calories: {calories}, Fats: {fats}%, Protein: {protein}%, Carbs: {carbs}%")
        return redirect(url_for("dashboard"))
    return render_template("set_goals.html")

@app.route("/daily_menu", methods=["GET", "POST"])
def daily_menu():
    selected_date = request.args.get("date", "12")
    selected_meal = request.args.get("meal", "Breakfast")
    
    
    return render_template(
        "daily_menu.html", 
        selected_date=selected_date, 
        selected_meal=selected_meal
    )


if __name__ == "__main__":
    app.run(debug=True)