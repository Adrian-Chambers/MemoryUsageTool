Write unit tests for my MemoryTrackerApp project that verify:

1. Process Cache Management:
   - Test that the process cache is properly initialized and updated
   - Verify that the cache refresh interval (15 seconds) is respected
   - Test that the cache is properly cleared and updated with new process data

2. Memory Usage Calculations:
   - Test the accuracy of memory usage calculations for different processes
   - Verify that memory thresholds are correctly identified and flagged
   - Test edge cases with processes that have zero memory usage or extremely high memory usage

3. GUI Updates:
   - Test that the efficiency bar updates correctly based on system memory usage
   - Verify that memory tables (HighestMemoryTable and FlaggedMemoryTable) are properly populated and updated
   - Test that the UI updates don't freeze the main thread

4. Process Management:
   - Test the process termination functionality
   - Verify that file location opening works correctly
   - Test process detail viewing functionality

Use appropriate mocking for system calls and process information to ensure tests are reliable and don't depend on actual system state. 