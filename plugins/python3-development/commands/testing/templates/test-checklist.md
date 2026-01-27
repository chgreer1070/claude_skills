# Test Review Checklist

```markdown
## Test Review Checklist

### Coverage
- [ ] New behavior has tests
- [ ] Negative/edge cases are tested
- [ ] Regression tests added for bug fixes

### Test Quality
- [ ] Tests assert user-visible behavior (not implementation details)
- [ ] Test names describe expected behavior (when/then)
- [ ] No brittle sleeps/time-based flakiness

### Fixtures and Mocks
- [ ] Fixtures are scoped appropriately
- [ ] Mocks are used only at boundaries (I/O, network, filesystem)
- [ ] Mocks assert important calls/arguments

### Determinism
- [ ] Tests are deterministic and order-independent
- [ ] Randomness is seeded or controlled

### Runtime
- [ ] Tests run fast enough for local iteration
- [ ] Slow tests are clearly marked or isolated
```
