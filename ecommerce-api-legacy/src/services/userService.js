'use strict';

const userModel = require('../models/userModel');
const { transaction, run } = require('../db/connection');
const { NotFoundError } = require('../utils/errors');

async function deleteUser(userId) {
    const user = await userModel.findById(userId);
    if (!user) {
        throw new NotFoundError('Usuário não encontrado');
    }
    // ON DELETE CASCADE no schema garante remoção de enrollments e payments,
    // mas explicitamos a transação para isolamento.
    return transaction(async () => {
        await run('DELETE FROM users WHERE id = ?', [userId]);
        await run('INSERT INTO audit_logs (action) VALUES (?)',
            [`User ${userId} deleted (cascade)`]);
    });
}

module.exports = { deleteUser };
