'use strict';

const logger = require('../utils/logger');
const { DomainError } = require('../utils/errors');

// 4-arg signature is required by Express to recognize this as error middleware.
// eslint-disable-next-line no-unused-vars
module.exports = function errorHandler(err, req, res, next) {
    if (err instanceof DomainError) {
        logger.warn('domain.error', { msg: err.message, status: err.statusCode });
        return res.status(err.statusCode).json({ error: err.message });
    }
    logger.error('unhandled.error', { msg: err.message, stack: err.stack });
    res.status(500).json({ error: 'Internal server error' });
};
