"""Entry point for the Resume Ingestor graph.

Overview:
    * Extends :class:`BaseGraph` to build a LangGraph StateGraph.
    * Uses :class:`Resume_ingestorState` as the underlying state container.
    * Ships with a minimal start → end path that you can extend.

Guidelines:
    1. Call ``builder.add_node()`` with custom node classes.
    2. Connect nodes via ``builder.add_edge()`` or ``builder.add_conditional_edges()`` when branching.
    3. Return the compiled graph to orchestrate LangGraph execution.

Official document URL:
    - Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
    - StateGraph: https://docs.langchain.com/oss/python/langgraph/graph-api#stategraph
    - Nodes: https://docs.langchain.com/oss/python/langgraph/graph-api#nodes
    - Edges: https://docs.langchain.com/oss/python/langgraph/graph-api#edges
    - Graph API Usage: https://docs.langchain.com/oss/python/langgraph/use-graph-api
"""

from langgraph.graph import END, START, StateGraph

from casts.base_graph import BaseGraph
from casts.resume_ingestor.modules.nodes import ExtractTextNode, ParseSectionsNode
from casts.resume_ingestor.modules.state import InputState, OutputState, State


class ResumeIngestorGraph(BaseGraph):
    """Graph definition for Resume Ingestor.

    Attributes:
        input: Input schema for the graph.
        output: Output schema for the graph.
        state: State schema for the graph.
    """

    def __init__(self) -> None:
        super().__init__()
        self.input = InputState
        self.output = OutputState
        self.state = State

    def build(self):
        """Builds and compiles the graph graph.

        Returns:
            CompiledStateGraph: Compiled graph ready for execution.
        """
        builder = StateGraph(
            self.state, input_schema=self.input, output_schema=self.output
        )

        builder.add_node("extract_text", ExtractTextNode())
        builder.add_node("parse_sections", ParseSectionsNode())
        builder.add_edge(START, "extract_text")
        builder.add_edge("extract_text", "parse_sections")
        builder.add_edge("parse_sections", END)

        graph = builder.compile()
        graph.name = self.name
        return graph


resume_ingestor_graph = ResumeIngestorGraph()
