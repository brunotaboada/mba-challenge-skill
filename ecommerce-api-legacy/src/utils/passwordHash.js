'use strict';

const bcrypt = require('bcrypt');

const ROUNDS = 10;

async function hashPassword(plaintext) {
    if (!plaintext) {
        throw new Error('password is required');
    }
    return bcrypt.hash(String(plaintext), ROUNDS);
}

async function verifyPassword(plaintext, hash) {
    try {
        return await bcrypt.compare(String(plaintext), String(hash));
    } catch {
        return false;
    }
}

module.exports = { hashPassword, verifyPassword };
