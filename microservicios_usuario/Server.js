// server.js
const express = require('express');
const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');
const User = require('./user');
const app = express();
app.use(express.json());

// Clave secreta para JWT (en producción, usar una variable de entorno)
const SECRET_KEY = 'clave_secreta';

// Conectar a MongoDB
mongoose.connect('mongodb://localhost:27017/microservicios', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

// Ruta de registro
app.post('/register', async (req, res) => {
    try {
        const { username, password } = req.body;
        const user = new User({ username, password });
        await user.save();
        res.status(201).send({ message: 'Usuario registrado' });
    } catch (err) {
        res.status(400).send({ error: 'Error al registrar usuario', details: err });
    }
});

// Ruta de login
app.post('/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        const user = await User.findOne({ username });
        if (!user) return res.status(401).send({ error: 'Usuario no encontrado' });

        const isMatch = await user.comparePassword(password);
        if (!isMatch) return res.status(401).send({ error: 'Contraseña incorrecta' });

        // Generar token JWT
        const token = jwt.sign({ sub: user._id }, SECRET_KEY, { expiresIn: '1h' });
        res.send({ token });
    } catch (err) {
        res.status(400).send({ error: 'Error al iniciar sesión', details: err });
    }
});

// Middleware de autenticación
function authMiddleware(req, res, next) {
    const authHeader = req.headers['authorization'];
    if (!authHeader) return res.status(401).send({ error: 'Token no proporcionado' });

    const token = authHeader.split(' ')[1]; // Extrae el token después de "Bearer"
    if (!token) return res.status(401).send({ error: 'Token no proporcionado' });
    
    jwt.verify(token, SECRET_KEY, (err, decoded) => {
        if (err) return res.status(403).send({ error: 'Token inválido' });
        req.userId = decoded.sub;
        next();
    });
}

// Ruta protegida de perfil
app.get('/profile', authMiddleware, async (req, res) => {
    try {
        const user = await User.findById(req.userId).select('-password');
        res.send(user);
    } catch (err) {
        res.status(400).send({ error: 'Error al obtener el perfil', details: err });
    }
});

app.listen(3000, () => {
    console.log('Microservicio de Usuarios ejecutándose en el puerto 3000');
});
