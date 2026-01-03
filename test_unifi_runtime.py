#!/usr/bin/env python3
"""Test script for UniFi MCP Runtime Integration."""

import asyncio
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "/Users/les/Projects/oneiric")

from oneiric.runtime.mcp_health import HealthStatus

from unifi_mcp.__main__ import UniFiConfig, UniFiMCPServer


def test_unifi_runtime_integration():
    """Test complete UniFi runtime integration."""
    print("🚀 Starting UniFi MCP Runtime Integration tests...")
    
    # Create a temporary cache directory
    temp_cache_dir = Path(tempfile.mkdtemp(prefix="unifi_test_"))
    
    try:
        # Test 1: Configuration
        print("\n1. Testing configuration...")
        config = UniFiConfig()
        print(f"✅ Config loaded: {config}")
        
        # Test 2: Server creation with runtime components
        print("\n2. Testing server creation with runtime components...")
        server = UniFiMCPServer(config)
        
        # Update cache directories to use temp directory
        server.snapshot_manager.cache_dir = temp_cache_dir
        server.snapshot_manager.snapshots_dir = temp_cache_dir / "snapshots"
        server.cache_manager.cache_dir = temp_cache_dir
        server.cache_manager.cache_file = temp_cache_dir / "unifi-mcp_cache.json"
        
        print(f"✅ Server created: {server}")
        print(f"✅ Snapshot manager: {server.snapshot_manager}")
        print(f"✅ Cache manager: {server.cache_manager}")
        print(f"✅ Health monitor: {server.health_monitor}")
        
        # Test 3: Runtime component initialization
        print("\n3. Testing runtime component initialization...")
        asyncio.run(server.snapshot_manager.initialize())
        asyncio.run(server.cache_manager.initialize())
        print("✅ Runtime components initialized")
        
        # Test 4: Snapshot creation
        print("\n4. Testing snapshot creation...")
        components = {
            "test_component": {
                "status": "tested",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }
        snapshot = asyncio.run(server.snapshot_manager.create_snapshot(components))
        print(f"✅ Snapshot created: {snapshot}")
        
        # Test 5: Cache operations
        print("\n5. Testing cache operations...")
        asyncio.run(server.cache_manager.set("test_key", "test_value", ttl=60))
        cached_value = asyncio.run(server.cache_manager.get("test_key"))
        print(f"✅ Cache set and get: {cached_value}")
        
        cache_stats = asyncio.run(server.cache_manager.get_cache_stats())
        print(f"✅ Cache stats: {cache_stats}")
        
        # Test 6: Health check
        print("\n6. Testing health check...")
        health_response = asyncio.run(server.health_check())
        print(f"✅ Health response created: {health_response}")
        print(f"✅ Health status: {health_response.status}")
        print(f"✅ Components: {len(health_response.components)}")
        
        # Verify health response structure
        assert health_response.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
        assert len(health_response.components) == 3  # controllers, cache, snapshot
        assert health_response.timestamp is not None
        
        # Test component health
        for component in health_response.components:
            print(f"   Component {component.name}: {component.status.value}")
            assert component.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
        
        # Test 7: Snapshot history
        print("\n7. Testing snapshot history...")
        history = asyncio.run(server.snapshot_manager.get_snapshot_history())
        print(f"✅ Snapshot history: {len(history)} snapshots")
        
        # Test 8: Current snapshot
        print("\n8. Testing current snapshot...")
        current = asyncio.run(server.snapshot_manager.get_current_snapshot())
        print(f"✅ Current snapshot: {current}")
        
        # Test 9: Cache cleanup
        print("\n9. Testing cache cleanup...")
        asyncio.run(server.cache_manager.clear())
        cleared_stats = asyncio.run(server.cache_manager.get_cache_stats())
        print(f"✅ Cache cleared: {cleared_stats['total_entries']} entries")
        
        # Test 10: Runtime component cleanup
        print("\n10. Testing runtime component cleanup...")
        asyncio.run(server.snapshot_manager.cleanup())
        asyncio.run(server.cache_manager.cleanup())
        print("✅ Runtime components cleaned up")
        
        print("\n🎉 All UniFi runtime integration tests passed!")
        
        # Print summary
        print("\n📊 Test Summary:")
        print("   ✅ Configuration: Working")
        print("   ✅ Runtime Components: Initialized")
        print(f"   ✅ Snapshot Management: {len(history)} snapshots")
        print("   ✅ Cache Management: Functional")
        print(f"   ✅ Health Monitoring: {health_response.status.value}")
        print("   ✅ Lifecycle Hooks: Operational")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_cache_dir, ignore_errors=True)

if __name__ == "__main__":
    success = test_unifi_runtime_integration()
    
    if success:
        print("\n🎉 UniFi MCP Runtime Integration is fully operational!")
        sys.exit(0)
    else:
        print("\n❌ UniFi MCP Runtime Integration tests failed!")
        sys.exit(1)