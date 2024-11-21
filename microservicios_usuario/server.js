// server.js
const express = require('express');
const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');
const User = require('./user');
const app = express();
app.use(express.json());

// Zipkin
const opentelemetry = require("@opentelemetry/api")
const { NodeSDK } = require("@opentelemetry/sdk-node")
const { ZipkinExporter } = require("@opentelemetry/exporter-zipkin")
const { Resource } = require("@opentelemetry/resources")
const { SemanticResourceAttributes } = require("@opentelemetry/semantic-conventions")
const { ExpressInstrumentation } = require("@opentelemetry/instrumentation-express")
const { MongooseInstrumentation } = require("@opentelemetry/instrumentation-mongoose")
const { HttpInstrumentation } = require("@opentelemetry/instrumentation-http")
// const { SimpleSpanProcessor } = require("@opentelemetry/sdk-trace-base")
// const { NodeTracerProvider } = require("@opentelemetry/sdk-trace-node")
// const { registerInstrumentations } = require("@opentelemetry/instrumentation")

// Clave secreta para JWT (en producción, usar una variable de entorno)
const SECRET_KEY = 'clave_secreta';
const MONGO_URL = process.env.MONGO_URL || 'mongodb://localhost:27017/microservicios';

// Configurar la instrumentación de OpenTelemetry y Zipkin
const sdk = new NodeSDK({
    resource: new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: 'user-service',
    }),
    traceExporter: new ZipkinExporter({
        url: "http://zipkin:9411/api/v2/spans",
    }),
    instrumentations: [
        new HttpInstrumentation(),
        new ExpressInstrumentation(),
        new MongooseInstrumentation(),
    ],
})

sdk.start()

const tracer = opentelemetry.trace.getTracer('user-service')

// Middleware para rastrear las solicitudes
app.use((req, res, next) => {
    const span = tracer.startSpan(`[${req.method}] ${req.originalUrl}`)
    res.on('finish', () => {
        span.setAttributes({
            "http.status_code": res.statusCode,
            "http.method": req.method,
            "http.url": req.originalUrl
        })
        // Cerrar la traza cuando la respuesta se haya enviado
        span.end()
    })
    next()
})

// Conectar a MongoDB
mongoose.connect(MONGO_URL, {
    useNewUrlParser: true,
    useUnifiedTopology: true
})
.then(() => console.log("Conexión exitosa a MongoDB"))
.catch(err => console.log("Error al conectar con MongoDB: ", err.message))

// Ruta de registro
app.post('/register', async (req, res) => {
    const span = tracer.startSpan('register_user')
    try {
        const { username, password } = req.body;
        const user = new User({ username, password });
        await user.save();
        res.status(201).send({ message: 'Usuario registrado' });
    } catch (err) {
        span.recordException(err)
        res.status(400).send({ error: 'Error al registrar usuario', details: err });
    } finally {
        span.end()
    }
});

app.get('/alive', async (req, res) => {
    const span = tracer.startSpan('alive_check')
    try {
        res.status(200).send('alive ...')
    } catch (err) {
        span.recordException(err)
        res.status(500).send('something is going wrong')
    } finally {
        span.end()
    }
})

app.get('/livez', async (req, res) => {
    const span = tracer.startSpan('liveness check')
    res.status(200).send('OK')
    span.end()
})

// Ruta de login
app.post('/login', async (req, res) => {
    const span = tracer.startSpan('login_user')
    try {
        const { username, password } = req.body;
        const user = await User.findOne({ username });
        if (!user) {
            span.addEvent('User not found')
            return res.status(401).send({ error: 'Usuario no encontrado' });
        }
        
        const isMatch = await user.comparePassword(password);
        if (!isMatch) {
            span.addEvent('Incorrect password')
            return res.status(401).send({ error: 'Contraseña incorrecta' });
        }
        // Generar token JWT
        const token = jwt.sign({ sub: user._id }, SECRET_KEY, { expiresIn: '1h' });
        res.send({ token });
    } catch (err) {
        span.recordException(err)
        res.status(400).send({ error: 'Error al iniciar sesión', details: err });
    } finally {
        span.end()
    }
});

// Middleware de autenticación
function authMiddleware(req, res, next) {
    const span = tracer.startSpan('auth_middleware')
    const authHeader = req.headers['authorization'];
    if (!authHeader) {
        span.addEvent("No token provided")
        span.end()
        return res.status(401).send({ error: 'Token no proporcionado' });
    }
    
    const token = authHeader.split(' ')[1]; // Extrae el token después de "Bearer"
    if (!token) {
        span.addEvent("No token provided!")
        span.end()
        return res.status(401).send({ error: 'Token no proporcionado' });
    }

    jwt.verify(token, SECRET_KEY, (err, decoded) => {
        if (err) {
            span.recordException(err)
            span.end()
            return res.status(403).send({ error: 'Token inválido' });
        }

        req.userId = decoded.sub;
        span.end()
        next();
    });
}

// Ruta protegida de perfil
app.get('/profile', authMiddleware, async (req, res) => {
    const span = tracer.startSpan('get_profile')
    try {
        const user = await User.findById(req.userId).select('-password');
        res.send(user);
    } catch (err) {
        span.recordException(err)
        res.status(400).send({ error: 'Error al obtener el perfil', details: err });
    } finally {
        span.end()
    }
});

app.listen(3000, () => {
    console.log('Microservicio de Usuarios ejecutándose en el puerto 3000');
});
