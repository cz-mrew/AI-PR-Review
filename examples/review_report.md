# AI Review Report

## PR Summary

**PR:** `https://github.com/example/shop-api/pull/123`

**Title:** Add coupon validation to checkout flow

**Author:** `octocat`

**Base Branch:** `main`

**Head Branch:** `feature/coupon-validation`

This pull request adds coupon validation to the checkout API. It introduces a new coupon service, updates the checkout endpoint to apply discounts, and adds unit tests for valid, expired, and unsupported coupon codes.

## Change Statistics

| Metric | Value |
| --- | ---: |
| Files changed | 6 |
| Additions | 214 |
| Deletions | 38 |
| Commits | 3 |
| Tests added | 5 |

Changed files:

- `src/checkout/routes.py`
- `src/checkout/service.py`
- `src/coupons/service.py`
- `src/coupons/models.py`
- `tests/test_checkout_coupons.py`
- `tests/test_coupon_service.py`

## AI Summary

The PR cleanly separates coupon lookup and validation into a dedicated service, then integrates the result into the checkout calculation path. The implementation covers the expected success path and several common invalid coupon cases.

The main behavior change is that checkout totals can now be reduced by a fixed or percentage discount when a valid coupon code is supplied. Invalid or expired coupons are rejected before payment calculation.

Overall risk is **medium** because checkout and pricing logic are customer-facing and financially sensitive.

## Risk Areas

### Pricing Logic

The discount calculation changes the final order total. Edge cases around rounding, minimum payable amount, and stacked discounts should be reviewed carefully.

### Validation Flow

Coupon validation now occurs before payment authorization. If validation service errors are not handled consistently, valid checkouts may fail unexpectedly.

### Backward Compatibility

The checkout request now accepts an optional `coupon_code` field. Existing clients should continue to work because the field is optional.

### Observability

Rejected coupons are currently returned as API errors, but there is no clear logging or metric for coupon rejection reasons.

## Review Suggestions

- Add an explicit guard to prevent discounted totals from going below zero.
- Confirm whether percentage discounts should round up, round down, or use banker's rounding.
- Add structured logs for rejected coupons with reason codes such as `expired`, `not_found`, and `not_applicable`.
- Consider moving coupon error responses into a small typed error object so API consumers can distinguish user mistakes from service failures.
- Verify that coupon validation does not introduce an extra database query per item in the cart.

## Test Suggestions

- Add a test for a coupon that would reduce the total below zero.
- Add a test for percentage discount rounding behavior.
- Add a test for checkout without `coupon_code` to lock in backward compatibility.
- Add a test for an expired coupon on an otherwise valid cart.
- Add a test for coupon service failure to confirm checkout returns a controlled error.
- Add an integration test for a full checkout request with a valid coupon and payment authorization mocked.
