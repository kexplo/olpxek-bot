from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import AsyncIterator, Iterator
import urllib.parse

from youtube_transcript_api import NoTranscriptFound, YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from olpxek_bot.utils.llm_provider import SimpleLLMInterface

logger = logging.getLogger(__name__)


@dataclass
class Transcript:
    language: str
    language_code: str
    text: str


class YoutubeSummarizer:
    @classmethod
    def get_video_id_from_url(cls, url: str) -> str:
        if not url.startswith("http") and not url.startswith("//"):
            url = "//" + url
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.netloc == "youtu.be":
            video_id = parsed_url.path[1:]
        elif parsed_url.netloc in ["www.youtube.com", "youtube.com"]:
            video_id = urllib.parse.parse_qs(parsed_url.query)["v"][0]
        else:
            raise ValueError(f"Invalid URL: {url}")
        return video_id

    @classmethod
    def fetch_transcript(cls, url: str) -> Transcript:
        video_id = cls.get_video_id_from_url(url)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["ko", "en"])
        except NoTranscriptFound:
            logger.info(f"no manually created transcript found for {video_id}")
            pass

        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(["en", "ko"])
            except NoTranscriptFound:
                logger.info(f"no generated transcript found for {video_id}")
                raise

        formatter = TextFormatter()
        text = formatter.format_transcript(transcript.fetch())
        return Transcript(
            language=transcript.language,
            language_code=transcript.language_code,
            text=text,
        )

    def sync_summarize(
        self, url: str, llm: SimpleLLMInterface, model: str, stream: bool = False
    ) -> str | Iterator[str]:
        raise NotImplementedError

    async def async_summarize(
        self, url: str, llm: SimpleLLMInterface, model: str, stream: bool = False
    ) -> str | AsyncIterator[str]:
        transcript = self.fetch_transcript(url)

        prompt = (
            "다음은 동영상 자막입니다. 자막을 통해 영상의 내용을 요약하세요. "
            "누락 없이 핵심적인 내용만 추려서 리스트 형태로 요약하세요:\n\n"
            f"```\n{transcript.text}\n```"
        )
        logging.info(f"start summarizing {url} using {model}")
        return await llm.async_completion(model=model, prompt=prompt, stream=stream)
