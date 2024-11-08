# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
)
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
import jwt

# Monitorización con opentelemetry y zipkin
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace import get_current_span

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'clave_secreta'  # Debe ser la misma clave usada en el Microservicio de Usuarios
app.config['JWT_IDENTITY_CLAIM'] = 'sub'  # Usamos 'sub' como claim de identidad

jwt_manager = JWTManager(app)

# Conectar a MongoDB
client = MongoClient('mongodb://mongodb:27017/')
db = client.microservicios
tasks_collection = db.tasks

# region openTelemetry
# Configurar el nombre del servicio para opentelemetry
resource = Resource(attributes={
    "service.name": "microservicio_tareas"
})

trace.set_tracer_provider(TracerProvider(resource=resource))

# Exportar zipkin
zipkin_exporter = ZipkinExporter(
    # Asegurarse de que Zipkin esté ejecutándose en este endpoint
    endpoint="http://zipkin:9411/api/v2/spans"
)

# Procesador de spans (para enviar los datos de trace)
span_processor = BatchSpanProcessor(zipkin_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

FlaskInstrumentor.instrument_app(app)

# Obtener el span actual y asociar el _id del usuario como atributo ademas de la petición HTTP
def get_span(user_id = "invitado", request = "GET"):
    span = get_current_span()
    if span:
        span.set_attribute("app.user_id", user_id)
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url)

# Ruta para la página de inicio (formulario de inicio de sesión)
@app.route('/', methods=['GET', 'POST'])
def home():
    
    # Obtener el span actual
    get_span(request=request)
        
    if request.method == 'POST':
        # Obtener credenciales del formulario
        username = request.form['username']
        password = request.form['password']

        # Realizar una solicitud al Microservicio de Usuarios para obtener el token
        response = requests.post('http://user-service:3000/login', json={
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    
    # Obtener el span actual
    get_span(request=request)
        
    if request.method == 'POST':
        # Obtener credenciales del formulario
        username = request.form['username']
        password = request.form['password']

        # Realizar una solicitud al Microservicio de Usuarios para obtener el token
        response = requests.post('http://user-service:3000/register', json={
            'username': username,
            'password': password
        })

        print("status: ",response.status_code)
        if response.status_code != 201:
            error_message = response.json().get('error', 'Error desconocido')
            return render_template('register.html', error=error_message)

        return redirect(url_for('home'))
    
    return render_template('register.html')

# Ruta para mostrar las tareas
@app.route('/tasks', methods=['GET', 'POST'])
def show_tasks():
    
    # Obtener el token de la cookie
    token = request.cookies.get('token')
    if not token:
        print("no token")
        return redirect(url_for('home'))

    try:
        # Decodificar el token para obtener el user_id
        decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        user_id = decoded_token['sub']
        
        # Obtener el span actual
        get_span(user_id, request)

    except jwt.ExpiredSignatureError:
        print("[-] Expired token")
        return redirect(url_for('home'))
    except jwt.InvalidTokenError:
        print("[-] Invalid token")
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

# Ruta para crear tarea
@app.route('/task_form', methods=['GET', 'POST'])
def task_form():
    
    # Obtener el token de la cookie
    token = request.cookies.get("token")
    if not token:
        print("No token")
        return redirect(url_for("home"))
    
    try:
        # Decodificar el token para obtener el user_id
        decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        user_id = decoded_token['sub']
        
        # Obtener el span actual
        get_span(user_id, request)
        
    except jwt.ExpiredSignatureError:
        print("[-] Expired token")
        return redirect(url_for("home"))
    except jwt.InvalidTokenError:
        print("[-] Invalid token")
        return redirect(url_for("home"))
    except Exception as err:
        print("[-] Error no reconocido", err)
        return redirect(url_for("home"))

    if request.method == 'POST':
        # Si el formulario ha sido enviado, guardar la nueva tarea
        title = request.form['title']
        description = request.form['description']
        task_data = {
            'title': title,
            'description': description,
            'user_id': user_id
        }
        tasks_collection.insert_one(task_data)
        
        # Redirige a la página de tareas
        return redirect(url_for('show_tasks'))

    # Si el método es GET, mostrar el formulario para crear una tarea
    return render_template('task_form.html')

# Ruta para eliminar tarea
@app.route('/delete_task/<task_id>', methods=['POST'])
def delete_task(task_id):
    
    # Obtener el token de la cookie
    token = request.cookies.get("token")
    if not token:
        print("No token")
        return redirect(url_for("home"))
    
    try:
        # Decodificar el token para obtener el user_id
        decoded_token = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        user_id = decoded_token['sub']
        
        # Obtener el span actual
        get_span(user_id, request)
        
        result = tasks_collection.delete_one({"_id": ObjectId(task_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Tarea no encontrada"}), 404
        
        # Redirige a la página de tareas
        return redirect(url_for("show_tasks"))
    except Exception as err:
        print("[-] Error no reconocido", err)
        return jsonify({"error": "Error al eliminar la tarea", "details": str(err)}), 500
        # return redirect(url_for("home"))

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    resp = redirect(url_for('home'))
    resp.set_cookie('token', '', expires=0)
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)