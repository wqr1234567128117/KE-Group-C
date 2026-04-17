from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    ark_api_key: str = Field(default='')
    ark_base_url: str = Field(default='https://ark.cn-beijing.volces.com/api/v3')
    ark_model: str = Field(default='doubao-seed-2-0-pro-260215')
    max_image_size_mb: int = Field(default=10, alias='MAX_IMAGE_SIZE_MB')
    max_image_count: int = Field(default=8, alias='MAX_IMAGE_COUNT')
    max_text_question_count: int = Field(default=12, alias='MAX_TEXT_QUESTION_COUNT')
    max_ppt_size_mb: int = Field(default=30, alias='MAX_PPT_SIZE_MB')


@lru_cache
def get_settings() -> Settings:
    return Settings()
