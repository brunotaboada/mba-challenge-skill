'use strict';

const { get, run } = require('../db/connection');

async function findByEmail(email) {
    return get('SELECT id, name, email FROM users WHERE email = ?', [email]);
}

async function findById(id) {
    return get('SELECT id, name, email FROM users WHERE id = ?', [id]);
}

async function create({ name, email, hashedPassword }) {
    const { lastID } = await run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, hashedPassword]
    );
    return lastID;
}

async function deleteById(id) {
    await run('DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, findById, create, deleteById };
