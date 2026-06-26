import sys
import os
from unittest.mock import MagicMock

# Mock third-party packages that are missing
sys.modules['schedule'] = MagicMock()
sys.modules['vnstock_data'] = MagicMock()
sys.modules['vnstock_ta'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot_app')))

import main

def mock_reset_market():
    # Attempt to load cache just to see if the file exists
    main.load_alert_cache() 
    raise RuntimeError("Intentional crash!")

# monkey patch main's reference
main.reset_market = mock_reset_market

def test_crash_atomic_caching():
    cache_file = main.ALERT_CACHE_FILE
    if os.path.exists(cache_file):
        os.remove(cache_file)
        
    try:
        main.run_cycle()
    except RuntimeError as e:
        print(f"Caught expected exception: {e}")
        
    if os.path.exists(cache_file):
        print("Pass: .alert_cache was saved despite the crash.")
        sys.exit(0)
    else:
        print("Fail: .alert_cache was NOT saved.")
        sys.exit(1)

if __name__ == '__main__':
    test_crash_atomic_caching()
