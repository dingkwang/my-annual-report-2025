#!/usr/bin/env python3
"""
Diary Generator - Generate daily diaries from OpenAI conversation exports
"""

import json
import logging
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field
from tqdm import tqdm


class DayDiary(BaseModel):
    """Data model for a single day's diary"""

    title: str = Field(
        description="A 10-20 character title summarizing the day's main topics"
    )
    content: str = Field(
        description="The diary content. Focus on what I thought and did that day."
    )


class YearSummary(BaseModel):
    """Data model for annual summary"""

    title: str = Field(
        description="A title for the year summary, e.g., '2024年度总结'"
    )
    content: str = Field(
        description="Annual summary focusing on non-technical growth, reflections, and personal development"
    )


class AnnualResume(BaseModel):
    """Data model for annual resume with year-specific entries"""

    field_2021_and_before: str = Field(
        alias="2021_and_before",
        description="Career history up to and including 2021"
    )
    field_2022: str = Field(alias="2022", description="Career events in 2022")
    field_2023: str = Field(alias="2023", description="Career events in 2023")
    field_2024: str = Field(alias="2024", description="Career events in 2024")
    field_2025: str = Field(alias="2025", description="Career events in 2025")

    class Config:
        populate_by_name = True


class DiaryRecord(TypedDict):
    """Type for diary record stored in generated_diaries list"""
    date: str
    diary: DayDiary


class AgentWrapper:
    """Wrapper class for LLM with structured output parsing"""

    def __init__(
        self,
        llm: ChatOpenAI,
        parser: PydanticOutputParser[DayDiary],
        llm_config: Dict[str, Any],
    ) -> None:
        self.llm = llm
        self.parser = parser
        self.llm_config = llm_config

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, DayDiary]:
        messages: List[Dict[str, str]] = inputs.get("messages", [])

        # Add format instructions to the last user message
        if messages and messages[-1]["role"] == "user":
            format_instructions = self.parser.get_format_instructions()
            messages[-1]["content"] += f"\n\n{format_instructions}"

        # Invoke LLM
        response: AIMessage = self.llm.invoke(messages)  # type: ignore[assignment]

        # Parse response
        try:
            content_text: str = response.content if isinstance(response.content, str) else str(response.content)
            structured_response = self.parser.parse(content_text)
        except Exception:
            # Fallback to basic parsing
            content_str: str = response.content if isinstance(response.content, str) else str(response.content)
            structured_response = DayDiary(
                title=f"日记 - {self.llm_config.get('model', 'AI')}",
                content=content_str[:500],
            )

        return {"structured_response": structured_response}


class DiaryGenerator:
    """Generate diaries from conversation data with full context accumulation"""

    config: Dict[str, Any]
    output_dir: Path
    full_context: str
    generated_diaries: List[DiaryRecord]
    logger: logging.Logger
    example_config: Dict[str, Any]

    def __init__(self, config_path: str = "config.yaml", example_path: str = "example_diary.json"):
        """Initialize the diary generator"""
        self.config = self._load_config(config_path)
        self.example_config = self._load_example_config(example_path)

        # Setup logging early so we can use it during initialization
        self._setup_logging()

        # Generate annual resume if not exists
        if not self._has_annual_resume():
            print("_annual_resume not found in config.yaml, generating...")
            try:
                annual_resume = self._generate_annual_resume()
                if annual_resume:
                    self._save_annual_resume_to_config(annual_resume, config_path)
                    self.config = self._load_config(config_path)
                    print("Successfully generated and saved annual resume")
            except Exception as e:
                self.logger.error(f"Failed to generate annual resume: {str(e)}")
                print(f"Warning: Failed to generate annual resume: {str(e)}")

        self.agent = self._init_agent()
        self.output_dir = Path(str(self.config["output"]["base_dir"]))
        self.full_context = ""  # Full accumulation mode (like podcastify)
        self.generated_diaries = []  # Store all generated diary objects

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, "r", encoding="utf-8") as f:
            result: Dict[str, Any] = yaml.safe_load(f)
            return result

    def _load_example_config(self, example_path: str) -> Dict[str, Any]:
        """Load example configuration from JSON file"""
        with open(example_path, "r", encoding="utf-8") as f:
            result: Dict[str, Any] = json.load(f)
            return result

    def _has_annual_resume(self) -> bool:
        """Check if _annual_resume exists in config and is not empty"""
        annual_resume = self.config.get("_annual_resume", {})
        if not annual_resume or not isinstance(annual_resume, dict):
            return False

        # Check for both string and integer keys (YAML can parse years as integers)
        required_keys = ["2021_and_before", "2022", "2023", "2024", "2025"]
        required_keys_int = [2022, 2023, 2024, 2025]

        # Check string key for 2021_and_before
        if "2021_and_before" not in annual_resume:
            return False
        if not isinstance(annual_resume["2021_and_before"], str):
            return False
        if len(annual_resume["2021_and_before"].strip()) == 0:
            return False

        # Check year keys (can be string or int)
        for year_str, year_int in zip(["2022", "2023", "2024", "2025"], required_keys_int):
            # Check if either string or int version exists
            if year_str not in annual_resume and year_int not in annual_resume:
                return False
            # Get value using either key
            value = annual_resume.get(year_str) or annual_resume.get(year_int)
            if not isinstance(value, str) or len(value.strip()) == 0:
                return False

        return True

    def _generate_annual_resume(self) -> Dict[str, str]:
        """Generate annual resume from resume_plain_text using LLM with structured output"""
        resume_plain_text = self.example_config.get("resume_plain_text", "")

        if not resume_plain_text or not resume_plain_text.strip():
            self.logger.warning("resume_plain_text is empty, skipping generation")
            return {}

        self.logger.info("Generating annual resume from resume_plain_text...")

        parser: PydanticOutputParser[AnnualResume] = PydanticOutputParser(
            pydantic_object=AnnualResume
        )

        system_prompt = """You are helping to parse a career resume into year-by-year entries.
Given a plain text resume, break it down by year into specific time periods.

Requirements:
1. Parse into exactly 5 periods: 2021_and_before, 2022, 2023, 2024, 2025
2. Provide concise summary of career activities for each year
3. Use Chinese for output
4. If year not mentioned, write "无记录" or infer from context
5. Keep each entry concise (1-2 sentences)"""

        user_prompt = f"""Please parse this resume into year-by-year entries:

{resume_plain_text}

Parse into the required 5 time periods."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        format_instructions = parser.get_format_instructions()
        messages[-1]["content"] += f"\n\n{format_instructions}"

        llm_config: Dict[str, Any] = self.config["llm"]
        llm = ChatOpenAI(
            model=llm_config["model"],
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            temperature=llm_config.get("temperature", 0.3),
        )

        response: AIMessage = llm.invoke(messages)  # type: ignore[assignment]

        try:
            content_text: str = response.content if isinstance(response.content, str) else str(response.content)
            annual_resume: AnnualResume = parser.parse(content_text)

            result = {
                "2021_and_before": annual_resume.field_2021_and_before,
                "2022": annual_resume.field_2022,
                "2023": annual_resume.field_2023,
                "2024": annual_resume.field_2024,
                "2025": annual_resume.field_2025,
            }

            self.logger.info("Successfully generated annual resume")
            return result

        except Exception as e:
            self.logger.error(f"Error parsing annual resume: {str(e)}")
            raise

    def _save_annual_resume_to_config(self, annual_resume: Dict[str, str], config_path: str = "config.yaml") -> None:
        """Save generated annual resume to config.yaml, preserving structure"""
        self.logger.info(f"Saving annual resume to {config_path}...")

        self.config["_annual_resume"] = annual_resume

        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find _annual_resume section
        annual_resume_start = -1
        annual_resume_end = -1

        for i, line in enumerate(lines):
            if line.strip().startswith("_annual_resume:"):
                annual_resume_start = i
            elif annual_resume_start >= 0 and not line.startswith((" ", "\t")) and line.strip():
                annual_resume_end = i
                break

        # If not found, append at end
        if annual_resume_start == -1:
            with open(config_path, "a", encoding="utf-8") as f:
                f.write("\n_annual_resume:\n")
                for key, value in annual_resume.items():
                    # Quote the key to prevent YAML from parsing years as integers
                    f.write(f'    "{key}": {value}\n')
            self.logger.info("Added new _annual_resume section")
            return

        # Replace existing section
        if annual_resume_end == -1:
            annual_resume_end = len(lines)

        new_section = ["_annual_resume:\n"]
        for key, value in annual_resume.items():
            # Quote the key to prevent YAML from parsing years as integers
            new_section.append(f'    "{key}": {value}\n')

        new_lines = lines[:annual_resume_start] + new_section + lines[annual_resume_end:]

        with open(config_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        self.logger.info("Successfully updated _annual_resume in config.yaml")

    def _get_date_aware_resume(self, target_date: str) -> str:
        """Get accumulated resume string up to the target date

        Args:
            target_date: Date in format YYYY-MM-DD

        Returns:
            String with accumulated resume entries up to target year
        """
        if not self.config.get("_annual_resume"):
            self.logger.warning("_annual_resume not found, returning empty string")
            return ""

        annual_resume = self.config["_annual_resume"]
        target_year = int(target_date.split("-")[0])

        resume_parts = []

        # Always include 2021_and_before
        if "2021_and_before" in annual_resume:
            resume_parts.append(f"2021及之前: {annual_resume['2021_and_before']}")

        # Add years from 2022 up to target_year
        # Handle both string and integer keys (YAML can parse years as integers)
        for year in range(2022, min(target_year + 1, 2026)):  # Cap at 2025
            year_str = str(year)
            year_int = year
            # Try both string and integer keys
            value = annual_resume.get(year_str) or annual_resume.get(year_int)
            if value:
                resume_parts.append(f"{year}年: {value}")

        return "\n".join(resume_parts)

    def _init_agent(self) -> "AgentWrapper":
        """Initialize the agent with structured output"""
        llm_config: Dict[str, Any] = self.config["llm"]

        # Create LLM with OpenAI API
        llm = ChatOpenAI(
            model=llm_config["model"],
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            temperature=llm_config.get("temperature", 0.3),
        )

        # Create parser for structured output
        parser: PydanticOutputParser[DayDiary] = PydanticOutputParser(pydantic_object=DayDiary)

        return AgentWrapper(llm, parser, llm_config)

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        log_config: Dict[str, Any] = self.config["logging"]
        log_file = Path(str(log_config["file"]))
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, str(log_config["level"])),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def generate_all_diaries(self, conversations_path: str, overwrite: bool = False) -> None:
        """Generate diaries for all dates

        Args:
            conversations_path: Path to conversations JSON file
            overwrite: If True, regenerate all diaries ignoring progress.json
        """
        self.logger.info(f"Loading conversations from {conversations_path}")

        # Load conversation data
        with open(conversations_path, "r", encoding="utf-8") as f:
            conversations_by_date = json.load(f)

        sorted_dates = sorted(conversations_by_date.keys())
        total_days = len(sorted_dates)

        self.logger.info(f"Found {total_days} days with conversations")
        print(f"\n📅 Preparing to generate diaries for {total_days} days...")

        # Load progress if exists (unless overwrite mode)
        processed_dates: set[str] = set()
        if not overwrite:
            progress = self._load_progress()
            processed_dates = set(progress.get("processed_dates", []))
        else:
            self.logger.info("Overwrite mode: ignoring existing progress")
            print("🔄 Overwrite mode: regenerating all diaries...")

        # Process each day
        for date in tqdm(sorted_dates, desc="Generating diaries"):
            # Skip if already processed (unless overwrite mode)
            if not overwrite and date in processed_dates:
                self.logger.info(f"Skipping {date} - already processed")
                # Load existing diary to context
                self._load_existing_diary_to_context(date)
                continue

            try:
                # Generate diary for this day
                diary = self.generate_single_day(date, conversations_by_date[date])

                # Save diary
                self.save_diary(date, diary)

                # Update progress
                self._save_progress(date)

                # Log success
                self.logger.info(f"Generated diary for {date}: {diary.title}")

            except Exception as e:
                self.logger.error(f"Error processing {date}: {str(e)}")
                print(f"\n❌ Error processing {date}: {str(e)}")
                continue

        print(
            f"\n✅ Diary generation complete! Generated {len(self.generated_diaries)} diaries."
        )

        # Generate annual summaries
        self.generate_annual_summaries(sorted_dates)

    def generate_single_day(self, date: str, conversations: List[Dict[str, Any]]) -> DayDiary:
        """Generate diary for a single day"""
        # Preprocess conversations
        processed_convs = self._preprocess_conversations(conversations)

        if not processed_convs:
            self.logger.warning(f"No valid conversations for {date}")
            return DayDiary(
                title=f"{date} - 无对话记录", content="今天没有进行任何对话。"
            )

        # Build prompt
        messages = self._build_prompt(date, processed_convs)

        # Generate diary using agent
        result = self.agent.invoke({"messages": messages})
        diary = result["structured_response"]

        # Update full context (accumulate like podcastify)
        if not self.full_context:
            self.full_context = f"【{date}】{diary.title}\n{diary.content}"
        else:
            self.full_context += f"\n\n【{date}】{diary.title}\n{diary.content}"

        # Record generated diary
        self.generated_diaries.append({"date": date, "diary": diary})

        return diary

    def _preprocess_conversations(self, conversations: List[Dict[str, Any]]) -> str:
        """Preprocess conversations for the day"""
        processed_parts: List[str] = []

        for conv in conversations:
            title = conv.get("title", "Untitled")
            messages = conv.get("messages", [])

            # Filter out system messages and very short conversations
            user_assistant_messages = [
                msg
                for msg in messages
                if msg.get("author") in ["user", "assistant"]
                and len(msg.get("text", ""))
                > self.config["diary_settings"]["min_conversation_length"]
            ]

            if not user_assistant_messages:
                continue

            # Format conversation
            conv_text = f"对话主题：{title}\n"

            for msg in user_assistant_messages:
                author = "我" if msg["author"] == "user" else "AI助手"
                text = (
                    msg["text"][:500] + "..." if len(msg["text"]) > 500 else msg["text"]
                )
                conv_text += f"{author}：{text}\n"

            processed_parts.append(conv_text)

        return "\n---\n".join(processed_parts)

    def _build_prompt(self, date: str, processed_convs: str) -> List[Dict[str, str]]:
        """Build the prompt for diary generation"""
        # Load example diary from config and get date-aware resume
        example_diary = self.example_config.get("example_diary", "")
        resume = self._get_date_aware_resume(date)
        customer_requirements = self.example_config.get("requirements", "")

        system_prompt = f"""你是以下对话的用户，以下都是你和 AI 的对话，以第一人称写一篇客观的日记。

个人简历（请不要在日记中引用）：
{resume}
注意：
    你在写今天日记的之后不可能之后知道未来发生的事情。

日记示例：
{example_diary}

要求：
1. 生成的日记需要包含一个简短的标题（概括当天主要内容）和正文
2. 日记内容应真实反映我当天在想什么，发生了什么事情
3. 主要专注于当天内容。
4. 请确保每句话都是第一人称, 你写的日记都是你的所思所想所做，而不是在推测对话人的想法。

Customer requirements:
{customer_requirements}

输出格式：
- title: 一个10-20字的标题, 概括当天的主要活动或话题
- content: 简短的日记正文。""
"""
        # Build context section if we have previous diaries (limit to last 50)
        context_section = ""
        if self.generated_diaries:
            # Get the last 50 diaries for context
            recent_diaries = self.generated_diaries[-50:]
            recent_context = "\n\n---\n\n".join(
                [
                    f"日期：{d['date']}\n标题：{d['diary'].title}\n{d['diary'].content}"
                    for d in recent_diaries
                ]
            )
            context_section = f"""以下是之前最近的日记记录（最多50篇），请参考这些内容保持叙述的连贯性：

{recent_context}

"""

        user_prompt = f"""{context_section}日期：{date}

今天的对话记录：
{processed_convs}

请为今天生成中文日记，包含标题和正文。"""

        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return messages

    def _sanitize_filename(self, title: str) -> str:
        """Sanitize title for use in filename"""
        # Remove characters that are invalid in filenames
        sanitized = re.sub(r'[<>:"/\\|?*]', "", title)
        # Replace spaces with underscores
        sanitized = sanitized.replace(" ", "_")
        # Limit length to avoid overly long filenames
        sanitized = sanitized[:50]
        return sanitized

    def save_diary(self, date: str, diary: DayDiary) -> None:
        """Save diary to file"""
        # Parse date to get year
        year = date.split("-")[0]

        # Create year directory if needed
        year_dir = self.output_dir / year
        year_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize title for filename
        safe_title = self._sanitize_filename(diary.title)

        # Save diary file with title in filename
        diary_file = year_dir / f"{date}-{safe_title}.md"

        content = f"""# {diary.title}

**日期**: {date}

{diary.content}
"""

        with open(diary_file, "w", encoding="utf-8") as f:
            f.write(content)

        self.logger.info(f"Saved diary to {diary_file}")

    def _load_progress(self) -> Dict[str, Any]:
        """Load processing progress"""
        progress_file = Path("progress.json")
        if progress_file.exists():
            with open(progress_file, "r") as f:
                result: Dict[str, Any] = json.load(f)
                return result
        return {"processed_dates": []}

    def _save_progress(self, date: str) -> None:
        """Save processing progress"""
        progress = self._load_progress()
        progress["processed_dates"].append(date)
        progress["last_processed"] = date
        progress["last_updated"] = datetime.now().isoformat()

        with open("progress.json", "w") as f:
            json.dump(progress, f, indent=2)

    def _load_existing_diary_to_context(self, date: str) -> None:
        """Load existing diary to maintain context continuity"""
        year = date.split("-")[0]
        diary_file = self.output_dir / year / f"{date}.md"

        if diary_file.exists():
            with open(diary_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Extract title and content from markdown
                lines = content.strip().split("\n")
                if lines:
                    title = lines[0].replace("# ", "")
                    diary_content = "\n".join(lines[4:]) if len(lines) > 4 else ""

                    # Add to context
                    if not self.full_context:
                        self.full_context = f"【{date}】{title}\n{diary_content}"
                    else:
                        self.full_context += f"\n\n【{date}】{title}\n{diary_content}"

    def generate_annual_summaries(self, all_dates: List[str]) -> None:
        """Generate annual summaries for each year that has diaries"""
        # Group dates by year
        years: Dict[str, List[str]] = {}
        for date in all_dates:
            year = date.split("-")[0]
            if year not in years:
                years[year] = []
            years[year].append(date)

        # Generate summary for each year
        for year in sorted(years.keys()):
            print(f"\n📖 Generating annual summary for {year}...")
            try:
                summary = self.generate_year_summary(year, years[year])
                self.save_year_summary(year, summary)
                print(f"✅ Annual summary for {year} completed!")
            except Exception as e:
                self.logger.error(f"Error generating summary for {year}: {str(e)}")
                print(f"❌ Error generating summary for {year}: {str(e)}")

    def generate_year_summary(self, year: str, dates: List[str]) -> YearSummary:
        """Generate summary for a specific year"""
        # Read all diaries for this year
        year_dir = self.output_dir / year
        if not year_dir.exists():
            self.logger.warning(f"No diaries found for {year}")
            return YearSummary(
                title=f"{year}年度总结",
                content=f"{year}年没有日记记录。"
            )

        # Collect all diary contents
        all_diaries = []
        for date in sorted(dates):
            diary_files = list(year_dir.glob(f"{date}-*.md"))
            if diary_files:
                diary_file = diary_files[0]
                with open(diary_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    all_diaries.append(f"【{date}】\n{content}\n")

        if not all_diaries:
            return YearSummary(
                title=f"{year}年度总结",
                content=f"{year}年没有找到日记文件。"
            )

        # Build prompt for annual summary
        all_content = "\n---\n\n".join(all_diaries)

        # Get year-aware resume (only up to this year)
        year_end_date = f"{year}-12-31"
        resume = self._get_date_aware_resume(year_end_date)
        
        # Load previous year's summary if exists
        prev_year = str(int(year) - 1)
        prev_summary_content = ""
        prev_year_dir = self.output_dir / prev_year
        prev_summary_file = prev_year_dir / f"{prev_year}-年度总结.md"
        
        if prev_summary_file.exists():
            with open(prev_summary_file, "r", encoding="utf-8") as f:
                prev_summary_content = f.read()
        
        # Build context section with previous year's summary
        prev_context = ""
        if prev_summary_content:
            prev_context = f"""
以下是{prev_year}年的年度总结，请参考这个作为背景，看看今年相比去年有什么成长和变化：

{prev_summary_content}

---

"""
        
        system_prompt = f"""你是以下对话的用户，现在需要写一篇{year}年的年度总结。

个人简历：
{resume}


要求：
1. 这是一份个人年度总结，着重于非技术方面的内容
2. 关注个人成长、思考、生活变化、人际关系、心态转变等
3. 从全年的日记中提炼出最重要的收获和感悟
4. 使用第一人称，真实反映这一年的心路历程
5. 内容应该有深度，不要流于表面
6. 如果有前一年的总结，可以对比今年的变化和成长
7. 越长越好
8. 我们不知道未来会发生什么，比如 2023 年的年度总结不应该提到 2024 年发生的事情。


输出格式：
- title: 年度总结的标题，例如"2024：成长与蜕变"
- content: 年度总结正文
"""

        user_prompt = f"""{prev_context}{year}年全年日记：

{all_content}

请基于以上全年的日记内容，写一篇深刻的年度总结。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Create parser for YearSummary
        parser: PydanticOutputParser[YearSummary] = PydanticOutputParser(pydantic_object=YearSummary)
        
        # Add format instructions
        format_instructions = parser.get_format_instructions()
        messages[-1]["content"] += f"\n\n{format_instructions}"

        # Invoke LLM
        llm_config: Dict[str, Any] = self.config["llm"]
        llm = ChatOpenAI(
            model=llm_config["model"],
            base_url=llm_config["base_url"],
            api_key=llm_config["api_key"],
            temperature=llm_config.get("temperature", 0.3),
        )
        
        response: AIMessage = llm.invoke(messages)  # type: ignore[assignment]
        
        # Parse response
        try:
            content_text: str = response.content if isinstance(response.content, str) else str(response.content)
            summary = parser.parse(content_text)
        except Exception as e:
            self.logger.error(f"Error parsing summary response: {str(e)}")
            # Fallback
            content_str: str = response.content if isinstance(response.content, str) else str(response.content)
            summary = YearSummary(
                title=f"{year}年度总结",
                content=content_str[:1500],
            )

        return summary

    def save_year_summary(self, year: str, summary: YearSummary) -> None:
        """Save annual summary to file"""
        year_dir = self.output_dir / year
        year_dir.mkdir(parents=True, exist_ok=True)

        summary_file = year_dir / f"{year}-年度总结.md"

        content = f"""# {summary.title}

**年份**: {year}

{summary.content}
"""

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(content)

        self.logger.info(f"Saved annual summary to {summary_file}")


if __name__ == "__main__":
    # This is for testing - main script will be separate
    generator = DiaryGenerator()
    print("DiaryGenerator initialized successfully!")
