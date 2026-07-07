"use strict";

/**
 * Core password-strength analysis logic exposed as a plain JavaScript class.
 *
 * Graftcode Gateway introspects the public methods of PasswordChecker at
 * startup and makes them remotely callable without any HTTP framework.
 *
 * No imports from express, fastify, koa, hono, or any other HTTP library.
 * Zero runtime npm dependencies — pure Node.js built-ins only.
 */

/** @type {ReadonlySet<string>} */
const COMMON_PASSWORDS = new Set([
  "password",
  "password1",
  "password123",
  "123456",
  "123456789",
  "12345678",
  "12345",
  "1234567",
  "1234567890",
  "qwerty",
  "qwerty123",
  "abc123",
  "letmein",
  "admin",
  "admin123",
  "welcome",
  "welcome1",
  "monkey",
  "dragon",
  "master",
  "sunshine",
  "princess",
  "shadow",
  "superman",
  "michael",
  "football",
  "baseball",
  "iloveyou",
  "trustno1",
  "000000",
  "111111",
  "123123",
  "654321",
]);

// ---------------------------------------------------------------------------
// Scoring helpers — each returns true when the criterion is satisfied
// ---------------------------------------------------------------------------

/** @param {string} password */
const _hasMinLength = (password) => password.length >= 8;

/** @param {string} password */
const _hasUppercase = (password) => /[A-Z]/.test(password);

/** @param {string} password */
const _hasLowercase = (password) => /[a-z]/.test(password);

/** @param {string} password */
const _hasDigit = (password) => /[0-9]/.test(password);

/** @param {string} password */
const _hasSpecial = (password) =>
  /[!@#$%^&*()\-_=+[\]{};:'",.<>/?\\|`~]/.test(password);

// ---------------------------------------------------------------------------
// Label thresholds
// ---------------------------------------------------------------------------

/**
 * @param {number} score
 * @returns {"Weak"|"Fair"|"Strong"|"Very Strong"}
 */
function _scoreToLabel(score) {
  if (score <= 1) return "Weak";
  if (score === 2) return "Fair";
  if (score === 3) return "Strong";
  return "Very Strong";
}

// ---------------------------------------------------------------------------
// Public class
// ---------------------------------------------------------------------------

class PasswordChecker {
  /**
   * A plain JavaScript class that analyses password strength.
   *
   * Exposes strength scoring, labelling, common-password detection, and
   * input validation without depending on any HTTP framework.
   * Graftcode Gateway (`gg`) wraps this class at runtime and makes every
   * public method remotely callable via strongly-typed Grafts.
   */

  // ------------------------------------------------------------------
  // Input validation helper (private)
  // ------------------------------------------------------------------

  /**
   * Assert that `value` is a non-null string; throw otherwise.
   * @param {unknown} value
   * @param {string} [paramName]
   * @returns {string} The validated string
   */
  _assertString(value, paramName = "password") {
    if (typeof value !== "string") {
      throw new TypeError(
        `${paramName} must be a string, got ${value === null ? "null" : typeof value}`
      );
    }
    return value;
  }

  // ------------------------------------------------------------------
  // Public methods
  // ------------------------------------------------------------------

  /**
   * Perform a full password strength analysis.
   *
   * @param {string} password - The password to analyse.
   * @returns {{
   *   score: number,
   *   label: string,
   *   isCommon: boolean,
   *   criteria: {
   *     minLength: boolean,
   *     hasUppercase: boolean,
   *     hasLowercase: boolean,
   *     hasDigit: boolean,
   *     hasSpecial: boolean
   *   },
   *   feedback: string[]
   * }} Full analysis result.
   *
   * @throws {TypeError} If password is not a string.
   */
  checkStrength(password) {
    this._assertString(password);

    const criteria = {
      minLength: _hasMinLength(password),
      hasUppercase: _hasUppercase(password),
      hasLowercase: _hasLowercase(password),
      hasDigit: _hasDigit(password),
      hasSpecial: _hasSpecial(password),
    };

    const score = Object.values(criteria).filter(Boolean).length;
    const label = _scoreToLabel(score);
    const isCommon = this.isCommonPassword(password);

    /** @type {string[]} */
    const feedback = [];
    if (!criteria.minLength) feedback.push("Use at least 8 characters.");
    if (!criteria.hasUppercase) feedback.push("Add an uppercase letter.");
    if (!criteria.hasLowercase) feedback.push("Add a lowercase letter.");
    if (!criteria.hasDigit) feedback.push("Add a number.");
    if (!criteria.hasSpecial) feedback.push("Add a special character.");
    if (isCommon) feedback.push("Avoid commonly used passwords.");

    return { score, label, isCommon, criteria, feedback };
  }

  /**
   * Return a numeric strength score between 0 and 5 (inclusive).
   *
   * One point is awarded for each satisfied criterion:
   *   - length >= 8
   *   - contains an uppercase letter
   *   - contains a lowercase letter
   *   - contains a digit
   *   - contains a special character
   *
   * @param {string} password - The password to score.
   * @returns {number} Strength score 0–5.
   *
   * @throws {TypeError} If password is not a string.
   */
  getScore(password) {
    this._assertString(password);
    return [
      _hasMinLength(password),
      _hasUppercase(password),
      _hasLowercase(password),
      _hasDigit(password),
      _hasSpecial(password),
    ].filter(Boolean).length;
  }

  /**
   * Return a human-readable strength label for the password.
   *
   * | Score | Label        |
   * |-------|--------------|
   * | 0–1   | "Weak"       |
   * | 2     | "Fair"       |
   * | 3     | "Strong"     |
   * | 4–5   | "Very Strong"|
   *
   * @param {string} password - The password to label.
   * @returns {"Weak"|"Fair"|"Strong"|"Very Strong"} Strength label.
   *
   * @throws {TypeError} If password is not a string.
   */
  getLabel(password) {
    this._assertString(password);
    return _scoreToLabel(this.getScore(password));
  }

  /**
   * Check whether the password appears in the built-in common-password list.
   *
   * The comparison is case-insensitive.
   *
   * @param {string} password - The password to check.
   * @returns {boolean} True if the password is commonly used.
   *
   * @throws {TypeError} If password is not a string.
   */
  isCommonPassword(password) {
    this._assertString(password);
    return COMMON_PASSWORDS.has(password.toLowerCase());
  }

  /**
   * Validate the password and return a list of issues found.
   *
   * Unlike `checkStrength`, this method focuses only on what is *wrong*
   * with the password — it does not return a score or label.
   *
   * @param {string} password - The password to validate.
   * @returns {{
   *   isValid: boolean,
   *   issues: string[]
   * }} Validation result; `isValid` is true when `issues` is empty.
   *
   * @throws {TypeError} If password is not a string.
   */
  validate(password) {
    this._assertString(password);

    /** @type {string[]} */
    const issues = [];

    if (password.length === 0) {
      issues.push("Password must not be empty.");
      return { isValid: false, issues };
    }

    if (!_hasMinLength(password))
      issues.push("Password must be at least 8 characters long.");
    if (!_hasUppercase(password))
      issues.push("Password must contain at least one uppercase letter.");
    if (!_hasLowercase(password))
      issues.push("Password must contain at least one lowercase letter.");
    if (!_hasDigit(password))
      issues.push("Password must contain at least one digit.");
    if (!_hasSpecial(password))
      issues.push("Password must contain at least one special character.");
    if (this.isCommonPassword(password))
      issues.push("Password is too common. Please choose a more unique one.");

    return { isValid: issues.length === 0, issues };
  }
}

module.exports = { PasswordChecker };
