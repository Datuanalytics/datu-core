// Ensure jest-dom matchers are available in all tests
require("@testing-library/jest-dom");

const { TextEncoder, TextDecoder } = require("util");
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;
