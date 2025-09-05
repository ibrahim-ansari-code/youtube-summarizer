from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv

# Local tools
from .tools.transcript_tool import EnhancedTranscriptTool
from .tools.text_cleaner_tool import TranscriptCleanerTool
from .tools.google_docs_tool import GoogleDocsIntegrationTool

load_dotenv()

@CrewBase
class YouTubeSummarizer():
    """Pipeline: transcript -> clean -> summarize -> review -> (optional) publish"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Agents
    @agent
    def transcript_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['transcript_extractor'],
            verbose=True,
            tools=[EnhancedTranscriptTool()]
        )

    @agent
    def text_cleaner(self) -> Agent:
        return Agent(
            config=self.agents_config['text_cleaner'],
            verbose=True,
            tools=[TranscriptCleanerTool()]
        )

    @agent
    def summary_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['summary_writer'],
            verbose=True
        )

    @agent
    def quality_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['quality_checker'],
            verbose=True
        )

    @agent
    def docs_uploader(self) -> Agent:
        return Agent(
            config=self.agents_config['docs_uploader'],
            verbose=True,
            tools=[GoogleDocsIntegrationTool()]
        )

    # Tasks
    @task
    def transcript_task(self) -> Task:
        return Task(
            config=self.tasks_config['transcript_task']
        )

    @task
    def cleaning_task(self) -> Task:
        return Task(
            config=self.tasks_config['cleaning_task']
        )

    @task
    def summarize_task(self) -> Task:
        return Task(
            config=self.tasks_config['summarize_task']
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_task']
        )

    @task
    def gdocs_publish_task(self) -> Task:
        return Task(
            config=self.tasks_config['gdocs_publish_task']
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
