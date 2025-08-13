import pytest
import os
from unittest.mock import patch, MagicMock
from llm import call_llm, _fallback_heuristic

def test_fallback_heuristic_matchup():
    """Test fallback heuristic for matchup questions"""
    result = _fallback_heuristic("What's the matchup between PHI and DAL?")
    assert result["tool_call"]["name"] == "fetch_nfl_data"
    assert result["tool_call"]["arguments"]["kind"] == "matchup"
    assert result["tool_call"]["arguments"]["away"] == "phi"
    assert result["tool_call"]["arguments"]["home"] == "dal"

def test_fallback_heuristic_team():
    """Test fallback heuristic for team questions"""
    result = _fallback_heuristic("Who are the starters for KC?")
    assert result["tool_call"]["name"] == "fetch_nfl_data"
    assert result["tool_call"]["arguments"]["kind"] == "team"
    assert result["tool_call"]["arguments"]["abbr"] == "kc"

def test_fallback_heuristic_teams_week():
    """Test fallback heuristic for general week questions"""
    result = _fallback_heuristic("What teams are playing in week 1?")
    assert result["tool_call"]["name"] == "fetch_nfl_data"
    assert result["tool_call"]["arguments"]["kind"] == "teams_week"

@patch.dict(os.environ, {"LLM_PROVIDER": "none"})
def test_llm_fallback_mode():
    """Test LLM falls back to heuristic when provider is none"""
    messages = [{"role": "user", "content": "PHI vs DAL matchup"}]
    result = call_llm(messages)
    assert "tool_call" in result
    assert result["tool_call"]["name"] == "fetch_nfl_data"

@patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"})
@patch('llm.OpenAI')
def test_llm_openai_success(mock_openai):
    """Test successful OpenAI call with tool call"""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_tool_call = MagicMock()
    mock_function = MagicMock()
    
    mock_function.name = "fetch_nfl_data"
    mock_function.arguments = '{"kind": "teams_week"}'
    mock_tool_call.function = mock_function
    mock_choice.message.tool_calls = [mock_tool_call]
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    messages = [{"role": "user", "content": "What teams are playing?"}]
    result = call_llm(messages)
    
    assert result["tool_call"]["name"] == "fetch_nfl_data"
    assert result["tool_call"]["arguments"]["kind"] == "teams_week"

@patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"})
@patch('llm.OpenAI')
def test_llm_openai_text_response(mock_openai):
    """Test successful OpenAI call with text response"""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.tool_calls = None
    mock_choice.message.content = "Here's the answer"
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    messages = [{"role": "user", "content": "What teams are playing?"}]
    result = call_llm(messages, tools_schema=False)
    
    # When tools_schema=False, we should get content directly
    assert result["content"] == "Here's the answer"
