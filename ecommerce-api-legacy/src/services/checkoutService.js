'use strict';

const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditModel = require('../models/auditModel');
const paymentGateway = require('./paymentGateway');
const { hashPassword } = require('../utils/passwordHash');
const { transaction } = require('../db/connection');
const { NotFoundError, ValidationError } = require('../utils/errors');
const logger = require('../utils/logger');

async function checkout({ name, email, password, courseId, cardNumber }) {
    if (!name || !email || !courseId || !cardNumber) {
        throw new ValidationError('Campos obrigatórios: name, email, courseId, cardNumber');
    }
    if (!password) {
        throw new ValidationError('password é obrigatório');
    }

    const course = await courseModel.findActiveById(courseId);
    if (!course) {
        throw new NotFoundError('Curso não encontrado');
    }

    const auth = await paymentGateway.authorize({
        cardNumber,
        amount: course.price,
    });

    let user = await userModel.findByEmail(email);
    return transaction(async () => {
        if (!user) {
            const hash = await hashPassword(password);
            const newUserId = await userModel.create({
                name,
                email,
                hashedPassword: hash,
            });
            user = { id: newUserId, name, email };
        }

        const enrollmentId = await enrollmentModel.create({
            userId: user.id,
            courseId,
        });
        await paymentModel.create({
            enrollmentId,
            amount: course.price,
            status: auth.status,
        });
        await auditModel.log(`Checkout curso ${courseId} por ${user.id}`);

        logger.info('checkout.completed', {
            userId: user.id,
            courseId,
            enrollmentId,
            transactionId: auth.transactionId,
        });

        return { enrollmentId, transactionId: auth.transactionId };
    });
}

module.exports = { checkout };
