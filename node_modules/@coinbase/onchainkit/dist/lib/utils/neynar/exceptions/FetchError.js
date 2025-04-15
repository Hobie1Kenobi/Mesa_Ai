"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FetchError = void 0;
class FetchError extends Error {
    constructor(message) {
        super(message);
        this.name = 'FetchError';
    }
}
exports.FetchError = FetchError;
//# sourceMappingURL=FetchError.js.map