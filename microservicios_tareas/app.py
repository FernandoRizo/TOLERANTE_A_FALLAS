# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
)
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
import jwt

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'clave_secreta'  # Debe ser la misma clave usada en el Microservicio de Usuarios
app.config['JWT_IDENTITY_CLAIM'] = 'sub'  # Usamos 'sub' como claim de identidad

jwt_manager = JWTManager(app)

# Conectar a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.microservicios
tasks_collection = db.tasks

# Ruta para la página de inicio (formulario de inicio de sesión)
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Obtener credenciales del formulario
        username = request.form['username']
        password = request.form['password']

        # Realizar una solicitud al Microservicio de Usuarios para obtener el token
        response = requests.post('http://localhost:3000/login', json={
            'username': username,
            'password': password
        })

        if response.status_code != 200:
            error_message = response.json().get('error', 'Error desconocido')
            return render_template('login.html', error=error_message)

        token = response.json()['token']

        # Guardar el token en una cookie (para simplificar; en producción usar sesiones seguras)
        resp = redirect(url_for('show_tasks'))
        resp.set_cookie('token', token)
        return resp

    return render_template('login.html')

# Ruta para mostrar las tareas
@app.route('/tasks', methods=['GET', 'POST'])
def show_tasks():
    # Obtener el token de la cookie
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('home'))

    try:
        # Decodificar el token para obtener el user_id
        decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        user_id = decoded_token['sub']
    except jwt.ExpiredSignatureError:
        return redirect(url_for('home'))
    except jwt.InvalidTokenError:
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Añadir una nueva tarea
        title = request.form['title']
        description = request.form['description']
        task_data = {
            'title': title,
            'description': description,
            'user_id': user_id
        }
        tasks_collection.insert_one(task_data)
        return redirect(url_for('show_tasks'))

    # Obtener las tareas del usuario
    tasks = list(tasks_collection.find({'user_id': user_id}))
    for task in tasks:
        task['_id'] = str(task['_id'])

    return render_template('tasks.html', tasks=tasks)

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    resp = redirect(url_for('home'))
    resp.set_cookie('token', '', expires=0)
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
