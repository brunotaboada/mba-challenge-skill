'use strict';

const reportService = require('../services/reportService');

async function getFinancialReport(req, res) {
    const report = await reportService.financialReport();
    res.json(report);
}

module.exports = { getFinancialReport };
