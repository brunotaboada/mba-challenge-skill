'use strict';

const checkoutService = require('../services/checkoutService');

async function postCheckout(req, res) {
    const { usr, eml, pwd, c_id: courseId, card } = req.body || {};
    const result = await checkoutService.checkout({
        name: usr,
        email: eml,
        password: pwd,
        courseId: parseInt(courseId, 10),
        cardNumber: card,
    });
    res.status(200).json({
        msg: 'Sucesso',
        enrollment_id: result.enrollmentId,
        transaction_id: result.transactionId,
    });
}

module.exports = { postCheckout };
