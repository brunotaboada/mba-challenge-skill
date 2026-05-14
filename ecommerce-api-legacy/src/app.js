'use strict';

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

const config = require('./config');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

function createApp() {
    const app = express();
    app.use(helmet());
    app.use(cors({ origin: config.allowedOrigins }));
    app.use(express.json({ limit: '64kb' }));

    app.use(routes);
    app.use(errorHandler);

    return app;
}

module.exports = createApp;
