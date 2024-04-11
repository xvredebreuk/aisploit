from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser

from ..core import BaseTarget, Response, BasePromptValue


class LangchainTarget(BaseTarget):
    def __init__(self, *, model: BaseLanguageModel) -> None:
        self._model = model

    def send_prompt(self, prompt: BasePromptValue) -> Response:
        response = self._model.invoke(prompt)

        if isinstance(response, str):
            return Response(content=response)

        if isinstance(response, BaseMessage):
            parser = StrOutputParser()
            return Response(content=parser.invoke(response))

        raise ValueError(f"Unsupported cache value {type(response)}")
