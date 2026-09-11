from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

@app.route("/age", methods=["GET", "POST"])
def age():
    if request.method == "POST":
        selected_age = request.form.get("selected_age")
        
        print(f"User selected age: {selected_age}")
    return render_template("age.html")

@app.route("/weight", methods=["GET", "POST"])
def weight():
    if request.method == "POST":
        selected_weight = request.form.get("selected_weight")
        print(f"User selected weight: {selected_weight}")
    return render_template("weight.html")

@app.route("/gender", methods=["GET", "POST"])
def gender():
    if request.method == "POST":
        selected_gender = request.form.get("gender")
        print(f"User selected gender: {selected_gender}")
    return render_template("gender.html")

@app.route("/height", methods=["GET", "POST"])
def height():
    if request.method == "POST":
        selected_height = request.form.get("selected_height")
        print(f"User selected height: {selected_height}")
    return render_template("height.html")

@app.route('/activity', methods=['GET', 'POST'])
def activity():
    if request.method == 'POST':
        
        pass
    return render_template('activity.html')

@app.route('/goal', methods=['GET', 'POST'])
def goal():
    if request.method == 'POST':
        # Handle saving the goal data here
        pass
    return render_template('goal.html')

@app.route("/profile", methods=["GET", "POST"])
def profile():
    message = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        height = request.form.get("height", "").strip()
        weight = request.form.get("weight", "").strip()
        activity_level = request.form.get("activity_level", "").strip()
        calorie_goal = request.form.get("calorie_goal", "").strip()

        if not all([name, age, height, weight, activity_level, calorie_goal]):
            message = "Please complete all profile fields."
        else:
            message = "Profile information accepted."

    return render_template("profile.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=True)
