'use strict';

const { get, all } = require('../db/connection');

async function findActiveById(id) {
    return get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

async function listAll() {
    return all('SELECT id, title, price, active FROM courses');
}

module.exports = { findActiveById, listAll };
