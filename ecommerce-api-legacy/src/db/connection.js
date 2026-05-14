'use strict';

const path = require('path');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

const config = require('../config');

const dbPath = config.dbPath === ':memory:'
    ? ':memory:'
    : path.resolve(process.cwd(), config.dbPath);

if (dbPath !== ':memory:') {
    fs.mkdirSync(path.dirname(dbPath), { recursive: true });
}

const db = new sqlite3.Database(dbPath);
db.run('PRAGMA foreign_keys = ON');

function all(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
}

function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function cb(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

async function transaction(work) {
    await run('BEGIN');
    try {
        const result = await work();
        await run('COMMIT');
        return result;
    } catch (err) {
        await run('ROLLBACK');
        throw err;
    }
}

module.exports = { db, all, get, run, transaction };
