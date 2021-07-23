from flask import Flask
from flask_session import Session

app = Flask(__name__)

# Configure sessions
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Routes were defined in individual files, so import them here.
import chesscorpy.index
import chesscorpy.register
