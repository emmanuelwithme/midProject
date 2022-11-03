import flask

app1 = flask.Flask("__name__")

@app1.route("/")
def hello():
    return flask.render_template("home.html")

if __name__ == "__main__":
    app1.run()
