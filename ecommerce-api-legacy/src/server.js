'use strict';

const createApp = require('./app');
const config = require('./config');
const { init } = require('./db/schema');
const logger = require('./utils/logger');

async function main() {
    await init();
    const app = createApp();
    app.listen(config.port, () => {
        logger.info('server.started', { port: config.port });
    });
}

main().catch((err) => {
    logger.error('server.fatal', { msg: err.message, stack: err.stack });
    process.exit(1);
});
