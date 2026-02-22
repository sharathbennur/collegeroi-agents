import unittest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from src.orchestrator import orchestrator_node, OrchestratorState

class TestOrchestratorScope(unittest.TestCase):
    
    @patch('src.orchestrator.get_model')
    def test_in_scope_query(self, mock_get_model):
        """Test that a tuition query gets a helpful response."""
        mock_model = MagicMock()
        mock_model.invoke.return_value = AIMessage(content="I will research tuition for Stanford.")
        mock_get_model.return_value = mock_model
        
        state = OrchestratorState(
            messages=[MagicMock(content="Find tuition for Stanford")],
            colleges_queried=[],
            validated_info={}
        )
        
        result = orchestrator_node(state)
        response = result["messages"][0].content
        
        # Verify model was called
        mock_model.invoke.assert_called()
        self.assertIn("tuition", response)

    @patch('src.orchestrator.get_model')
    def test_out_of_scope_query(self, mock_get_model):
        """Test that a random query is declined (simulated by prompt instruction)."""
        # Since we are mocking the LLM, we can't test if the LLM *actually* declines 
        # based on the prompt unless we run a real integration test.
        # However, we can inspect the system prompt passed to the model to ensure 
        # it contains the restrictive instructions.
        
        mock_model = MagicMock()
        mock_model.invoke.return_value = AIMessage(content="I cannot help with that.")
        mock_get_model.return_value = mock_model
        
        state = OrchestratorState(
            messages=[MagicMock(content="Write a poem about cats")],
            colleges_queried=[],
            validated_info={}
        )
        
        orchestrator_node(state)
        
        # Get the messages passed to the model
        call_args = mock_model.invoke.call_args
        messages_arg = call_args[0][0]
        system_prompt = messages_arg[0].content
        
        # VERIFY the instructions are present
        self.assertIn("YOUR ONLY CAPABILITIES ARE", system_prompt)
        self.assertIn("politely DECLINE", system_prompt)
        self.assertIn("specialized agent for college cost research only", system_prompt)

if __name__ == '__main__':
    unittest.main()
