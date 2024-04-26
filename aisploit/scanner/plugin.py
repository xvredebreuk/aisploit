from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Sequence

from .report import Issue, IssueCategory
from ..converters import NoOpConverter
from ..core import BaseConverter, BaseTarget, BaseTextClassifier, Prompt, Score
from ..sender import SenderJob, SendReport, SendReportEntry


@dataclass(kw_only=True)
class BasePlugin(ABC):
    """Abstract base class for plugins."""

    name: str
    issue_category: IssueCategory
    issue_references: Sequence[str] = field(default_factory=list)

    @abstractmethod
    def run(self, *, run_id: str, target: BaseTarget) -> Sequence[Issue]:
        """Run the plugin.

        Args:
            run_id (str): The ID of the run.
            target (BaseTarget): The target to execute the plugin against.

        Returns:
            Sequence[Issue]: A sequence of issues found by the plugin.
        """
        pass


@dataclass(kw_only=True)
class SendPromptsPlugin(BasePlugin, ABC):
    """Abstract base class for plugins that send prompts."""

    converters: List[BaseConverter] = field(default_factory=lambda: [NoOpConverter()])
    classifier: BaseTextClassifier

    @abstractmethod
    def create_prompts(self) -> Sequence[str | Prompt]:
        """Create prompts to send.

        Returns:
            Sequence[str | Prompt]: A sequence of prompts.
        """
        pass

    def run(self, *, run_id: str, target: BaseTarget) -> Sequence[Issue]:
        """Run the plugin.

        Args:
            run_id (str): The ID of the run.
            target (BaseTarget): The target to execute the plugin against.

        Returns:
            Sequence[Issue]: A sequence of issues found by the plugin.
        """
        sender = SenderJob(
            target=target,
            converters=self.converters,
            include_original_prompt=True,
            disable_progressbar=True,
        )

        report = sender.execute(
            run_id=run_id,
            prompts=self.create_prompts(),
        )

        return self._score_report(report)

    def _score_report(self, report: SendReport) -> Sequence[Issue]:
        """Score the report entries and generate issues.

        Args:
            report (SendReport): The report generated by sending prompts.

        Returns:
            Sequence[Issue]: A sequence of issues found by scoring the report entries.
        """
        issues: List[Issue] = []

        for entry in report:
            score = self._score_entry(entry)
            if score.flagged:
                issues.append(
                    Issue(
                        category=self.issue_category,
                        references=self.issue_references,
                        send_report_entry=entry,
                        score=score,
                    )
                )

        return issues

    def _score_entry(self, entry: SendReportEntry) -> Score:
        """Score a report entry.

        Args:
            entry (SendReportEntry): A report entry to score.

        Returns:
            Score: The score generated by scoring the report entry.
        """
        return self.classifier.score(entry.response.content, metadata=entry.metadata)
