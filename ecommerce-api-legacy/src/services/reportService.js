'use strict';

const enrollmentModel = require('../models/enrollmentModel');

async function financialReport() {
    const rows = await enrollmentModel.listWithDetails();
    const byCourse = new Map();

    for (const row of rows) {
        const courseId = row.course_id;
        if (!byCourse.has(courseId)) {
            byCourse.set(courseId, {
                course: row.course_title,
                revenue: 0,
                students: [],
            });
        }
        const bucket = byCourse.get(courseId);
        if (!row.enrollment_id) continue;
        if (row.payment_status === 'PAID') {
            bucket.revenue += row.payment_amount || 0;
        }
        bucket.students.push({
            student: row.user_name || 'Unknown',
            paid: row.payment_amount || 0,
        });
    }

    return Array.from(byCourse.values());
}

module.exports = { financialReport };
