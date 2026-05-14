'use strict';

const userService = require('../services/userService');

async function deleteUser(req, res) {
    await userService.deleteUser(parseInt(req.params.id, 10));
    res.json({ message: 'Usuário deletado (matrículas e pagamentos foram removidos em cascata)' });
}

module.exports = { deleteUser };
