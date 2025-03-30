import json
from inspect import signature
from time import sleep, time
import asyncio

import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import ResourceExhausted

from lib.modules.paths import Path, PathLike, PurePath
from lib.modules.display import Logger

from lib.config import Paths
from lib import utils
from .security import auth


'''def python_schema_to_json(response_schema: dict) -> dict:
    """
    Converts a Python-compatible schema to a JSON-compatible schema.

    Args:
        response_schema (dict): The schema defined in Python enums.

    Returns:
        dict: The schema converted into JSON-compatible format.
    """
    response_schema = response_schema.copy()
    for k, v in response_schema.items():
        if isinstance(v, dict):
            response_schema[k] = python_schema_to_json(v)
        elif k != 'required':
            response_schema[k] = v.name.lower()
    return response_schema

def json_schema_to_python(response_schema: dict) -> dict:
    """
    Converts a JSON-compatible schema to a Python-compatible schema.

    Args:
        response_schema (dict): The schema defined in JSON format.

    Returns:
        dict: The schema converted into Python enums.
    """
    response_schema = response_schema.copy()
    for k, v in response_schema.items():
        if isinstance(v, dict):
            response_schema[k] = json_schema_to_python(v)
        elif k != 'required':
            v: str
            response_schema[k] = eval(f'content.Type.{v.upper()}')
    return response_schema'''


class MODE:
    class VIDEODATA:
        def IN(
            source: str | None,
            author: str | None,
            title: str | None = None,
            description: str | None = None,
            publication_date: str | None = None,
            hashtags: list[str] | None = None,
            comms: list[str] | None = None,
            timeline: list[tuple[int, int]] | None = None,
            context_prompt: str = "",
            **k
        ) -> str:
            prompt = f"Analyse this video as usual.\n{context_prompt}"
            if title or description or publication_date or hashtags or comms or timeline:
                prompt += f"\nTo help you, Here is some information that I was able to extract from the video posted on {source if source else 'social medias'}:\n"
                if author: prompt += f"    - Author: {author}\n"
                if title: prompt += f"    - Title: {utils.reduce_text(title, max_len=100)}\n"
                if description: prompt += f"    - Description: {utils.reduce_text(description, max_len=300)}\n"
                if publication_date: prompt += f"    - Publication date: {publication_date}\n"
                if hashtags: prompt += f"    - Hashtag(s): #{', #'.join(hashtags[:10])}\n"
                if comms: prompt += f"    - Comment(s): « {' », « '.join(comms[:10])} »\n"
                if timeline:
                    prompt += (f"I know there is a total of {len(timeline)} scenes to analyse."
                                " You must strictly identify all of them and give the analysis found for each of them, precisely respecting the following timelines:\n")
                    for i, (t_start, t_end) in enumerate(timeline):
                        prompt += f"    - Scene {i}: ({round(t_start, 3)} - {round(t_end, 3)}) s\n"
            return prompt

        def OUT(**k) -> utils.JSONType:
            return {
                "type": content.Type.OBJECT,
                "properties": {
                    "analysis": {
                        "type": content.Type.STRING
                    },
                    "scenes_data": {
                        "type": content.Type.ARRAY,
                        "items": {
                            "type": content.Type.OBJECT,
                            "properties": {
                                "analysis": {
                                    "type": content.Type.STRING
                                },
                                "timeline": {
                                    "type": content.Type.OBJECT,
                                    "properties": {
                                        "t_start": {
                                            "type": content.Type.NUMBER
                                        },
                                        "t_end": {
                                            "type": content.Type.NUMBER
                                        }
                                    },
                                    "required": [
                                        "t_start",
                                        "t_end"
                                    ]
                                }
                            },
                            "required": [
                                "analysis",
                                "timeline"
                            ]
                        }
                    },
                    "keywords": {
                        "type": content.Type.ARRAY,
                        "items": {
                            "type": content.Type.STRING
                        }
                    }
                },
                "required": [
                    "analysis",
                    "scenes_data",
                    "keywords"
                ]
            }

    class SCENEPACK:
        def IN(
            source: str | None,
            author: str | None,
            title: str | None = None,
            description: str | None = None,
            publication_date: str | None = None,
            hashtags: list[str] | None = None,
            comms: list[str] | None = None,
            timeline: list[tuple[int, int]] | None = None,
            context_prompt: str = '',
            **k
        ) -> str:
            prompt = f"Analyse this video as usual.\n{context_prompt}"
            if title or description or publication_date or hashtags or comms or timeline:
                prompt += f"\nTo help you, Here is some information that I was able to extract from the video posted on {source if source else 'social medias'}:\n"
                if author: prompt += f"    - Author: {author}\n"
                if title: prompt += f"    - Title: {utils.reduce_text(title, max_len=100)}\n"
                if description: prompt += f"    - Description: {utils.reduce_text(description, max_len=300)}\n"
                if publication_date: prompt += f"    - Publication date: {publication_date}\n"
                if hashtags: prompt += f"    - Hashtag(s): #{', #'.join(hashtags[:10])}\n"
                if comms: prompt += f"    - Comment(s): « {' », « '.join(comms[:10])} »\n"
                if timeline:
                    prompt += (f"I know there is a total of {len(timeline)} scenes to analyse."
                                " You must strictly identify all of them and give the analysis found for each of them, precisely respecting the following timelines:\n")
                    for i, (t_start, t_end) in enumerate(timeline):
                        prompt += f"    - Scene {i}: ({round(t_start, 3)} - {round(t_end, 3)}) s\n"
            return prompt

        def OUT(**k) -> utils.JSONType:
            return {
                "type": content.Type.OBJECT,
                "properties": {
                    "analysis": {
                        "type": content.Type.STRING
                    },
                    "scenes_data": {
                        "type": content.Type.ARRAY,
                        "items": {
                            "type": content.Type.OBJECT,
                            "properties": {
                                "analysis": {
                                    "type": content.Type.STRING
                                },
                                "timeline": {
                                    "type": content.Type.OBJECT,
                                    "properties": {
                                        "t_start": {
                                            "type": content.Type.NUMBER
                                        },
                                        "t_end": {
                                            "type": content.Type.NUMBER
                                        }
                                    },
                                    "required": [
                                        "t_start",
                                        "t_end"
                                    ]
                                }
                            },
                            "required": [
                                "analysis",
                                "timeline"
                            ]
                        }
                    },
                    "keywords": {
                        "type": content.Type.ARRAY,
                        "items": {
                            "type": content.Type.STRING
                        }
                    }
                },
                "required": [
                    "analysis",
                    "scenes_data",
                    "keywords"
                ]
            }

    class MYVIDEO:
        def IN(
            analysis_prediction: str | None = None,
            scenes_predictions: list[dict[str | dict[str, float]]] | None = None,
            context_prompt: str = '',
            **k
        ) -> str:
            prompt = f"Analyse this video as usual.\n{context_prompt}"
            scenes_predictions = [sp for sp in scenes_predictions if sp]   # Clean empty predictions
            if analysis_prediction or scenes_predictions:
                prompt += f"\nTo help you, Here is some information about the video:\n"
                if analysis_prediction: prompt += f"I can make the prediction that the video analysis will look like this: '{analysis_prediction}' It can be wrong however.\n"
                if scenes_predictions:
                    prompt += (f"I can make the prediction that the video has a total of {len(scenes_predictions)} scenes to analyse."
                                " Try to identify them and give an analysis for each of them, trying to follow the predicted scenes analysis and timelines:\n")
                    prev_t_start = 0
                    for i, scene_prediction in enumerate(scenes_predictions):
                        prompt += f"    - Scene {i}:\n"
                        if len(scene_prediction.get('timeline', [])) == 2:
                            t_start, t_end = tuple(scene_prediction['timeline'].values())
                            if float(t_start) > float(t_end):   # Swap t_start, t_end if inversed
                                t_start, t_end = t_end, t_start
                            if i == 0:
                                assert t_start == 0, 'Invalid parameter: timeline must start by 0'
                            assert t_end >= prev_t_start, 'Invalid parameter: timeline must be filled'
                            prompt += f"        - Timeline predicted: ({t_start} - {t_end}) seconds\n"
                        if scene_prediction.get('analysis'):
                            prompt += f"        - Analysis predicted: {scene_prediction['analysis']}\n"
                prompt += "This is only predictions made based on what type of videos the author usually make, it can be totaly different."
            return prompt

        def OUT(**k) -> utils.JSONType:
            return {
                "type": content.Type.OBJECT,
                "properties": {
                    "analysis": {
                        "type": content.Type.STRING
                    },
                    "scenes_data": {
                        "type": content.Type.ARRAY,
                        "items": {
                            "type": content.Type.OBJECT,
                            "properties": {
                                "analysis": {
                                    "type": content.Type.STRING
                                },
                                "timeline": {
                                    "type": content.Type.OBJECT,
                                    "properties": {
                                        "t_start": {
                                            "type": content.Type.NUMBER
                                        },
                                        "t_end": {
                                            "type": content.Type.NUMBER
                                        }
                                    },
                                    "required": [
                                        "t_start",
                                        "t_end"
                                    ]
                                }
                            },
                            "required": [
                                "analysis",
                                "timeline"
                            ]
                        }
                    },
                    "keywords": {
                        "type": content.Type.ARRAY,
                        "items": {
                            "type": content.Type.STRING
                        }
                    }
                },
                "required": [
                    "analysis",
                    "scenes_data",
                    "keywords"
                ]
            }


class VideoAnalyst:
    """
    A class to analyze video files using the Gemini 1.5 Pro API.
    """

    MODE = MODE
    logger = Logger('[VideoAnalyst]')
    DEFAULT_UPLOAD_TIME = 10.0
    api_key_tracker: dict[str, float] = {}
    _ins: dict = {'ins': None, 'params': None}

    def __new__(cls, *args, **kwargs) -> 'VideoAnalyst':
        bound_args = signature(cls.__init__).bind(None, *args, **kwargs)
        bound_args.apply_defaults()
        # Remove 'self' from the arguments
        params = dict(bound_args.arguments)
        params.pop('self')

        if cls._ins['ins'] is None or cls._ins['params'] != params:
            if cls._ins['ins'] is not None:
                cls._ins['ins'].close()

            cls._ins = {
                'ins': super().__new__(cls),
                'params': params
            }
        return cls._ins['ins']

    def __init__(self,
            initial_api_key: str | None = None,
            response_schema: utils.JSONType | None = None,
            default_query: str = "Analyse this video as usual.",
            max_retries: int = 1,
            auth_save: bool = True
        ):
        """
        Initializes the VideoAnalyst instance.

        Ensures that a valid API key is available. If none is found,
        logs an error.
        """
        self.api_key = (auth.get_valid_key(initial_api_key, raise_error=True))

        if auth_save:
            auth.set_auto_save()
        else:
            auth.set_no_auto_save()

        self.default_query = default_query
        self.response_schema = response_schema or MODE.VIDEODATA.OUT()
        self.max_retries = max_retries
        self.errors_count = 0
        self.model: genai.GenerativeModel = None
        self.chat: genai.ChatSession = None
    
    def set_response_schema(self, response_schema: utils.JSONType) -> None:
        self.response_schema = response_schema

    def set_default_query(self, default_query: str) -> None:
        self.default_query = default_query

    def login(self) -> None:
        """
        Authenticates with the Gemini API and configures the generative model.

        Loads safety settings, response schema, and system instructions.
        """
        if self.model is None:
            self.errors_count = 0
            utils.assert_is_json_serializable(self.response_schema)
            self.logger.info('Connecting to gemini api...')

            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-pro-exp-02-05",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
                },
                generation_config={
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                    "response_schema": self.response_schema,
                    "response_mime_type": "application/json"
                },
                system_instruction=Paths('lib/analysts/video/system_instruction.txt').read(default='')
            )
            self.logger.info(f'Connected successfully with api key: {self.api_key}')

    def switch_api(self) -> None:
        """
        Switches to a new API key and reconfigures the generative model.

        Marks the current API key as invalid to prevent reuse.
        """
        self.logger.info('Switching account')
        auth.rotate_key(self.api_key)
        self.api_key = auth.get_valid_key(raise_error=True)
        genai.configure(api_key=self.api_key)

    def start_chat(self, history: dict | None = None) -> None:
        """
        Starts a new chat session with the Gemini API.

        Args:
            history (dict | None): Optional conversation history to initialize
                                   the chat session.
        """
        self.logger.info('Starting new conversation')
        self.chat = self.model.start_chat(history=history)
    
    @property
    def history(self) -> list[genai.protos.Content]:
        return self.chat.history

    @classmethod
    def upload_file(cls, file_path: PathLike) -> genai.protos.File:
        file_path = Path(file_path, 'File', assert_exists=True)
        cls.logger.info(f"Uploading file: {file_path.relative}")
        return genai.upload_file(file_path)

    def wait_file(self, file: genai.protos.File, sleep_time: float | None = None) -> None:
        """
        Waits for uploaded files to be processed and become ACTIVE.

        Args:
            files (list): A list of uploaded file objects.

        Raises:
            ConnectionError: If any file fails to become ACTIVE.
        """
        sleep_time = sleep_time or self.DEFAULT_UPLOAD_TIME
        self.logger.info(f"Processing file: {file.display_name}...")
        while file.state.name == "PROCESSING":
            print(". ", end="", flush=True)
            sleep(sleep_time)
            file = genai.get_file(file.name)
            sleep_time = max(sleep_time, self.DEFAULT_UPLOAD_TIME)
        if file.state.name != "ACTIVE":
            raise ConnectionError(f"File {file.display_name} failed to process")
        self.logger.info(f"File {file.display_name} active.")

    async def wait_file_async(self, file: genai.protos.File, sleep_time: float | None = None) -> None:
        """
        Asynchronous version of wait_file.

        Args:
            files (list): A list of uploaded file objects.

        Raises:
            ConnectionError: If any file fails to become ACTIVE.
        """
        sleep_time = sleep_time or self.DEFAULT_UPLOAD_TIME
        self.logger.info(f"Processing file: {file.display_name}...")
        while file.state.name == "PROCESSING":
            print(". ", end="", flush=True)
            await asyncio.sleep(sleep_time)
            file = genai.get_file(file.name)
            sleep_time = max(sleep_time, self.DEFAULT_UPLOAD_TIME)
        if file.state.name != "ACTIVE":
            raise ConnectionError(f"File {file.display_name} failed to process")
        self.logger.info(f"File {file.display_name} active.")

    def update_errors_count(self, increase_value: int = 0) -> None:
        self.errors_count += increase_value
        if self.errors_count > self.max_retries:
            raise RuntimeError(f'Max reties of {self.max_retries} exceeded')

    def analyze(self,
        video: PathLike | genai.protos.File,
        query: str | None = None,
        sleep_time: float | None = None,
        response_delay_limit: float = 180.0,
        increment_key_usage: bool = True,
        rotate_key: bool = True
    ) -> dict:
        """
        Uploads a video and analyzes it using the Gemini API.

        Args:
            video (PathLike): Path to the video file.

        Returns:
            dict: The structured JSON response from the API.

        Raises:
            ResourceExhausted: If the API quota is exceeded.
        """
        auth.is_valid_key(self.api_key, raise_error=True)

        if isinstance(video, (PurePath, str)):
            video = Path(video, 'File', assert_exists=True)
            self.logger.info(f'Analyzing video: {video.relative}...')
        else:
            self.logger.info(f'Analyzing video: {video.display_name}...')

        while time() - self.api_key_tracker.get(self.api_key, 0) <= auth.RPM_QUOTA * 60:
            sleep(0.01)

        query = query or self.default_query
        self.logger.info(f'Asking: {query}')

        while True:
            try:
                uploaded_file = self.upload_file(video.fs) if isinstance(video, (PurePath, str)) else video

                async def process_video():
                    await self.wait_file_async(uploaded_file, sleep_time)
                    return await self.chat.send_message_async([uploaded_file, query])

                response = asyncio.run(asyncio.wait_for(
                    process_video(),
                    timeout=response_delay_limit
                ))

                self.api_key_tracker[self.api_key] = time()
                if increment_key_usage:
                    auth.increment_key_usage(self.api_key)
                if rotate_key:
                    self.switch_api()

            except ResourceExhausted as e:
                self.logger.error(f'Error analyzing video: {video.relative if isinstance(video, (PurePath, str)) else video.display_name}', skippable=True, base_error=e)
                self.update_errors_count(1)
                self.logger.info('Retrying...')
            else:
                self.logger.info(f'Video: {video.relative if isinstance(video, (PurePath, str)) else video.display_name} analyzed successfully')
                text = response.text
                try:
                    out = json.loads(text)
                except json.JSONDecodeError:
                    out = text
                return out

    async def analyze_async(self,
        video: PathLike | genai.protos.File,
        query: str | None = None,
        sleep_time: float | None = None,
        response_delay_limit: float = 180.0,
        increment_key_usage: bool = True,
        rotate_key: bool = True
    ) -> dict:
        """
        Asynchronous version of analyze.

        Args:
            video (PathLike): Path to the video file.
            query (str | None): Query to send to the model
            sleep_time (float | None): Time to wait between upload status checks
            response_delay_limit (float): Maximum time in seconds to wait for response

        Returns:
            dict: The structured JSON response from the API.

        Raises:
            ResourceExhausted: If the API quota is exceeded.
            TimeoutError: If the response takes longer than response_delay_limit
        """
        auth.is_valid_key(self.api_key, raise_error=True)

        if isinstance(video, (PurePath, str)):
            video = Path(video, 'File', assert_exists=True)
            self.logger.info(f'Analyzing video: {video.relative}...')
        else:
            self.logger.info(f'Analyzing video: {video.display_name}...')

        while time() - self.api_key_tracker.get(self.api_key, 0) <= auth.RPM_QUOTA * 60:
            await asyncio.sleep(0.01)

        query = query or self.default_query
        self.logger.info(f'Asking: {query}')

        while True:
            try:
                uploaded_file = self.upload_file(video.fs) if isinstance(video, (PurePath, str)) else video
                
                async with asyncio.timeout(response_delay_limit):
                    await self.wait_file_async(uploaded_file, sleep_time)
                    response = await self.chat.send_message_async([uploaded_file, query])
                
                self.api_key_tracker[self.api_key] = time()
                if increment_key_usage:
                    auth.increment_key_usage(self.api_key)
                if rotate_key:
                    self.switch_api()

            except asyncio.TimeoutError:
                raise TimeoutError(f"Analysis took longer than {response_delay_limit} seconds")
            except ResourceExhausted as e:
                self.logger.error(f'Error analyzing video: {video.relative if isinstance(video, (PurePath, str)) else video.display_name}', skippable=True, base_error=e)
                self.update_errors_count(1)
                self.logger.info('Retrying...')
            else:
                self.logger.info(f'Video: {video.relative if isinstance(video, (PurePath, str)) else video.display_name} analyzed successfully')
                text = response.text
                try:
                    out = json.loads(text)
                except json.JSONDecodeError:
                    out = text
                return out

    def close(self) -> None:
        self.chat = None
        self.model = None

    def __enter__(self) -> 'VideoAnalyst':
        """Enter context with auto login and chat creation"""
        self.login()
        self.start_chat()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context"""
        self.close()
    