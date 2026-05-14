'use strict';

const { run, get } = require('./connection');
const { hashPassword } = require('../utils/passwordHash');

const SCHEMA = [
    `CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER DEFAULT 1
    )`,
    `CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id)
    )`,
    `CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL NOT NULL,
        status TEXT NOT NULL
    )`,
    `CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        created_at DATETIME DEFAULT (datetime('now'))
    )`,
];

async function init() {
    for (const stmt of SCHEMA) {
        await run(stmt);
    }
    const { c } = await get('SELECT COUNT(*) AS c FROM users');
    if (c === 0) {
        await seed();
    }
}

async function seed() {
    const adminHash = await hashPassword('123');
    await run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', adminHash]);
    await run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1)");
    await run("INSERT INTO courses (title, price, active) VALUES ('Docker', 497.00, 1)");
    await run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { init };
