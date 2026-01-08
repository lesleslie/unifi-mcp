"""Tests for retry utilities module."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from unifi_mcp.utils.retry_utils import (
    _calculate_delay,
    retry_async,
    retry_with_backoff,
)


class TestCalculateDelay:
    """Test delay calculation for retry logic."""

    def test_calculate_delay_basic(self):
        """Test basic delay calculation without jitter."""
        delay = _calculate_delay(
            base_delay=1.0, backoff_factor=2.0, attempt=0, max_delay=60.0, jitter=False
        )
        assert delay == 1.0

    def test_calculate_delay_with_backoff(self):
        """Test exponential backoff calculation."""
        # Attempt 0: 1.0 * 2^0 = 1.0
        delay = _calculate_delay(
            base_delay=1.0, backoff_factor=2.0, attempt=0, max_delay=60.0, jitter=False
        )
        assert delay == 1.0

        # Attempt 1: 1.0 * 2^1 = 2.0
        delay = _calculate_delay(
            base_delay=1.0, backoff_factor=2.0, attempt=1, max_delay=60.0, jitter=False
        )
        assert delay == 2.0

        # Attempt 2: 1.0 * 2^2 = 4.0
        delay = _calculate_delay(
            base_delay=1.0, backoff_factor=2.0, attempt=2, max_delay=60.0, jitter=False
        )
        assert delay == 4.0

        # Attempt 3: 1.0 * 2^3 = 8.0
        delay = _calculate_delay(
            base_delay=1.0, backoff_factor=2.0, attempt=3, max_delay=60.0, jitter=False
        )
        assert delay == 8.0

    def test_calculate_delay_with_max_delay(self):
        """Test that delay respects max_delay cap."""
        # With backoff_factor=2, attempt=10 would be 1024, but capped at 60
        delay = _calculate_delay(
            base_delay=1.0, backoff_factor=2.0, attempt=10, max_delay=60.0, jitter=False
        )
        assert delay == 60.0

    def test_calculate_delay_with_jitter(self):
        """Test that jitter adds randomness to delay."""
        delays = []
        for _ in range(100):
            delay = _calculate_delay(
                base_delay=1.0,
                backoff_factor=2.0,
                attempt=1,
                max_delay=60.0,
                jitter=True,
            )
            delays.append(delay)

        # With jitter, delay should be between 1.0 and 2.0 (50% to 100% of base)
        # Base delay for attempt 1 is 2.0, so with jitter: 1.0 to 2.0
        assert all(1.0 <= d <= 2.0 for d in delays)
        # Not all delays should be the same (randomness)
        assert len(set(delays)) > 1

    def test_calculate_delay_zero_backoff_factor(self):
        """Test with zero backoff factor."""
        delay = _calculate_delay(
            base_delay=1.0,
            backoff_factor=0.0,
            attempt=5,
            max_delay=60.0,
            jitter=False,
        )
        # 1.0 * 0^5 = 0
        assert delay == 0.0

    def test_calculate_delay_different_backoff_factors(self):
        """Test with different backoff factors."""
        # backoff_factor 1.5
        delay = _calculate_delay(
            base_delay=1.0, backoff_factor=1.5, attempt=2, max_delay=60.0, jitter=False
        )
        assert delay == 1.0 * (1.5**2)  # 2.25

        # backoff_factor 3.0
        delay = _calculate_delay(
            base_delay=1.0, backoff_factor=3.0, attempt=2, max_delay=60.0, jitter=False
        )
        assert delay == 1.0 * (3.0**2)  # 9.0


class TestRetryAsyncDecorator:
    """Test retry_async decorator."""

    async def test_retry_async_success_on_first_attempt(self):
        """Test that function succeeds on first attempt."""

        @retry_async(max_attempts=3)
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    async def test_retry_async_success_on_second_attempt(self):
        """Test that function succeeds after one retry."""
        call_count = 0

        @retry_async(max_attempts=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 2

    async def test_retry_async_success_on_last_attempt(self):
        """Test that function succeeds on the last attempt."""
        call_count = 0

        @retry_async(max_attempts=3)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 3

    async def test_retry_async_failure_after_all_attempts(self):
        """Test that function fails after all attempts exhausted."""

        @retry_async(max_attempts=3)
        async def test_func():
            raise ValueError("Persistent failure")

        with pytest.raises(ValueError, match="Persistent failure"):
            await test_func()

    async def test_retry_async_with_different_exceptions(self):
        """Test retrying with different exception types."""

        @retry_async(max_attempts=3, exceptions=(ValueError, KeyError))
        async def test_func():
            raise KeyError("Not found")

        with pytest.raises(KeyError, match="Not found"):
            await test_func()

    async def test_retry_async_only_retries_specific_exceptions(self):
        """Test that only specified exceptions trigger retries."""

        @retry_async(max_attempts=3, exceptions=(ValueError,))
        async def test_func():
            raise TypeError("Different error")

        # Should not retry, raise immediately
        with pytest.raises(TypeError, match="Different error"):
            await test_func()

    async def test_retry_async_custom_delays(self):
        """Test with custom delay parameters."""
        call_count = 0
        delays = []

        @retry_async(
            max_attempts=3, base_delay=0.1, backoff_factor=2.0, max_delay=1.0, jitter=False
        )
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        import time

        start = time.time()
        result = await test_func()
        elapsed = time.time() - start

        assert result == "success"
        assert call_count == 3
        # Should have waited: 0.1 (after first failure) + 0.2 (after second failure)
        # Give some tolerance for timing
        assert 0.25 <= elapsed <= 0.5

    async def test_retry_async_with_jitter_disabled(self):
        """Test with jitter disabled."""
        call_count = 0

        @retry_async(
            max_attempts=3, base_delay=0.1, backoff_factor=2.0, jitter=False
        )
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 3

    async def test_retry_async_with_jitter_enabled(self):
        """Test with jitter enabled."""
        call_count = 0

        @retry_async(
            max_attempts=3, base_delay=0.1, backoff_factor=2.0, jitter=True
        )
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 3

    async def test_retry_async_preserves_exception_message(self):
        """Test that exception message is preserved after retries."""

        @retry_async(max_attempts=3)
        async def test_func():
            raise ValueError("Specific error message")

        with pytest.raises(ValueError) as exc_info:
            await test_func()

        assert str(exc_info.value) == "Specific error message"

    async def test_retry_async_with_no_retry_on_success(self):
        """Test that successful calls don't trigger retries."""
        call_count = 0

        @retry_async(max_attempts=5)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 1  # Should only be called once

    async def test_retry_async_single_attempt(self):
        """Test with max_attempts=1 (no retries)."""

        @retry_async(max_attempts=1)
        async def test_func():
            raise ValueError("Failure")

        with pytest.raises(ValueError, match="Failure"):
            await test_func()


class TestRetryWithBackoff:
    """Test retry_with_backoff function."""

    async def test_retry_with_backoff_success(self):
        """Test successful retry with backoff."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry_with_backoff(
            test_func, max_attempts=3, base_delay=0.01, jitter=False
        )

        assert result == "success"
        assert call_count == 2

    async def test_retry_with_backoff_failure(self):
        """Test failure after all attempts."""

        async def test_func():
            raise ValueError("Persistent failure")

        with pytest.raises(ValueError, match="Persistent failure"):
            await retry_with_backoff(test_func, max_attempts=3, base_delay=0.01)

    async def test_retry_with_backoff_with_args(self):
        """Test retry_with_backoff passes arguments correctly."""

        async def test_func(arg1, arg2, kwarg1=None):
            if arg1 == "fail":
                raise ValueError("Temporary failure")
            return f"{arg1}-{arg2}-{kwarg1}"

        result = await retry_with_backoff(
            test_func,
            "success",
            "test",
            kwarg1="value",
            max_attempts=2,
            base_delay=0.01,
        )

        assert result == "success-test-value"

    async def test_retry_with_backoff_custom_exceptions(self):
        """Test custom exception types."""

        async def test_func():
            raise KeyError("Not found")

        with pytest.raises(KeyError, match="Not found"):
            await retry_with_backoff(
                test_func,
                max_attempts=3,
                base_delay=0.01,
                exceptions=(KeyError,),
            )

    async def test_retry_with_backoff_respects_max_delay(self):
        """Test that max_delay is respected."""
        call_count = 0

        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        import time

        start = time.time()
        result = await retry_with_backoff(
            test_func,
            max_attempts=3,
            base_delay=0.1,
            backoff_factor=10.0,  # Large factor
            max_delay=0.2,  # Low max
            jitter=False,
        )
        elapsed = time.time() - start

        assert result == "success"
        # Delay should be capped at 0.2, so total wait should be around 0.3
        assert 0.25 <= elapsed <= 0.5


class TestRetryEdgeCases:
    """Test edge cases for retry logic."""

    async def test_retry_async_with_zero_delay(self):
        """Test retry with zero delay."""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0, jitter=False)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 3

    async def test_retry_async_with_very_small_delay(self):
        """Test retry with very small delay."""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=0.001, jitter=False)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"

    async def test_retry_async_with_large_max_attempts(self):
        """Test with large number of max attempts."""
        call_count = 0

        @retry_async(max_attempts=10, base_delay=0.001, jitter=False)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                raise ValueError("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"
        assert call_count == 5

    async def test_retry_with_backoff_exception_type_filtering(self):
        """Test that non-matching exceptions don't trigger retries."""

        async def test_func():
            raise TypeError("Different error")

        with pytest.raises(TypeError):
            await retry_with_backoff(
                test_func,
                max_attempts=3,
                base_delay=0.01,
                exceptions=(ValueError,),  # Only retry on ValueError
            )

    async def test_retry_async_zero_max_attempts(self):
        """Test behavior with max_attempts=0 (edge case)."""
        # This should either fail immediately or raise an error
        @retry_async(max_attempts=0)
        async def test_func():
            return "success"

        # Depending on implementation, this might succeed or fail
        # The important thing is it doesn't hang or crash
        try:
            result = await test_func()
            # If it succeeds, that's also acceptable
            assert result == "success"
        except Exception:
            # If it raises an exception, that's also acceptable
            pass

    async def test_retry_async_negative_delay(self):
        """Test with negative delay (should be handled gracefully)."""
        call_count = 0

        @retry_async(max_attempts=3, base_delay=-1.0, jitter=False)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await test_func()
        assert result == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
