"""
Pydantic models for Plex API data validation.

This module provides type-safe models for Plex API requests and responses,
enabling validation, serialization, and documentation of data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PlexLibrary(BaseModel):
    """Model for a Plex library section."""

    key: str = Field(..., description="Library ID/key")
    title: str = Field(..., description="Library name")
    type: str = Field(..., description="Library type (movie, show, artist, photo)")
    agent: str = Field(..., description="Metadata agent")
    scanner: str = Field(..., description="Scanner type")
    language: str = Field(..., description="Library language")
    uuid: str = Field(..., description="Library UUID")
    updated_at: int = Field(..., alias="updatedAt", description="Last update timestamp")
    created_at: int = Field(..., alias="createdAt", description="Creation timestamp")
    scanned_at: Optional[int] = Field(None, alias="scannedAt", description="Last scan timestamp")
    content: Optional[bool] = Field(None, description="Has content")
    directory: Optional[bool] = Field(None, description="Is directory")
    content_changed_at: Optional[int] = Field(None, alias="contentChangedAt", description="Content change timestamp")
    hidden: Optional[int] = Field(None, description="Hidden flag")
    location: Optional[List[Dict[str, Any]]] = Field(None, alias="Location", description="Library locations")

    class Config:
        populate_by_name = True


class PlexMediaItem(BaseModel):
    """Model for a generic Plex media item (movie, episode, track)."""

    rating_key: str = Field(..., alias="ratingKey", description="Unique rating key")
    key: str = Field(..., description="Media item key/path")
    guid: Optional[str] = Field(None, description="Global unique identifier")
    studio: Optional[str] = Field(None, description="Studio")
    type: str = Field(..., description="Media type (movie, episode, track, etc.)")
    title: str = Field(..., description="Media title")
    title_sort: Optional[str] = Field(None, alias="titleSort", description="Sort title")
    content_rating: Optional[str] = Field(None, alias="contentRating", description="Content rating")
    summary: Optional[str] = Field(None, description="Media summary/description")
    rating: Optional[float] = Field(None, description="User/audience rating")
    audience_rating: Optional[float] = Field(None, alias="audienceRating", description="Audience rating")
    year: Optional[int] = Field(None, description="Release year")
    tagline: Optional[str] = Field(None, description="Tagline")
    thumb: Optional[str] = Field(None, description="Thumbnail path")
    art: Optional[str] = Field(None, description="Background art path")
    duration: Optional[int] = Field(None, description="Duration in milliseconds")
    originally_available_at: Optional[str] = Field(None, alias="originallyAvailableAt", description="Original air date")
    added_at: int = Field(..., alias="addedAt", description="Date added timestamp")
    updated_at: int = Field(..., alias="updatedAt", description="Last update timestamp")
    audience_rating_image: Optional[str] = Field(None, alias="audienceRatingImage", description="Audience rating image")
    primary_extra_key: Optional[str] = Field(None, alias="primaryExtraKey", description="Primary extra key")
    rating_image: Optional[str] = Field(None, alias="ratingImage", description="Rating image")
    view_count: Optional[int] = Field(0, alias="viewCount", description="Number of times viewed")
    last_viewed_at: Optional[int] = Field(None, alias="lastViewedAt", description="Last viewed timestamp")

    # TV Show specific fields
    parent_rating_key: Optional[str] = Field(None, alias="parentRatingKey", description="Parent rating key (for episodes)")
    grandparent_rating_key: Optional[str] = Field(None, alias="grandparentRatingKey", description="Grandparent rating key (for episodes)")
    parent_title: Optional[str] = Field(None, alias="parentTitle", description="Parent title (season)")
    grandparent_title: Optional[str] = Field(None, alias="grandparentTitle", description="Grandparent title (show)")
    index: Optional[int] = Field(None, description="Episode/track number")
    parent_index: Optional[int] = Field(None, alias="parentIndex", description="Season number")

    # Media and genre information
    media: Optional[List[Dict[str, Any]]] = Field(None, alias="Media", description="Media information")
    genre: Optional[List[Dict[str, Any]]] = Field(None, alias="Genre", description="Genres")
    director: Optional[List[Dict[str, Any]]] = Field(None, alias="Director", description="Directors")
    writer: Optional[List[Dict[str, Any]]] = Field(None, alias="Writer", description="Writers")
    role: Optional[List[Dict[str, Any]]] = Field(None, alias="Role", description="Cast/roles")

    class Config:
        populate_by_name = True


class PlexSession(BaseModel):
    """Model for a currently playing Plex session."""

    session_key: str = Field(..., alias="sessionKey", description="Session key")
    user: Dict[str, Any] = Field(..., alias="User", description="User information")
    player: Dict[str, Any] = Field(..., alias="Player", description="Player information")
    view_offset: int = Field(0, alias="viewOffset", description="Current playback position in milliseconds")

    # Include the media item being played
    rating_key: Optional[str] = Field(None, alias="ratingKey", description="Media rating key")
    key: Optional[str] = Field(None, description="Media key")
    title: Optional[str] = Field(None, description="Media title")
    type: Optional[str] = Field(None, description="Media type")
    thumb: Optional[str] = Field(None, description="Thumbnail")
    duration: Optional[int] = Field(None, description="Total duration in milliseconds")

    class Config:
        populate_by_name = True


class PlexServerIdentity(BaseModel):
    """Model for Plex server identity information."""

    machine_identifier: str = Field(..., alias="machineIdentifier", description="Unique machine identifier")
    version: str = Field(..., description="Plex Media Server version")
    my_plex: Optional[bool] = Field(None, alias="myPlex", description="Connected to Plex.tv")
    my_plex_username: Optional[str] = Field(None, alias="myPlexUsername", description="Plex.tv username")
    my_plex_mapping_state: Optional[str] = Field(None, alias="myPlexMappingState", description="Plex.tv mapping state")
    my_plex_signin_state: Optional[str] = Field(None, alias="myPlexSigninState", description="Plex.tv signin state")
    platform: str = Field(..., description="Server platform")
    platform_version: str = Field(..., alias="platformVersion", description="Platform version")
    friendly_name: Optional[str] = Field(None, alias="friendlyName", description="Friendly server name")
    size: Optional[int] = Field(None, alias="size", description="Directory size")
    allow_camera_upload: Optional[bool] = Field(None, alias="allowCameraUpload", description="Allow camera upload")
    allow_channel_access: Optional[bool] = Field(None, alias="allowChannelAccess", description="Allow channel access")
    allow_media_deletion: Optional[bool] = Field(None, alias="allowMediaDeletion", description="Allow media deletion")
    allow_sharing: Optional[bool] = Field(None, alias="allowSharing", description="Allow sharing")
    allow_sync: Optional[bool] = Field(None, alias="allowSync", description="Allow sync")
    allow_tuners: Optional[bool] = Field(None, alias="allowTuners", description="Allow tuners")
    background_processing: Optional[bool] = Field(None, alias="backgroundProcessing", description="Background processing enabled")
    certificate: Optional[bool] = Field(None, alias="certificate", description="Has certificate")
    companion_proxy: Optional[bool] = Field(None, alias="companionProxy", description="Companion proxy enabled")
    diagnostics: Optional[str] = Field(None, alias="diagnostics", description="Diagnostics")
    event_stream: Optional[bool] = Field(None, alias="eventStream", description="Event stream enabled")
    hub_search: Optional[bool] = Field(None, alias="hubSearch", description="Hub search enabled")
    item_clusters: Optional[bool] = Field(None, alias="itemClusters", description="Item clusters enabled")
    multiuser: Optional[bool] = Field(None, alias="multiuser", description="Multiuser enabled")
    photo_auto_tag: Optional[bool] = Field(None, alias="photoAutoTag", description="Photo auto-tagging enabled")
    plugin_host: Optional[bool] = Field(None, alias="pluginHost", description="Plugin host enabled")
    push_notifications: Optional[bool] = Field(None, alias="pushNotifications", description="Push notifications enabled")
    read_only_libraries: Optional[bool] = Field(None, alias="readOnlyLibraries", description="Read-only libraries enabled")
    streaming_brain_abr_version: Optional[int] = Field(None, alias="streamingBrainABRVersion", description="Streaming brain ABR version")
    streaming_brain_version: Optional[int] = Field(None, alias="streamingBrainVersion", description="Streaming brain version")
    sync: Optional[bool] = Field(None, alias="sync", description="Sync enabled")
    transcoder_active_video_sessions: Optional[int] = Field(None, alias="transcoderActiveVideoSessions", description="Active transcode sessions")
    transcoder_audio: Optional[bool] = Field(None, alias="transcoderAudio", description="Audio transcoding available")
    transcoder_lyrics: Optional[bool] = Field(None, alias="transcoderLyrics", description="Lyrics transcoding available")
    transcoder_photo: Optional[bool] = Field(None, alias="transcoderPhoto", description="Photo transcoding available")
    transcoder_subtitles: Optional[bool] = Field(None, alias="transcoderSubtitles", description="Subtitle transcoding available")
    transcoder_video: Optional[bool] = Field(None, alias="transcoderVideo", description="Video transcoding available")
    transcoder_video_bitrates: Optional[str] = Field(None, alias="transcoderVideoBitrates", description="Video transcoding bitrates")
    transcoder_video_qualities: Optional[str] = Field(None, alias="transcoderVideoQualities", description="Video transcoding qualities")
    transcoder_video_resolutions: Optional[str] = Field(None, alias="transcoderVideoResolutions", description="Video transcoding resolutions")
    updated_at: Optional[int] = Field(None, alias="updatedAt", description="Last update timestamp")
    updater: Optional[bool] = Field(None, alias="updater", description="Updater enabled")
    voice_search: Optional[bool] = Field(None, alias="voiceSearch", description="Voice search enabled")

    class Config:
        populate_by_name = True


class PlexHistoryRecord(BaseModel):
    """Model for a Plex watch history record."""

    history_key: Optional[str] = Field(None, alias="historyKey", description="History key")
    key: Optional[str] = Field(None, description="Media key")
    rating_key: Optional[str] = Field(None, alias="ratingKey", description="Media rating key")
    title: Optional[str] = Field(None, description="Media title")
    type: Optional[str] = Field(None, description="Media type")
    thumb: Optional[str] = Field(None, description="Thumbnail")
    parent_thumb: Optional[str] = Field(None, alias="parentThumb", description="Parent thumbnail")
    grandparent_thumb: Optional[str] = Field(None, alias="grandparentThumb", description="Grandparent thumbnail")
    grandparent_title: Optional[str] = Field(None, alias="grandparentTitle", description="Show title")
    viewed_at: Optional[int] = Field(None, alias="viewedAt", description="Viewed timestamp")
    account_id: Optional[int] = Field(None, alias="accountID", description="Account ID")
    device_id: Optional[int] = Field(None, alias="deviceID", description="Device ID")

    class Config:
        populate_by_name = True


class ErrorResponse(BaseModel):
    """Model for error responses from Plex API."""

    status: bool = Field(default=False, description="Status (always False for errors)")
    error: str = Field(..., description="Error message")
    message: Optional[str] = Field(None, description="Additional error message")
    status_code: Optional[int] = Field(None, alias="statusCode", description="HTTP status code")

    class Config:
        populate_by_name = True
