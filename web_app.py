from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    return render_template(".html")


@app.route('/upload', methods=['GET', 'POST'])
def upload_images():
    """..."""
    ...


@app.route("/resultat_ajout",methods = ["GET"])
def resultat_ajout():
    #result=request.args
    #n = result["nom"]
    n=42
    return render_template("test.html", val=n, )
