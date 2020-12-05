from flask import Flask, json, request
from pymongo import MongoClient
import datetime


USER = "grupo6"
PASS = "grupo6"
DATABASE = "grupo6"

URL = f"mongodb://{USER}:{PASS}@gray.ing.puc.cl/{DATABASE}?authSource=admin"
client = MongoClient(URL)

MESSAGE_KEYS = ["date", "lat", "long", "message", "receptant", "sender"]

db = client["grupo6"]

mensajes = db.mensajes
usuarios = db.usuarios
app = Flask(__name__)


# Funciones útiles
def check_date(string):
    '''
    https://www.kite.com/python/answers/how-to-validate-a-date-string-format-in-python
    '''
    format = "%Y-%m-%d"

    try:
        print(string)
        datetime.datetime.strptime(string, format)
        return True
    except ValueError:
        return False

def check_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
# Fin funciones útiles

# DB check
def check_uid(uid):
    query = usuarios.find({}, {"_id": 0, "uid": 1})
    uids = [user["uid"] for user in query]
    if uid in uids:
        return True
    else:
        return False

def check_mid(mid):
    query = mensajes.find({}, {"_id": 0, "mid": 1})
    mids = [message["mid"] for message in query]
    if mid in mids:
        return True
    else:
        return False


@app.route("/")
def home():
    query = usuarios.find({}, {"_id": 0})
    jsoneada = json.jsonify(list(query))
    return jsoneada


@app.route("/users", methods=['GET'])
def get_users():
    query = usuarios.find({}, {"_id": 0})
    jsoneada = json.jsonify(list(query))
    return jsoneada


@app.route("/messages", methods=['GET'])
def get_messages():
    ids = request.args
    if "id1" in ids.keys() and "id2" in ids.keys():
        id1 = int(ids["id1"])
        id2 = int(ids["id2"])
        inexistentes = []
        if not check_uid(id1):
            inexistentes.append(id1)
        if not check_uid(id2):
            inexistentes.append(id2)
        if inexistentes:
            error = {"exito": False, "error": {"uids_inexistentes": inexistentes}}
            return json.jsonify(error)
        query = mensajes.find({"$or": [{"$and": [{"sender": id1}, {"receptant": id2}]}, {"$and": [{"receptant": id1}, {"sender": id2}]}]}, {"_id": 0})
    else:
        query = mensajes.find({}, {"_id": 0})
    jsoneada = json.jsonify(list(query))
    return jsoneada


@app.route("/users/<int:id>", methods=['GET'])
def get_user(id):
    if not check_uid(id):
        error = {"exito": False, "error": "uid no existe"}
        return json.jsonify(error)
    query = mensajes.find({"sender": id}, {"_id": 0})
    user = usuarios.find({"uid": id}, {"_id": 0})
    mensajes_tela = [doc for doc in query]
    user_tela = [doc for doc in user]
    return json.jsonify({"user": user_tela, "messages": mensajes_tela})


@app.route("/messages/<int:id>", methods=['GET'])
def get_message(id):
    if not check_mid(id):
        error = {"exito": False, "error": "mid no existe"}
        return json.jsonify(error)
    query = mensajes.find({"mid": id}, {"_id": 0})
    jsoneada = json.jsonify(list(query))
    return jsoneada


@app.route("/text-search", methods=['GET'])
def text_search():
    # mensajes.createIndex({"message": "text"}, {"default_language": "none"})  SE IMPLEMENTÓ DIRECTO EN LA DB
    desired = []
    required = []
    forbidden = []
    uid = None

    if request.data:
        req = request.json
        if "desired" in req.keys():
            desired = req["desired"]
        if "required" in req.keys():
            required = req["required"]
        if "forbidden" in req.keys():
            forbidden = req["forbidden"]
        if "userId" in req.keys():
            uid = int(req["userId"])
            if not check_uid(uid):
                error = {"exito": False, "error": "userId no existe"}
                return json.jsonify(error)
        
        if not desired and not required and not forbidden:
            if type(uid) != int:
                return get_messages()
            elif type(uid) == int:
                query = mensajes.find({"sender": uid}, {"_id": 0})
                return json.jsonify(list(query))

        # Realizamos la consulta
        texto = []
        if desired:
            texto.extend(desired)
        if required:
            required_bkn = [f'\"{requi}\"' for requi in required]
            texto.extend(required_bkn)
        if forbidden:
            forbidden_bkn = [f"-{forbi}" for forbi in forbidden]
            texto.extend(forbidden_bkn)
            if not desired and not required:
                prohibidas = " ".join(forbidden)
                mids_malos = mensajes.find({"$text": {"$search": prohibidas}}, {"mid": 1, "_id": 0})
                mids_malos = [mid["mid"] for mid in mids_malos]
                if type(uid) == int:
                    query = mensajes.find({"$and": [{"sender": uid}, {"mid": {"$nin": list(mids_malos)}}]}, {"_id": 0})
                else:
                    query = mensajes.find({"mid": {"$nin": list(mids_malos)}}, {"_id": 0})
                return json.jsonify(list(query))

        mucho_texto = " ".join(texto)
        if type(uid) == int:
            query = mensajes.find({"$and": [{"sender": uid}, {"$text": {"$search": mucho_texto}}]}, {"_id": 0, "score": { "$meta": "textScore" }}).sort([('score', {'$meta': 'textScore'})])
        else:
            query = mensajes.find({"$text": {"$search": mucho_texto}}, {"_id": 0, "score": { "$meta": "textScore" }}).sort([('score', {'$meta': 'textScore'})])
        
        return json.jsonify(list(query))
    else:
        return get_messages()



@app.route("/messages", methods=['POST'])
def create_user():

    req = request.json

    if not req:
        return json.jsonify({"error": "dame un input porfaaa"})

    faltantes = []
    for elem in MESSAGE_KEYS:
        if elem not in req.keys():
            faltantes.append(elem)

    if not faltantes:
        invalidos = []
        # Revisamos los atributos que requieren un formato específico y que los uids existan
        if not check_date(req["date"]):
            invalidos.append("date")
        if not check_float(req["lat"]):
            invalidos.append("lat")
        if not check_float(req["long"]):
            invalidos.append("long")
        if not check_uid(req["sender"]):
            invalidos.append("sender")
        if not check_uid(req["receptant"]):
            invalidos.append("receptant")

        if invalidos:
            error = {"exito": False, "error": {"atributos_invalidos": invalidos}}
            return json.jsonify(error)

        # Agregamos el mid que sea una unidad mayor al máximo
        max_mid = mensajes.find({}, {"_id": 0, "mid": 1}).sort([("mid", -1)]).limit(1)
        max_mid = max_mid[0]["mid"]
        new_mid = max_mid + 1

        data = {key: request.json[key] for key in MESSAGE_KEYS}
        data["mid"] = new_mid
        print(data)
        mensajes.insert_one(data)

        return json.jsonify({"exito": True})
    else:
        error = {"exito": False, "error": {"atributos_faltantes": faltantes}}
        return json.jsonify(error)


@app.route("/message/<int:id>", methods=['DELETE'])
def delete_message(id):
    if not check_mid(id):
        error = {"exito": False, "error": "mid no existe"}
        return json.jsonify(error)

    # Si está todo bien, sigue...
    mensajes.remove({"mid": id})
    return json.jsonify({"exito": True})

if __name__ == "__main__":
    app.run(debug=True)
