'use strict';

const config = require('../config');
const logger = require('../utils/logger');
const { PaymentDeniedError } = require('../utils/errors');

/**
 * Adapter para o gateway de pagamento. Em produção, esta implementação deve
 * chamar Stripe/Pagar.me/etc. Aqui mantemos um stub determinístico, mas com
 * mascaramento de PAN no log e validação Luhn mínima.
 */
function luhnValid(cardNumber) {
    const digits = String(cardNumber).replace(/\D/g, '');
    if (digits.length < 12 || digits.length > 19) return false;
    let sum = 0;
    let alt = false;
    for (let i = digits.length - 1; i >= 0; i--) {
        let n = parseInt(digits[i], 10);
        if (alt) {
            n *= 2;
            if (n > 9) n -= 9;
        }
        sum += n;
        alt = !alt;
    }
    return sum % 10 === 0;
}

async function authorize({ cardNumber, amount }) {
    if (!luhnValid(cardNumber)) {
        throw new PaymentDeniedError('Cartão inválido');
    }
    // log com card mascarado pelo logger
    logger.info('payment.authorize', {
        amount,
        cardNumber,
        gatewayKeyConfigured: Boolean(config.paymentGatewayKey),
    });
    // Stub previsível: cartões iniciados em 4 (Visa) e válidos por Luhn passam.
    const approved = String(cardNumber).startsWith('4');
    if (!approved) {
        throw new PaymentDeniedError('Pagamento recusado');
    }
    return { status: 'PAID', transactionId: `tx_${Date.now()}` };
}

module.exports = { authorize };
