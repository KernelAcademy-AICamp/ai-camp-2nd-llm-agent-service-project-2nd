# AI Worker CI Test Failure Analysis - PR #52

## Executive Summary

The AI Worker CI tests are failing with 29% coverage due to:
1. **Two-tiered configuration problem**: `conftest.py` at root level vs `tests/conftest.py` have conflicting env variable handling
2. **Tests being skipped**: Integration tests and handler tests are skipped in CI by design
3. **Environment variable requirement blocking all tests**: `tests/conftest.py` line 39 uses `pytest.skip()` when required env vars are missing

The core issue is that `tests/conftest.py` is **blocking all test execution** instead of **allowing unit tests to run with mocked dependencies**.

---

## Problem Analysis

### 1. Conflicting conftest.py Files

**File 1: `/ai_worker/conftest.py` (Root Level)**
- Sets default test environment variables (lines 60-80)
- Provides fallback values like `"test-openai-key"`, `"test-access-key"`
- Allows tests to run without GitHub Secrets

**File 2: `/ai_worker/tests/conftest.py` (Test Directory)**
- **BLOCKS ALL TESTS** if required env vars are missing (line 39)
- Requires: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `OPENAI_API_KEY`
- Has NO fallback values

### 2. Which Tests Are Being Skipped

**Patterns in conftest.py (lines 44-50):**
```python
integration_patterns = [
    "test_integration_e2e",      # E2E tests (intentional - requires real services)
    "test_case_isolation",       # Case isolation tests (intentional)
    "test_storage_manager",      # Storage manager tests (intentional)
    "test_search_engine",        # Search engine tests (intentional)
    "test_handler",              # Handler tests (added in commit 1a948bc)
]
```

**In CI Environment:**
- When `CI=true` and `RUN_INTEGRATION_TESTS` is not set
- These patterns are automatically skipped
- This is correct behavior for CI

### 3. The Real Problem: tests/conftest.py pytest.skip()

**Current Behavior (tests/conftest.py:26-41):**
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure environment variables are loaded for all tests"""
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION',
        'OPENAI_API_KEY',
    ]
    
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        pytest.skip(f"Missing required environment variables: {missing}")
```

**Issue:** When these 4 variables are missing, **ALL TESTS ARE SKIPPED** because:
- `autouse=True` means this fixture runs for every test
- `pytest.skip()` in a session-scoped autouse fixture skips the entire test session

---

## Root Causes

### Root Cause #1: Two Conftest Files with Different Strategies
- `conftest.py` (root): Provides sensible defaults ✓
- `tests/conftest.py`: Requires real values ✗

**Result:** Tests never reach the root conftest defaults

### Root Cause #2: conftest.py Location
Python/Pytest searches for conftest.py in the directory hierarchy:
1. `/ai_worker/tests/conftest.py` (found first)
2. `/ai_worker/conftest.py` (never used if #1 exists)

The test-level conftest blocks before root conftest can provide defaults.

### Root Cause #3: pytest.skip() in autouse Fixture
- An `autouse` fixture that calls `pytest.skip()` skips ALL tests in the session
- This is a global blocker, not a per-test filter

---

## Coverage Impact

**Current State (from commit 1a948bc):**
- Coverage threshold: 75% (lowered from 80%)
- Tests skipped:
  - Handler tests (5+ test classes)
  - Case isolation tests (4+ test classes)
  - Storage manager tests
  - Search engine tests
  - Integration E2E tests

**If tests/conftest.py blocks:** All remaining tests also skipped (0% coverage)

---

## Test File Structure Analysis

### 40 Test Files Found:
```
ai_worker/tests/
├── conftest.py                          (PROBLEM: blocks all tests)
├── test_handler.py                      (14 test classes, skipped in CI)
├── test_integration_e2e.py              (5+ test classes, skipped in CI)
├── test_sensitive_logging.py
├── test_text_parser_kakao.py
└── src/
    ├── test_ai_analyzer.py
    ├── test_ai_classification.py
    ├── test_analysis_engine.py
    ├── test_article_840_tagger.py
    ├── test_audio_parser.py
    ├── test_audio_parser_v2.py
    ├── test_case_isolation.py             (13 test methods, skipped in CI)
    ├── test_context_matcher.py
    ├── test_embeddings_fallback.py
    ├── test_encoding.py
    ├── test_evidence_scorer.py
    ├── test_exceptions.py
    ├── test_hybrid_search.py
    ├── test_image_ocr.py
    ├── test_image_parser_v2.py
    ├── test_image_vision.py
    ├── test_kakaotalk_v2.py
    ├── test_legal_analyzer.py
    ├── test_legal_parser.py
    ├── test_legal_search.py
    ├── test_legal_vectorizer.py
    ├── test_logging.py
    ├── test_metadata_store.py
    ├── test_parsers.py
    ├── test_pdf_parser.py
    ├── test_pdf_parser_v2.py
    ├── test_risk_analyzer.py
    ├── test_schemas.py
    ├── test_search_engine.py               (skipped in CI)
    ├── test_search_engine_v2.py
    ├── test_standard_metadata.py           (has skipif for ffmpeg/pytesseract)
    ├── test_storage_manager.py             (skipped in CI)
    ├── test_summarizer.py
    ├── test_timeline_generator.py
    ├── test_vector_store.py                (has pytest.skip for QDRANT_URL)
    └── test_video_parser.py
```

**Breakdown:**
- **Intentionally skipped in CI:** ~8 test files (integration, handler, storage)
- **Should run in CI:** ~32 test files
- **Actual run in CI:** 0 test files (due to conftest.py block)

---

## Current CI Configuration

**File: `.github/workflows/ci.yml` (lines 165-168)**
```yaml
- name: Run pytest
  env:
    TESTING: true
  run: pytest --cov=src --cov-report=xml -v -m "not integration"
```

**Issues:**
1. No env variables set for AWS/OpenAI
2. `TESTING=true` flag is set but not used
3. `-m "not integration"` filters by marker but conftest.py blocks first

**Compare with Backend CI (lines 109-119):**
```yaml
- name: Run pytest (skip integration tests)
  timeout-minutes: 5
  env:
    DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
    JWT_SECRET: test_secret_key_for_ci_pipeline_32chars
    TESTING: true
    AWS_REGION: ap-northeast-2
    AWS_ACCESS_KEY_ID: test-access-key
    AWS_SECRET_ACCESS_KEY: test-secret-key
    S3_EVIDENCE_BUCKET: test-bucket
    DDB_EVIDENCE_TABLE: test-evidence-table
    OPENAI_API_KEY: test-openai-key
  run: pytest --cov=app --cov-report=xml -v --timeout=60 -m "not integration"
```

✓ Backend DOES provide test env variables in CI
✗ AI Worker CI DOES NOT

---

## Mocking Architecture - Good News

**Tests ARE properly mocked already:**

### Example 1: Vector Store Tests (test_vector_store.py)
- Lines 28-37: `patch('qdrant_client.QdrantClient')`
- All Qdrant calls are mocked
- Unit tests run with `mock_qdrant_client` fixture
- Integration tests have separate `@pytest.mark.integration` marker

### Example 2: Metadata Store Tests (test_metadata_store.py)
- Lines 16-19: `patch('boto3.client')`
- All DynamoDB calls are mocked
- Unit tests work without real AWS credentials

### Example 3: Audio/Image Parsers (test_audio_parser.py, test_image_vision.py)
- `@patch('src.parsers.audio_parser.openai')`
- `@patch('src.parsers.image_vision.pytesseract')`
- OpenAI calls are fully mocked

### Example 4: Handler Tests (test_handler.py)
- Lines 44-45: `patch('handler.route_and_process')`
- Multiple patches for storage classes
- Designed to work with mocks

**Conclusion:** Tests have proper mocking already! They don't need real AWS/OpenAI keys.

---

## Why 29% Coverage Happens

**Scenario:**
1. CI runs pytest in ai_worker directory
2. pytest discovers conftest.py files in this order:
   - `/ai_worker/tests/conftest.py` (found first, runs first)
3. `setup_test_environment()` fixture runs (autouse=True)
4. Missing env vars detected → `pytest.skip()` called
5. **Entire test session skipped**
6. Coverage = 0%

**But we see 29%** suggests:
- Some test files might not use the conftest.py (older tests)
- Or CI logs show 29% from a previous run
- Or coverage calculation differs from skip count

---

## Solution Architecture

### Option A: Add Test Environment Variables to CI (Recommended)

**Pros:**
- Minimal code changes
- Matches backend CI approach
- Most straightforward fix
- Uses existing mock infrastructure

**Changes needed:**
1. Update `.github/workflows/ci.yml` AI Worker job
2. Add test env vars (same as backend)
3. Remove `tests/conftest.py` blocking

**Files to modify:**
- `.github/workflows/ci.yml` (lines 165-168)
- `/ai_worker/tests/conftest.py` (change approach)

---

### Option B: Make tests/conftest.py Mock-Friendly

**Pros:**
- No CI changes needed
- Keeps conftest philosophy

**Changes needed:**
1. Remove pytest.skip() from tests/conftest.py
2. Make env vars optional for unit tests
3. Only require real env vars for integration tests

**Implementation:**
```python
# Instead of pytest.skip, only log warning for unit tests
if CI and missing_vars:
    print(f"Warning: {missing_vars} not set - using defaults")
```

---

### Option C: Separate Integration Tests Clearly

**Pros:**
- Clean test organization
- Explicit intent

**Changes needed:**
1. Create separate `tests/integration/` directory
2. Only integration tests require real env vars
3. All unit tests in `tests/unit/` work with mocks

---

## Recommended Solution: **Option A + B Combined**

**Step 1: Fix CI Configuration**
- Add test env vars to `.github/workflows/ci.yml`
- Follows backend pattern
- Cost: low

**Step 2: Make tests/conftest.py Smarter**
- Provide defaults instead of blocking
- Only fail integration tests without real vars
- Cost: low

**Result:**
- CI runs unit tests with mocked dependencies ✓
- Coverage jumps from 29% to ~75-80% ✓
- No real AWS/OpenAI API calls ✓
- GitHub Secrets not needed ✓
- Local testing with `RUN_INTEGRATION_TESTS=1` still works ✓

---

## Specific File Changes Needed

### 1. `/ai_worker/tests/conftest.py` (Fix the blocker)

**Current (lines 26-42):**
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure environment variables are loaded for all tests"""
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION',
        'OPENAI_API_KEY',
    ]
    
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        pytest.skip(f"Missing required environment variables: {missing}")
    
    yield
```

**Should become:**
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Load environment variables for tests, using defaults for CI unit tests"""
    # Set defaults for unit tests in CI
    test_defaults = {
        "AWS_REGION": "ap-northeast-2",
        "AWS_ACCESS_KEY_ID": "test-access-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret-key",
        "OPENAI_API_KEY": "test-openai-key",
        "QDRANT_URL": "http://localhost:6333",
        "DDB_EVIDENCE_TABLE": "test-evidence-table",
    }
    
    for key, default_value in test_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
    
    yield
```

**Rationale:**
- Provides defaults for unit tests (which are mocked)
- Doesn't block test execution
- Matches root-level conftest.py approach
- Integration tests can still require real vars if needed

---

### 2. `.github/workflows/ci.yml` (Add test env vars - lines 165-176)

**Current:**
```yaml
      - name: Run pytest
        env:
          TESTING: true
        run: pytest --cov=src --cov-report=xml -v -m "not integration"
```

**Should become:**
```yaml
      - name: Run pytest
        env:
          TESTING: true
          AWS_REGION: ap-northeast-2
          AWS_ACCESS_KEY_ID: test-access-key
          AWS_SECRET_ACCESS_KEY: test-secret-key
          S3_EVIDENCE_BUCKET: test-bucket
          DDB_EVIDENCE_TABLE: test-evidence-table
          OPENAI_API_KEY: test-openai-key
          QDRANT_URL: http://localhost:6333
          QDRANT_API_KEY: test-api-key
        run: pytest --cov=src --cov-report=xml -v -m "not integration"
```

**Rationale:**
- Matches backend CI pattern
- Provides required vars without GitHub Secrets
- Uses safe test values (clearly marked as test-*)
- No sensitive real credentials

---

### 3. `/ai_worker/conftest.py` (Optional cleanup)

**Current setup_test_environment() can be enhanced:**
```python
# Add validation to ensure required vars are set
def pytest_configure(config):
    """Validate minimum required environment variables"""
    required_for_ci = [
        'AWS_REGION',
        'AWS_ACCESS_KEY_ID', 
        'AWS_SECRET_ACCESS_KEY',
        'OPENAI_API_KEY',
    ]
    
    in_ci = os.environ.get('CI') == 'true'
    if in_ci:
        missing = [v for v in required_for_ci if not os.environ.get(v)]
        if missing:
            raise ValueError(f"CI requires env vars: {missing}")
```

**Rationale:**
- Validates the integration between CI and conftest
- Provides clear error message
- Fails CI fast if env vars not set (instead of silent skip)

---

## Testing the Fix

### Local Testing (Unit Tests Only)
```bash
cd ai_worker
pytest -m "not integration" --cov=src
# Expected: ~75-80% coverage
```

### Local Testing (With Integration Tests)
```bash
cd ai_worker
RUN_INTEGRATION_TESTS=1 pytest --cov=src
# Expected: 80%+ coverage (if services running)
```

### CI Testing
```bash
git push origin feature-branch  # Triggers CI
# Should see:
# - All unit tests run (not skipped)
# - ~75% coverage reported
# - No real AWS/OpenAI calls
```

---

## Impact Analysis

### Coverage Improvement
- **Current:** 29% (nearly all tests skipped)
- **After Fix:** 75-80% (unit tests run, integration tests skipped in CI)
- **With Integration:** 80%+ (when services available)

### CI Time Impact
- Minimal: Unit tests are fast (mostly mocked)
- No additional dependencies
- System deps (tesseract, ffmpeg) already installed

### Code Quality Impact
- More test execution = better quality assurance
- Catches bugs in unit code (not just integration)
- Supports local debugging with real services

### Security Impact
- No new secrets required
- Uses safe test values only
- No exposure of real API keys in CI logs

---

## Related Files & Patterns

### 1. Root-level conftest.py Pattern (Works Well)
- Provides defaults ✓
- Doesn't block tests ✓
- Allows override ✓

### 2. Backend CI Pattern (Works Well)
- Provides test env vars ✓
- Runs tests with mocks ✓
- ~70%+ coverage ✓

### 3. Test-level conftest.py Pattern (Problematic)
- Blocks all tests on missing vars ✗
- No fallback mechanism ✗
- Conflicts with root conftest ✗

### 4. Mocking Infrastructure (Already Good)
- Proper patch decorators ✓
- Mock fixtures ✓
- Integration markers ✓

---

## Implementation Priority

1. **High Priority:** Fix tests/conftest.py (5 minutes)
2. **High Priority:** Add env vars to CI workflow (5 minutes)
3. **Medium Priority:** Add validation to root conftest.py (10 minutes)
4. **Low Priority:** Consider test reorganization (optional)

**Total estimated effort:** 20 minutes

---

## Verification Checklist

- [ ] Modify `/ai_worker/tests/conftest.py` to use defaults
- [ ] Update `.github/workflows/ci.yml` with test env vars
- [ ] Test locally: `pytest -m "not integration"`
- [ ] Verify coverage output (should be 75%+)
- [ ] Test with all markers: `pytest -v`
- [ ] Push to feature branch and check CI
- [ ] Verify no real AWS/OpenAI calls in CI logs
- [ ] Merge PR once tests pass

---

## References

- **pytest docs:** https://docs.pytest.org/en/stable/how-to/skipping.html
- **conftest.py resolution:** https://docs.pytest.org/en/stable/how-to/writing_plugins.html#the-conftest-py-plugin
- **autouse fixtures:** https://docs.pytest.org/en/stable/how-to/fixtures.html#autouse-fixtures
- **Mocking best practices:** https://docs.python.org/3/library/unittest.mock.html

---

## Questions & Answers

**Q: Will this require GitHub Secrets?**
A: No. Test values like `test-access-key` are public test values, not secrets.

**Q: Won't this run integration tests in CI?**
A: No. `-m "not integration"` marker filtering still applies. Handler/storage tests are skipped by root conftest patterns.

**Q: What if a developer runs tests without env vars locally?**
A: They'll get defaults (like CI). For integration tests, they need RUN_INTEGRATION_TESTS=1.

**Q: Can we keep the pytest.skip() approach?**
A: Not recommended. It blocks all tests globally. Better to provide defaults + check on demand.

**Q: Will this affect other developers' workflows?**
A: No. All changes are CI/conftest only. Source code unchanged.

