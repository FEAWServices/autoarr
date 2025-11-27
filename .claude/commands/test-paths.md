Create a comprehensive test framework that validates the complete execution paths through this codebase. The tests should:

1. **Path-Based Testing**: For each major feature/flow, create tests that follow the complete execution path from entry point to completion, testing each function call in sequence.

2. **Contract Validation**: At each function boundary, verify:
   - Input parameters match what the caller provides (types, structure, required fields)
   - Output/return values match what downstream functions expect
   - Error responses are handled correctly by callers

3. **Integration Points**: Specifically test where:
   - Data is transformed between functions
   - External services are called (mock responses should match actual API contracts)
   - Configuration values are consumed
   - Async/promise chains connect

4. **Real-World Scenarios**: Create tests that simulate actual usage patterns:
   - Use realistic test data (not just happy path)
   - Include edge cases (empty values, nulls, undefined)
   - Test error paths and ensure errors propagate correctly

5. **Validation Strategy**:
   - Before writing tests, trace through the actual code paths
   - Log or assert intermediate values at each step
   - Verify the actual data structure being passed, not just that functions return
   - Test with data that closely resembles production scenarios

For the [specific feature/module], create tests that:

- Start from the user-facing entry point
- Follow the exact execution path through each layer
- Validate data transformations at each step
- Confirm that what function A outputs is exactly what function B expects as input

Do not assume interfaces work - prove they work by testing the actual data flow.
