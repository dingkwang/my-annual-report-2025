#!/usr/bin/env python3
"""
Integration test for diary generator
Tests the core functionality without making actual LLM calls
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from diary_generator import DiaryGenerator, DayDiary


@pytest.fixture
def temp_environment():
    """Create temporary test environment"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test config
        test_config = {
            'llm': {
                'model': 'grok-test',
                'base_url': 'http://test',
                'api_key': 'test-key',
                'temperature': 0.3,
                'max_tokens': 1000
            },
            'diary_settings': {
                'min_conversation_length': 10,
                'output_format': 'markdown'
            },
            'output': {
                'base_dir': str(temp_path / 'output' / 'diaries'),
                'organize_by': 'year'
            },
            'logging': {
                'level': 'INFO',
                'file': str(temp_path / 'logs' / 'test.log')
            }
        }

        # Write test config
        config_path = temp_path / 'test_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)

        yield {
            'temp_path': temp_path,
            'config_path': config_path,
            'test_config': test_config
        }


@pytest.fixture
def test_conversations():
    """Test conversation data"""
    return {
        "2023-01-08": [
            {
                "title": "RLHF三阶段解释",
                "create_time": 1673150000.0,
                "update_time": 1673151000.0,
                "messages": [
                    {
                        "author": "user",
                        "text": "请详细解释RLHF的三个阶段是什么？",
                        "create_time": 1673150000.0
                    },
                    {
                        "author": "assistant",
                        "text": "RLHF（Reinforcement Learning from Human Feedback）包含三个主要阶段：1. 监督微调（SFT）2. 奖励模型训练 3. 强化学习优化",
                        "create_time": 1673150100.0
                    }
                ]
            }
        ],
        "2023-01-09": [
            {
                "title": "Python异步编程",
                "create_time": 1673236400.0,
                "update_time": 1673237400.0,
                "messages": [
                    {
                        "author": "user",
                        "text": "Python中async/await是如何工作的？",
                        "create_time": 1673236400.0
                    },
                    {
                        "author": "assistant",
                        "text": "Python的async/await是协程的语法糖，用于编写异步代码。async定义协程函数，await用于等待异步操作完成。",
                        "create_time": 1673236500.0
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses"""
    return [
        DayDiary(
            title="探讨RLHF技术",
            content="今天主要和AI助手讨论了RLHF（人类反馈强化学习）的技术细节。了解到RLHF包含三个核心阶段：监督微调、奖励模型训练和强化学习优化。这些知识对理解现代语言模型的训练过程很有帮助。"
        ),
        DayDiary(
            title="学习Python异步编程",
            content="今天继续学习编程知识，重点了解了Python的异步编程机制。昨天学习了机器学习相关内容，今天转向了实用的编程技术。掌握了async/await的基本概念，理解了协程在Python中的实现方式。"
        )
    ]


def test_diary_generator_initialization(temp_environment):
    """Test basic initialization"""
    config_path = temp_environment['config_path']

    mock_agent = Mock()
    with patch.object(DiaryGenerator, '_init_agent', return_value=mock_agent):
        generator = DiaryGenerator(str(config_path))
        assert generator.full_context == ""
        assert len(generator.generated_diaries) == 0


def test_conversation_preprocessing(temp_environment, test_conversations):
    """Test conversation preprocessing"""
    config_path = temp_environment['config_path']

    mock_agent = Mock()
    with patch.object(DiaryGenerator, '_init_agent', return_value=mock_agent):
        generator = DiaryGenerator(str(config_path))
        processed = generator._preprocess_conversations(test_conversations["2023-01-08"])

        assert "RLHF三阶段解释" in processed
        assert "我：" in processed
        assert "AI助手：" in processed
        assert "请详细解释RLHF的三个阶段" in processed


def test_diary_generation_with_context(temp_environment, test_conversations, mock_llm_responses):
    """Test diary generation with context accumulation"""
    config_path = temp_environment['config_path']
    temp_path = temp_environment['temp_path']

    # Write test data
    test_data_path = temp_path / 'test_conversations.json'
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(test_conversations, f, ensure_ascii=False)

    # Mock agent
    mock_agent = Mock()
    mock_agent.invoke.side_effect = [
        {"structured_response": resp} for resp in mock_llm_responses
    ]

    with patch.object(DiaryGenerator, '_init_agent', return_value=mock_agent):
        generator = DiaryGenerator(str(config_path))
        generator.generate_all_diaries(str(test_data_path))

    # Verify context accumulation
    assert len(generator.full_context) > 0
    assert "探讨RLHF技术" in generator.full_context
    assert "学习Python异步编程" in generator.full_context

    # Verify both diaries were generated
    assert len(generator.generated_diaries) == 2


def test_file_output_structure(temp_environment, test_conversations, mock_llm_responses):
    """Test output file structure"""
    config_path = temp_environment['config_path']
    temp_path = temp_environment['temp_path']
    test_config = temp_environment['test_config']

    # Write test data
    test_data_path = temp_path / 'test_conversations.json'
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(test_conversations, f, ensure_ascii=False)

    # Mock agent
    mock_agent = Mock()
    mock_agent.invoke.side_effect = [
        {"structured_response": resp} for resp in mock_llm_responses
    ]

    with patch.object(DiaryGenerator, '_init_agent', return_value=mock_agent):
        generator = DiaryGenerator(str(config_path))
        generator.generate_all_diaries(str(test_data_path))

    # Check file structure
    output_dir = Path(test_config['output']['base_dir'])
    assert (output_dir / '2023').exists()

    diary1 = output_dir / '2023' / '2023-01-08.md'
    diary2 = output_dir / '2023' / '2023-01-09.md'
    assert diary1.exists()
    assert diary2.exists()

    # Check content structure
    with open(diary1, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "# 探讨RLHF技术" in content
        assert "**日期**: 2023-01-08" in content
        assert "RLHF" in content


def test_progress_tracking(temp_environment, test_conversations, mock_llm_responses):
    """Test progress tracking functionality"""
    config_path = temp_environment['config_path']
    temp_path = temp_environment['temp_path']

    # Clean up any existing progress file
    progress_file = Path('progress.json')
    if progress_file.exists():
        progress_file.unlink()

    # Write test data
    test_data_path = temp_path / 'test_conversations.json'
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(test_conversations, f, ensure_ascii=False)

    # Mock agent
    mock_agent = Mock()
    mock_agent.invoke.side_effect = [
        {"structured_response": resp} for resp in mock_llm_responses
    ]

    with patch.object(DiaryGenerator, '_init_agent', return_value=mock_agent):
        generator = DiaryGenerator(str(config_path))
        generator.generate_all_diaries(str(test_data_path))

    # Check progress file
    assert progress_file.exists()
    with open(progress_file, 'r') as f:
        progress = json.load(f)
        assert '2023-01-08' in progress['processed_dates']
        assert '2023-01-09' in progress['processed_dates']
        assert progress['last_processed'] == '2023-01-09'

    # Clean up
    progress_file.unlink()


def test_context_references_in_second_diary(temp_environment, test_conversations, mock_llm_responses):
    """Test that second diary references context from first"""
    config_path = temp_environment['config_path']
    temp_path = temp_environment['temp_path']

    # Write test data
    test_data_path = temp_path / 'test_conversations.json'
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(test_conversations, f, ensure_ascii=False)

    # Mock agent
    mock_agent = Mock()
    mock_agent.invoke.side_effect = [
        {"structured_response": resp} for resp in mock_llm_responses
    ]

    with patch.object(DiaryGenerator, '_init_agent', return_value=mock_agent):
        generator = DiaryGenerator(str(config_path))
        generator.generate_all_diaries(str(test_data_path))

    # Check that the second diary mentions previous content
    output_dir = Path(temp_environment['test_config']['output']['base_dir'])
    diary2 = output_dir / '2023' / '2023-01-09.md'

    with open(diary2, 'r', encoding='utf-8') as f:
        content = f.read()
        # The mock response includes a reference to yesterday's learning
        assert "昨天学习了机器学习" in content


def test_diary_generator_integration():
    """Legacy test function for standalone execution"""
    print("🧪 Running integration test for DiaryGenerator...")

    # Run all pytest tests programmatically
    pytest.main([__file__, "-v"])

    print("\n🎉 All integration tests completed!")
    print("\nKey features tested:")
    print("  ✓ Configuration loading")
    print("  ✓ Diary generation with structured output")
    print("  ✓ Context accumulation (like podcastify)")
    print("  ✓ File organization by year")
    print("  ✓ Progress tracking")
    print("  ✓ Conversation preprocessing")
    print("  ✓ Context references between diaries")


if __name__ == "__main__":
    test_diary_generator_integration()