from crewai import Agent, Crew, Process, Task
from typing import List
from dotenv import load_dotenv

# Local tools
from .tools.transcript_tool import EnhancedTranscriptTool
from .tools.text_cleaner_tool import TranscriptCleanerTool
from .tools.google_docs_tool import GoogleDocsIntegrationTool

load_dotenv()

class FastYouTubeSummarizer():
    """Optimized pipeline: transcript -> summarize -> (optional) publish"""

    def __init__(self):
        self._agents = None
        self._tasks = None

    def get_agents(self):
        """Return list of agents"""
        if self._agents is None:
            self._agents = [
                Agent(
                    role="YouTube Video Processor",
                    goal="Extract and process YouTube video transcripts efficiently",
                    backstory="You are an expert at quickly extracting YouTube transcripts, cleaning them, and preparing them for summarization. You work fast and accurately.",
                    verbose=False,  # Reduce verbosity for speed
                    tools=[EnhancedTranscriptTool(), TranscriptCleanerTool()],
                    max_iter=1,  # Limit iterations for speed
                    allow_delegation=False  # No delegation to avoid overhead
                ),
                Agent(
                    role="AI Summary Writer",
                    goal="Create comprehensive summaries from video transcripts",
                    backstory="You excel at creating clear, well-structured summaries that capture all key points from video content. You write concise but comprehensive summaries.",
                    verbose=False,  # Reduce verbosity for speed
                    max_iter=1,  # Limit iterations for speed
                    allow_delegation=False  # No delegation to avoid overhead
                ),
                Agent(
                    role="Google Docs Publisher",
                    goal="Publish summaries to Google Docs when requested",
                    backstory="You handle the technical details of creating formatted Google Docs from summaries.",
                    verbose=False,
                    tools=[GoogleDocsIntegrationTool()],
                    max_iter=1,
                    allow_delegation=False
                )
            ]
        return self._agents

    def get_tasks(self):
        """Return list of tasks"""
        if self._tasks is None:
            agents = self.get_agents()
            
            extract_task = Task(
                description="""
                Extract the transcript from {youtube_url} and clean it in one step:
                1. Get the transcript using the best available language
                2. Clean the text by removing timestamps and filler words
                3. Output clean, readable transcript text
                """,
                expected_output="Clean transcript text ready for summarization",
                agent=agents[0],  # transcript processor
                output_file="transcript.md"
            )
            
            summarize_task = Task(
                description="""
                Create a comprehensive summary from the cleaned transcript:
                - Include main topics and key points
                - Use clear headings and bullet points
                - Keep it concise but complete
                - Write in markdown format
                """,
                expected_output="A well-structured markdown summary with headings and bullet points",
                agent=agents[1],  # summarizer
                context=[extract_task],
                output_file="SUMMARY.md"
            )
            
            gdocs_task = Task(
                description="""
                If publish_to_gdocs is True, create a Google Doc from the summary.
                Use gdocs_title as the document title if provided.
                If publish_to_gdocs is False, skip and return "Google Docs publishing skipped".
                """,
                expected_output="Google Docs URL if published, or skip message if not requested",
                agent=agents[2],  # docs publisher
                context=[summarize_task]
            )
            
            self._tasks = [extract_task, summarize_task, gdocs_task]
        return self._tasks

    def crew(self) -> Crew:
        """Create and return the crew"""
        return Crew(
            agents=self.get_agents(),
            tasks=self.get_tasks(),
            process=Process.sequential,
            verbose=False,  # Reduce logging for speed
            memory=False,   # Disable memory to reduce overhead
            max_rpm=30      # Increase requests per minute
        )
