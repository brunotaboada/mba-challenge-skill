'use strict';

require('dotenv').config();

function required(name) {
    const value = process.env[name];
    if (!value && process.env.NODE_ENV === 'production') {
        throw new Error(`Required env var ${name} is missing`);
    }
    return value;
}

const config = {
    nodeEnv: process.env.NODE_ENV || 'development',
    port: parseInt(process.env.PORT || '3000', 10),
    dbPath: process.env.DB_PATH || './data/lms.db',
    dbUser: required('DB_USER') || 'admin_master',
    dbPass: required('DB_PASS') || 'dev-only-not-for-prod',
    paymentGatewayKey: required('PAYMENT_GATEWAY_KEY') || 'pk_test_dev',
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
    allowedOrigins: (process.env.ALLOWED_ORIGINS || 'http://localhost:3000')
        .split(',')
        .map(s => s.trim())
        .filter(Boolean),
    logLevel: process.env.LOG_LEVEL || 'info',
};

module.exports = config;
