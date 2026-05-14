'use strict';

const { run, all } = require('../db/connection');

async function create({ userId, courseId }) {
    const { lastID } = await run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userId, courseId]
    );
    return lastID;
}

async function listWithDetails() {
    return all(`
        SELECT
            c.id            AS course_id,
            c.title         AS course_title,
            e.id            AS enrollment_id,
            u.id            AS user_id,
            u.name          AS user_name,
            u.email         AS user_email,
            p.amount        AS payment_amount,
            p.status        AS payment_status
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN users u       ON u.id = e.user_id
        LEFT JOIN payments p    ON p.enrollment_id = e.id
        ORDER BY c.id, e.id
    `);
}

module.exports = { create, listWithDetails };
