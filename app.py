from flask import Flask, render_template, send_file, request
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import random
from string import ascii_letters
import time

app = Flask(__name__)
CORS(app)
sock = SocketIO(app, cors_allow_origins="*")

games = {}
adm = {}


@app.route("/api/newgame", methods=["POST"])
def newgame():
    gameid = "".join(random.choices(ascii_letters, k=6))
    return gameid


@app.route("/host")
def host():
    return render_template("host.html")


@app.route("/join")
def connect():
    return render_template("join.html")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/audio/buzz.mp3")
def buzz():
    return send_file("templates/buzz.mp3")


@sock.on("adm")
def handle_new_game(code):
    if code in games.keys():
        emit("adm_ok", "NO_ADM")
        return
    emit("adm_ok", "OK")
    join_room(code + "adm")
    games[code] = []
    adm[request.sid] = code


@sock.on("adm_scoreup")
def handle_scoreup(code):
    code = code.split(",")
    if adm.get(request.sid, None) != code[0]:
        emit("adm_ok", "NO_AUTH")
        return
    for i in games[code[0]]:
        if code[1] == i[1]:
            emit("user_scoreup", to=i[0])
            return

@sock.on("adm_scoredown")
def handle_scoredown(code):
    code = code.split(",")
    if adm.get(request.sid, None) != code[0]:
        emit("adm_ok", "NO_AUTH")
        return
    for i in games[code[0]]:
        if code[1] == i[1]:
            emit("user_scoredown", to=i[0])
            return


@sock.on("user_connect")
def handle_new_user(code):
    code = code.split(",")
    if code[0] not in games.keys():
        emit("user_ok", "NO_CODE")
        return
    for i in games[code[0]]:
        if code[1] == i[1]:
            emit("user_ok", "NO_USR")
            return
    emit("user_ok", "OK")
    emit("new_user", code[1], to=code[0] + "adm")
    join_room(code[0])
    games[code[0]].append([request.sid, code[1]])


@sock.on("user_buzz")
def handle_user_buzz(code):
    code = code.split(",")
    for i in games[code[0]]:
        if request.sid == i[0]:
            if code[1] != i[1]:
                return
    emit("adm_buzz", code[1], to=code[0] + "adm")


@sock.on("adm_clearbuzz")
def clear_buzz(code):
    if adm.get(request.sid, None) != code:
        emit("adm_ok", "NO_AUTH")
        return
    emit("ubuzz_enable", "OK", to=code)


@sock.on("disconnect")
def handle_disconn():
    a = request.sid
    for i in adm.keys():
        if i == a:
            del games[adm[a]]
            emit("disconnect", "OK", to=adm[a])
            del adm[a]
            return
    for i in games.keys():
        for j in range(len(games[i])):
            if games[i][j][0] == a:
                emit("adm_deluser", games[i][j][1], to=i + "adm")
                del games[i][j]
                return


@sock.on("adm_disconn")
def handle_disconn_adm(data):
    roomcode, uname = data.split(",")
    for j in range(len(games[roomcode])):
        if games[roomcode][j][1] == uname:
            emit("disconnect", "OK", to=games[roomcode][j][0])
            del games[roomcode][j]
            return

