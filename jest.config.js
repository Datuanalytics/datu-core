const path = require("path");

module.exports = {
  rootDir: ".",
  testMatch: ["<rootDir>/tests/frontend/**/*.test.js"],
  testPathIgnorePatterns: ["/node_modules/", "/dist/"],
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    "^@src/(.*)$": "<rootDir>/frontend/src/$1",
  },
  setupFilesAfterEnv: ["@testing-library/jest-dom"],
  moduleDirectories: ["node_modules", path.resolve(__dirname, "node_modules")],
  transform: {
    "^.+\\.[jt]sx?$": "babel-jest",
  },
  transformIgnorePatterns: [
    "/node_modules/(?!(react-monaco-editor|monaco-editor)/)",
  ],
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
};
