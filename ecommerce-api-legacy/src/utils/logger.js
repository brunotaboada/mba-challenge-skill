'use strict';

const config = require('../config');

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const current = LEVELS[config.logLevel] ?? LEVELS.info;

function maskCard(value) {
    if (!value) return value;
    const s = String(value);
    if (s.length < 8) return '****';
    return `${s.slice(0, 4)}-****-****-${s.slice(-4)}`;
}

function emit(level, message, meta) {
    if (LEVELS[level] > current) return;
    const payload = { level, time: new Date().toISOString(), msg: message };
    if (meta && typeof meta === 'object') {
        for (const [k, v] of Object.entries(meta)) {
            payload[k] = k.match(/card|password|pass|secret|key/i) ? maskCard(v) : v;
        }
    }
    console.log(JSON.stringify(payload));
}

module.exports = {
    info: (m, meta) => emit('info', m, meta),
    warn: (m, meta) => emit('warn', m, meta),
    error: (m, meta) => emit('error', m, meta),
    debug: (m, meta) => emit('debug', m, meta),
};
