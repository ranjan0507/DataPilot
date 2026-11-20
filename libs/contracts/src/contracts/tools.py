from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from contracts.common import (
    OUTPUT_CHARACTERS,
    PREVIEW_ROWS,
    ResultRef,
)

ANALYSIS_FUNCTION_NAMES = (
    "forecast",
    "correlation",
    "outlier",
    "hypothesis_test",
    "distribution",
)
AnalysisFunctionName = Literal[
    "forecast",
    "correlation",
    "outlier",
    "hypothesis_test",
    "distribution",
]

SCOPE_KEYS = {
    "user",
    "user_id",
    "dataset",
    "dataset_id",
    "dataset_version",
    "dataset_version_id",
    "run",
    "run_id",
    "execution",
    "execution_id",
}


def reject_scope_keys(value: dict[str, Any]) -> dict[str, Any]:
    found: set[str] = set()
    pending: list[Any] = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            found.update(SCOPE_KEYS.intersection(item))
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    if found:
        msg = f"Scope fields are not allowed in tool parameters: {', '.join(sorted(found))}"
        raise ValueError(msg)
    return value


class GetDatasetProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetDatasetProfileOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: str = Field(
        description="A bounded schema and profile summary for the scoped dataset.",
        max_length=OUTPUT_CHARACTERS,
    )


class SearchContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        description="Keywords used to find relevant prior results and artifacts.",
        max_length=500,
    )
    limit: int = Field(
        default=PREVIEW_ROWS,
        description="Maximum number of context summaries to return.",
        ge=1,
        le=20,
    )


class ContextSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(
        description="ID of the matching result or artifact.",
    )
    kind: Literal["result", "artifact"] = Field(
        description="Whether the matching item is a result or an artifact.",
    )
    title: str = Field(
        description="Short title for the matching item.",
        max_length=200,
    )
    description: str = Field(
        description="Short description of the matching item.",
        max_length=2_000,
    )
    category: str = Field(
        description="Category or type of the matching item.",
        max_length=100,
    )


class SearchContextOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summaries: list[ContextSummary] = Field(
        description="Capped summaries of relevant prior results and artifacts.",
        max_length=20,
    )


class RunSqlInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sql: str = Field(
        description="A single read-only SQL statement to execute against the scoped dataset.",
        max_length=OUTPUT_CHARACTERS,
    )


class RunSqlOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: ResultRef = Field(
        description="Reference and capped preview of the stored SQL result.",
    )


class AnalysisFunction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: AnalysisFunctionName = Field(
        description="Name of the fixed analysis function.",
    )
    description: str = Field(
        description="Purpose and limitations of the analysis function.",
        max_length=2_000,
    )
    parameter_schema: dict[str, Any] = Field(
        description="Schema describing parameters accepted by the function.",
        max_length=50,
    )


class ListAnalysisFunctionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ListAnalysisFunctionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    functions: list[AnalysisFunction] = Field(
        description="Capped list of available fixed analysis functions.",
        max_length=100,
    )


class CallAnalysisFunctionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    function_name: AnalysisFunctionName = Field(
        description="Name of the fixed analysis function to execute.",
    )
    params: dict[str, Any] = Field(
        description="Parameters for the named fixed analysis function.",
        max_length=50,
    )

    @field_validator("params")
    @classmethod
    def validate_params(cls, value: dict[str, Any]) -> dict[str, Any]:
        return reject_scope_keys(value)


class CallAnalysisFunctionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: ResultRef = Field(
        description="Reference and capped preview of the stored function result.",
    )


class GetResultPreviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: UUID = Field(
        description="ID of the stored result whose bounded preview is requested.",
    )


class GetResultPreviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: ResultRef = Field(
        description="Reference and capped preview of the requested result.",
    )


class ChartOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legend: bool = Field(
        default=True,
        description="Whether to display the chart legend.",
    )
    data_labels: bool = Field(
        default=False,
        description="Whether to display labels for chart data points.",
    )
    stacked: bool = Field(
        default=False,
        description="Whether compatible series are stacked.",
    )


class ChartConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart_type: Literal["line", "bar", "pie", "scatter", "area"] = Field(
        description="Supported chart type.",
    )
    title: str | None = Field(
        default=None,
        description="Optional chart title.",
        max_length=200,
    )
    x_column: str | None = Field(
        default=None,
        description="Optional result column plotted on the chart x-axis.",
        max_length=200,
    )
    y_columns: list[str] = Field(
        description="Result columns plotted on the chart y-axis.",
        max_length=20,
    )
    group_by: str | None = Field(
        default=None,
        description="Optional result column used to group chart series.",
        max_length=200,
    )
    options: ChartOptions = Field(
        default_factory=ChartOptions,
        description="Supported chart display options.",
    )


class CreateChartInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: UUID = Field(
        description="ID of the stored result to use when creating the chart.",
    )
    chart_config: ChartConfig = Field(
        description="Supported chart type and bounded rendering configuration.",
    )


class CreateChartOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart_id: UUID = Field(
        description="ID of the stored chart artifact.",
    )
    status: Literal["ready", "failed"] = Field(
        description="Whether chart creation completed or failed.",
    )


class ReportSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        description="Short title for this report section.",
        max_length=200,
    )
    text: str = Field(
        description="Approved narrative text for this report section.",
        max_length=5_000,
    )


class CreateReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_ids: list[UUID] = Field(
        description="IDs of stored results included in the report.",
        max_length=20,
    )
    chart_ids: list[UUID] = Field(
        description="IDs of stored charts included in the report.",
        max_length=20,
    )
    sections: list[ReportSection] = Field(
        description="Ordered approved text sections for the report.",
        max_length=20,
    )


class CreateReportOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: UUID = Field(
        description="ID of the stored structured report artifact.",
    )
    status: Literal["ready", "failed"] = Field(
        description="Whether report creation completed or failed.",
    )


class ExportResultInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: UUID = Field(
        description="ID of the stored result to export.",
    )
    format: Literal["csv", "xlsx"] = Field(
        description="File format for the exported result.",
    )


class ExportResultOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    export_id: UUID = Field(
        description="ID of the stored export artifact.",
    )
    format: Literal["csv", "xlsx"] = Field(
        description="File format of the completed export.",
    )
    status: Literal["ready", "failed"] = Field(
        description="Whether export creation completed or failed.",
    )


class SaveWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Display name for the workflow.",
        max_length=200,
    )
    analysis_record_ids: list[UUID] = Field(
        description="IDs of executed analysis records used to build the workflow.",
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        description="Optional short description of the workflow.",
        max_length=2_000,
    )
    parameters: dict[str, Any] | None = Field(
        default=None,
        description="Optional named values and defaults exposed by the workflow.",
        max_length=50,
    )

    @field_validator("parameters")
    @classmethod
    def validate_parameters(
        cls,
        value: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        return None if value is None else reject_scope_keys(value)


class SaveWorkflowOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: UUID = Field(
        description="ID of the saved workflow.",
    )
    revision_id: UUID = Field(
        description="ID of the workflow revision created or updated.",
    )
    status: Literal["saved", "failed"] = Field(
        description="Whether the workflow revision was saved or failed.",
    )


class WorkflowSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: UUID = Field(
        description="ID of the saved workflow.",
    )
    name: str = Field(
        description="Display name of the workflow.",
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        description="Short description of the workflow.",
        max_length=2_000,
    )
    revision_id: UUID = Field(
        description="ID of the workflow's current revision.",
    )


class ListWorkflowsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(
        default=20,
        description="Maximum number of workflows to return.",
        ge=1,
        le=100,
    )
    cursor: str | None = Field(
        default=None,
        description="Optional pagination cursor for the next workflow page.",
        max_length=200,
    )


class ListWorkflowsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflows: list[WorkflowSummary] = Field(
        description="Capped summaries of workflows in the scoped dataset.",
        max_length=100,
    )
    next_cursor: str | None = Field(
        default=None,
        description="Cursor for retrieving the next workflow page, if more exist.",
        max_length=200,
    )


class RunWorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: UUID = Field(
        description="ID of the workflow to execute.",
    )
    parameters: dict[str, Any] | None = Field(
        default=None,
        description="Optional named parameter values overriding workflow defaults.",
        max_length=50,
    )

    @field_validator("parameters")
    @classmethod
    def validate_parameters(
        cls,
        value: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        return None if value is None else reject_scope_keys(value)


class RunWorkflowOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_id: UUID = Field(
        description="ID of the workflow execution.",
    )
    status: Literal[
        "pending",
        "running",
        "completed",
        "failed",
    ] = Field(
        description="Current workflow execution status.",
    )
    summary: str = Field(
        description="Capped status summary for the workflow execution.",
        max_length=2_000,
    )
