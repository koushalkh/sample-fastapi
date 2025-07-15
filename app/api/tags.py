from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class ApiType(str, Enum):
    """
    Enum defining the different API types available in the system.
    This helps in categorizing APIs based on their target consumers.
    """
    UI = "ui"
    INTERNAL = "internal"
    SYSTEM = "system"  # For system endpoints like healthz, readyz
    ALL = "all"  # For APIs that are accessible to all types of consumers

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns a list of all enum values.
        """
        return [member.value for member in cls]


class ApiVersion(str, Enum):
    """
    Enum defining the API versions.
    This allows for versioning of APIs and supporting multiple versions simultaneously.
    """
    V1ALPHA1 = "v1alpha1"
    # Add future versions here as they are developed
    # V1BETA1 = "v1beta1"
    # V1 = "v1"

    @classmethod
    def values(cls) -> List[str]:
        """
        Returns a list of all enum values.
        """
        return [member.value for member in cls]


@dataclass
class Tag:
    """
    Class to represent an API tag with metadata.
    A tag helps in grouping related endpoints together and provides metadata for documentation.
    """
    name: str
    description: str
    api_type: ApiType
    api_version: Optional[ApiVersion] = None
    display_name: str = ""

    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.name.title()

    def as_dict(self) -> Dict[str, str]:
        """
        Return the tag as a dictionary for FastAPI's OpenAPI specification.
        """
        return {"name": self.name, "description": self.description}


# System level tags
HEALTHZ = Tag(
    name="healthz",
    description="Health check endpoints to verify service liveness",
    api_type=ApiType.SYSTEM,
)

READYZ = Tag(
    name="readyz",
    description="Readiness probe endpoints to verify service is ready to receive requests",
    api_type=ApiType.SYSTEM,
)

# Internal API tags with version v1alpha1
INTERNAL_ABEND_V1ALPHA1 = Tag(
    name="internal-abend-v1alpha1",
    description="Internal ABEND API endpoints (v1alpha1)",
    api_type=ApiType.INTERNAL,
    api_version=ApiVersion.V1ALPHA1,
    display_name="Internal ABEND API"
)

INTERNAL_SOP_V1ALPHA1 = Tag(
    name="internal-sop-v1alpha1",
    description="Internal SOP API endpoints (v1alpha1)",
    api_type=ApiType.INTERNAL,
    api_version=ApiVersion.V1ALPHA1,
    display_name="Internal SOP API"
)

# UI API tags with version v1alpha1
UI_ABEND_V1ALPHA1 = Tag(
    name="ui-abend-v1alpha1",
    description="UI ABEND API endpoints (v1alpha1)",
    api_type=ApiType.UI,
    api_version=ApiVersion.V1ALPHA1,
    display_name="UI ABEND API"
)

UI_SOP_V1ALPHA1 = Tag(
    name="ui-sop-v1alpha1",
    description="UI SOP API endpoints (v1alpha1)",
    api_type=ApiType.UI,
    api_version=ApiVersion.V1ALPHA1,
    display_name="UI SOP API"
)


# Add all tags to this list for easy access
ALL_TAGS = [
    HEALTHZ,
    READYZ,
    INTERNAL_ABEND_V1ALPHA1,
    INTERNAL_SOP_V1ALPHA1,
    UI_ABEND_V1ALPHA1,
    UI_SOP_V1ALPHA1
]

# Helper functions for getting tags by type, version, etc.
def get_tags_by_type(api_type: ApiType) -> List[Tag]:
    """
    Get all tags of a specific API type.
    """
    return [tag for tag in ALL_TAGS if tag.api_type == api_type]

def get_tags_by_version(api_version: ApiVersion) -> List[Tag]:
    """
    Get all tags of a specific API version.
    """
    return [tag for tag in ALL_TAGS if tag.api_version == api_version]

def get_tags_by_type_and_version(api_type: ApiType, api_version: ApiVersion) -> List[Tag]:
    """
    Get all tags of a specific API type and version.
    """
    return [tag for tag in ALL_TAGS if tag.api_type == api_type and tag.api_version == api_version]

def get_tag_names_by_type(api_type: ApiType) -> List[str]:
    """
    Get all tag names of a specific API type.
    """
    return [tag.name for tag in get_tags_by_type(api_type)]

def get_tag_dicts_for_openapi() -> List[Dict[str, str]]:
    """
    Get all tags formatted as dictionaries for FastAPI's OpenAPI specification.
    """
    return [tag.as_dict() for tag in ALL_TAGS]
