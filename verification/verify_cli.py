import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import os

# Add parent directory to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import main (since we patch it inside the test methods) -- wait, we need to import it first
# to have it in sys.modules, but we need to patch its internal usage.
# Since main.py does: from src.orchestrator import get_orchestrator_graph
# we need to patch 'main.get_orchestrator_graph' inside the tests.

# However, we must ensure src.orchestrator is mockable or importable first.
# Let's mock src.orchestrator BEFORE importing main so main doesn't fail import if no API key etc.
# But main only calls get_orchestrator_graph() inside main(), not at module level.
# So importing main is safe as long as we don't run main().

import main as cli_main

class TestCLI(unittest.TestCase):
    
    @patch('builtins.input', side_effect=['quit'])
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', ['main.py'])
    def test_cli_quit(self, mock_stdout, mock_input):
        """Test that typing 'quit' exits the loop."""
        # Patch the function as it appears in main's namespace
        with patch('main.get_orchestrator_graph') as mock_get_graph:
             mock_graph = MagicMock()
             mock_get_graph.return_value = mock_graph
             
             cli_main.main()
             
             output = mock_stdout.getvalue()
             self.assertIn("Welcome to the College ROI Agent CLI!", output)
             self.assertIn("Goodbye!", output)

    @patch('builtins.input', side_effect=['quit'])
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', ['main.py', 'Initial College'])
    def test_cli_initial_arg(self, mock_stdout, mock_input):
        """Test that initial argument triggers a graph invocation."""
        with patch('main.get_orchestrator_graph') as mock_get_graph:
             mock_graph = MagicMock()
             # Configure the mock to return a response structure matching what main.py expects
             mock_graph.invoke.return_value = {"messages": [MagicMock(content="Mock Response")]}
             mock_get_graph.return_value = mock_graph
             
             cli_main.main()
             
             output = mock_stdout.getvalue()
             self.assertIn("You: Find the per-year tuition cost for Initial College", output)
             # Check if graph.invoke was called
             mock_graph.invoke.assert_called()
             self.assertIn("Assistant: Mock Response", output)

if __name__ == '__main__':
    unittest.main()
