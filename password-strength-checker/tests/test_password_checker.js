"use strict";

/**
 * Comprehensive unit tests for PasswordChecker.
 *
 * Design constraints (per AGENTS.md):
 *   - node:test only (Node 20+ built-in) — zero npm test dependencies
 *   - Fully offline — no network calls, no Docker dependency
 *   - Fast — pure in-memory operations
 *
 * Run with:
 *   node --test tests/test_password_checker.js
 *   npm test
 */

const { describe, it, before } = require("node:test");
const assert = require("node:assert/strict");
const { PasswordChecker } = require("../password_checker/checker");

// ---------------------------------------------------------------------------
// Shared fixtures
// ---------------------------------------------------------------------------

/** @type {PasswordChecker} */
let checker;

before(() => {
  checker = new PasswordChecker();
});

// ---------------------------------------------------------------------------
// checkStrength
// ---------------------------------------------------------------------------

describe("checkStrength", () => {
  it("throws TypeError for null input", () => {
    assert.throws(() => checker.checkStrength(null), TypeError);
  });

  it("throws TypeError for undefined input", () => {
    assert.throws(() => checker.checkStrength(undefined), TypeError);
  });

  it("throws TypeError for numeric input", () => {
    assert.throws(() => checker.checkStrength(42), TypeError);
  });

  it("returns score 0 and label Weak for empty string", () => {
    const result = checker.checkStrength("");
    assert.equal(result.score, 0);
    assert.equal(result.label, "Weak");
  });

  it("returns Weak for a single lowercase letter", () => {
    const result = checker.checkStrength("a");
    assert.equal(result.label, "Weak");
    assert.equal(result.score, 1); // only hasLowercase
  });

  it("returns Weak for all-digit short password", () => {
    const result = checker.checkStrength("1234");
    assert.equal(result.label, "Weak");
  });

  it("returns Fair for password meeting 2 criteria", () => {
    // lowercase + digit, length < 8
    const result = checker.checkStrength("abc1");
    assert.equal(result.label, "Fair");
    assert.equal(result.score, 2);
  });

  it("returns Strong for password meeting 3 criteria", () => {
    // lowercase + uppercase + digit, length < 8
    const result = checker.checkStrength("Abc123");
    assert.equal(result.label, "Strong");
    assert.equal(result.score, 3);
  });

  it("returns Very Strong for password meeting all 5 criteria", () => {
    const result = checker.checkStrength("P@ssw0rd!");
    assert.equal(result.label, "Very Strong");
    assert.equal(result.score, 5);
  });

  it("marks a known common password in result", () => {
    const result = checker.checkStrength("password");
    assert.equal(result.isCommon, true);
    assert.ok(result.feedback.some((f) => f.includes("common")));
  });

  it("sets isCommon false for a unique strong password", () => {
    const result = checker.checkStrength("Xk9#mP2@wQr!");
    assert.equal(result.isCommon, false);
  });

  it("returns all 5 criteria as booleans", () => {
    const result = checker.checkStrength("P@ssw0rd!");
    const { criteria } = result;
    assert.equal(typeof criteria.minLength, "boolean");
    assert.equal(typeof criteria.hasUppercase, "boolean");
    assert.equal(typeof criteria.hasLowercase, "boolean");
    assert.equal(typeof criteria.hasDigit, "boolean");
    assert.equal(typeof criteria.hasSpecial, "boolean");
  });

  it("provides feedback array when criteria are unmet", () => {
    const result = checker.checkStrength("abc");
    assert.ok(Array.isArray(result.feedback));
    assert.ok(result.feedback.length > 0);
  });

  it("returns empty feedback for a perfect password", () => {
    const result = checker.checkStrength("Xk9#mP2@wQr!");
    // Only feedback allowed would be isCommon — which is false
    const nonCommonFeedback = result.feedback.filter(
      (f) => !f.includes("common")
    );
    assert.equal(nonCommonFeedback.length, 0);
  });
});

// ---------------------------------------------------------------------------
// getScore
// ---------------------------------------------------------------------------

describe("getScore", () => {
  it("throws TypeError for null", () => {
    assert.throws(() => checker.getScore(null), TypeError);
  });

  it("returns 0 for empty string", () => {
    assert.equal(checker.getScore(""), 0);
  });

  it("returns 1 for lowercase-only short password", () => {
    assert.equal(checker.getScore("abc"), 1);
  });

  it("returns 2 for lowercase + digit (short)", () => {
    assert.equal(checker.getScore("abc1"), 2);
  });

  it("returns 3 for lowercase + uppercase + digit", () => {
    assert.equal(checker.getScore("Abc123"), 3);
  });

  it("returns 4 for lowercase + uppercase + digit + minLength", () => {
    assert.equal(checker.getScore("Abcdefg1"), 4);
  });

  it("returns 5 for all criteria met", () => {
    assert.equal(checker.getScore("P@ssw0rd!"), 5);
  });

  it("score is always between 0 and 5", () => {
    const passwords = ["", "a", "abc123", "P@ssw0rd!", "Xk9#mP2@wQr!!!!"];
    for (const pw of passwords) {
      const s = checker.getScore(pw);
      assert.ok(s >= 0 && s <= 5, `Score ${s} out of range for "${pw}"`);
    }
  });
});

// ---------------------------------------------------------------------------
// getLabel
// ---------------------------------------------------------------------------

describe("getLabel", () => {
  it("throws TypeError for null", () => {
    assert.throws(() => checker.getLabel(null), TypeError);
  });

  it('returns "Weak" for score 0 (empty)', () => {
    assert.equal(checker.getLabel(""), "Weak");
  });

  it('returns "Weak" for score 1', () => {
    assert.equal(checker.getLabel("abc"), "Weak");
  });

  it('returns "Fair" for score 2', () => {
    assert.equal(checker.getLabel("abc1"), "Fair");
  });

  it('returns "Strong" for score 3', () => {
    assert.equal(checker.getLabel("Abc123"), "Strong");
  });

  it('returns "Very Strong" for score 4', () => {
    assert.equal(checker.getLabel("Abcdefg1"), "Very Strong");
  });

  it('returns "Very Strong" for score 5', () => {
    assert.equal(checker.getLabel("P@ssw0rd!"), "Very Strong");
  });

  it("label is always one of the four valid values", () => {
    const valid = new Set(["Weak", "Fair", "Strong", "Very Strong"]);
    const passwords = ["", "abc", "abc1", "Abc1", "Abc1234", "P@ssw0rd!"];
    for (const pw of passwords) {
      assert.ok(valid.has(checker.getLabel(pw)), `Unexpected label for "${pw}"`);
    }
  });
});

// ---------------------------------------------------------------------------
// isCommonPassword
// ---------------------------------------------------------------------------

describe("isCommonPassword", () => {
  it("throws TypeError for null", () => {
    assert.throws(() => checker.isCommonPassword(null), TypeError);
  });

  it('returns true for "password"', () => {
    assert.equal(checker.isCommonPassword("password"), true);
  });

  it('returns true for "123456"', () => {
    assert.equal(checker.isCommonPassword("123456"), true);
  });

  it('returns true for "qwerty"', () => {
    assert.equal(checker.isCommonPassword("qwerty"), true);
  });

  it('returns true for "admin"', () => {
    assert.equal(checker.isCommonPassword("admin"), true);
  });

  it("is case-insensitive (PASSWORD → true)", () => {
    assert.equal(checker.isCommonPassword("PASSWORD"), true);
  });

  it("is case-insensitive (Admin → true)", () => {
    assert.equal(checker.isCommonPassword("Admin"), true);
  });

  it("returns false for a unique strong password", () => {
    assert.equal(checker.isCommonPassword("Xk9#mP2@wQr!"), false);
  });

  it("returns false for an empty string", () => {
    assert.equal(checker.isCommonPassword(""), false);
  });
});

// ---------------------------------------------------------------------------
// validate
// ---------------------------------------------------------------------------

describe("validate", () => {
  it("throws TypeError for null", () => {
    assert.throws(() => checker.validate(null), TypeError);
  });

  it("throws TypeError for a number", () => {
    assert.throws(() => checker.validate(99), TypeError);
  });

  it("returns isValid false with one issue for empty password", () => {
    const { isValid, issues } = checker.validate("");
    assert.equal(isValid, false);
    assert.ok(issues.length > 0);
  });

  it("returns isValid false with issue for missing uppercase", () => {
    const { isValid, issues } = checker.validate("abcdefg1!");
    assert.equal(isValid, false);
    assert.ok(issues.some((i) => i.includes("uppercase")));
  });

  it("returns isValid false with issue for missing digit", () => {
    const { isValid, issues } = checker.validate("Abcdefg!");
    assert.equal(isValid, false);
    assert.ok(issues.some((i) => i.includes("digit")));
  });

  it("returns isValid false with issue for missing special character", () => {
    const { isValid, issues } = checker.validate("Abcdefg1");
    assert.equal(isValid, false);
    assert.ok(issues.some((i) => i.includes("special")));
  });

  it("returns isValid false for too-short password", () => {
    const { isValid, issues } = checker.validate("Ab1!");
    assert.equal(isValid, false);
    assert.ok(issues.some((i) => i.includes("8 characters")));
  });

  it("returns isValid false for a common password", () => {
    // 'password' fails multiple criteria AND is common
    const { isValid } = checker.validate("password");
    assert.equal(isValid, false);
  });

  it("returns isValid true for a strong unique password", () => {
    const { isValid, issues } = checker.validate("Xk9#mP2@wQr!");
    assert.equal(isValid, true);
    assert.equal(issues.length, 0);
  });

  it("issues is always an array", () => {
    assert.ok(Array.isArray(checker.validate("P@ssw0rd!").issues));
    assert.ok(Array.isArray(checker.validate("weak").issues));
  });
});

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

describe("Edge cases", () => {
  it("handles a whitespace-only password without throwing", () => {
    assert.doesNotThrow(() => checker.checkStrength("        "));
  });

  it("whitespace-only 8-char password satisfies minLength only (score 1)", () => {
    // 8 spaces: only minLength is true
    assert.equal(checker.getScore("        "), 1);
  });

  it("handles a very long password (1000 chars) without throwing", () => {
    const long = "aA1!".repeat(250); // 1000 chars, all criteria met
    assert.doesNotThrow(() => checker.checkStrength(long));
    assert.equal(checker.getScore(long), 5);
  });

  it("handles a password with only special characters", () => {
    // only hasSpecial criterion satisfied
    const result = checker.checkStrength("!@#");
    assert.equal(result.criteria.hasSpecial, true);
    assert.equal(result.criteria.hasDigit, false);
    assert.equal(result.criteria.hasUppercase, false);
  });

  it("each new PasswordChecker instance is independent", () => {
    const a = new PasswordChecker();
    const b = new PasswordChecker();
    assert.equal(a.getScore("P@ssw0rd!"), b.getScore("P@ssw0rd!"));
  });
});
