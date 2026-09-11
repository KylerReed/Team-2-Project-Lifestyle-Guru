from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)


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
        selected_age = request.form.get("selected_age")
        print(f"User selected age: {selected_age}")

        return redirect(url_for("weight"))

    return render_template("age.html")


@app.route("/weight", methods=["GET", "POST"])
def weight():
    if request.method == "POST":
        selected_weight = request.form.get("selected_weight")
        print(f"User selected weight: {selected_weight}")

        return redirect(url_for("gender"))

    return render_template("weight.html")


@app.route("/gender", methods=["GET", "POST"])
def gender():
    if request.method == "POST":
        selected_gender = request.form.get("gender")
        print(f"User selected gender: {selected_gender}")

        return redirect(url_for("height"))

    return render_template("gender.html")


@app.route("/height", methods=["GET", "POST"])
def height():
    if request.method == "POST":
        selected_height = request.form.get("height_value")
        print(f"User selected height: {selected_height}")

        return redirect(url_for("activity"))

    return render_template("height.html")


@app.route("/activity", methods=["GET", "POST"])
def activity():
    if request.method == "POST":
        selected_activity = request.form.get("activity")
        print(f"User selected activity: {selected_activity}")

        return redirect(url_for("goal"))

    return render_template("activity.html")


@app.route("/goal", methods=["GET", "POST"])
def goal():
    if request.method == "POST":
        selected_goal = request.form.get("goal")
        print(f"User selected goal: {selected_goal}")

    return render_template("goal.html")


if __name__ == "__main__":
    app.run(debug=True)
