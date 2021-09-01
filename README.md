![Image of ChessCorPy](https://raw.githubusercontent.com/kurtjd/chesscorpy/master/chesscorpy/static/img/screenshot.png)

ChessCorPy
====================
A simple web-based correspondence chess application written in Python+Flask.

This was made just to get familliar with Flask and Python as a back-end web development platform. 
Thus, I spent very little time on the front-end and it's pretty ugly.

Although this does not have near the number of features of professional chess apps, it has all the basics such as:

* Account creation system
* Creating and viewing game challenges
* Automatic email notifications when a move is played
* Input validation, error handling, and basic security
* And of course, a playable chess board!

Requirements
============
* Python 3+
* All requirements in requirements.txt

Installation
============
```pip install -r requirements.txt```

Run
===
In the folder where the chesscorpy package is located:

```
export FLASK_APP=chesscorpy
flask run
```

Configure
=========
* In app.py, modify email configuration if you wish to have emails sent out to players.
* Modify database.py if you wish to use a database platform other than SQLite.

Acknowledgements
================
* Chris Oakman (chessboard.js)
* Jeff Hlywa (chess.js)
