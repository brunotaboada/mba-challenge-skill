'use strict';

const { run } = require('../db/connection');

async function log(action) {
    await run('INSERT INTO audit_logs (action) VALUES (?)', [action]);
}

module.exports = { log };
