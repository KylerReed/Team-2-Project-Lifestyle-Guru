from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
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
