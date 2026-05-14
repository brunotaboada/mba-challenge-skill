'use strict';

class DomainError extends Error {
    constructor(message, statusCode = 400) {
        super(message);
        this.name = this.constructor.name;
        this.statusCode = statusCode;
    }
}

class NotFoundError extends DomainError {
    constructor(message = 'Resource not found') {
        super(message, 404);
    }
}

class ValidationError extends DomainError {
    constructor(message = 'Invalid input') {
        super(message, 400);
    }
}

class PaymentDeniedError extends DomainError {
    constructor(message = 'Pagamento recusado') {
        super(message, 402);
    }
}

module.exports = { DomainError, NotFoundError, ValidationError, PaymentDeniedError };
