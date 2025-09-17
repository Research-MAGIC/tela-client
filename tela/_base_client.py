from __future__ import annotations

import json
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Union,
    Mapping,
    Optional,
    cast,
    Type,
    TypeVar,
)
from typing_extensions import override
import httpx
from httpx import Response

from ._types import (
    NOT_GIVEN,
    NotGiven,
    Headers,
    Query,
    Body,
    ResponseT,
    RequestOptions,
)
from ._exceptions import (
    APIError,
    APIStatusError,
    APITimeoutError,
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from ._streaming import Stream, AsyncStream
from ._utils import is_given

if TYPE_CHECKING:
    from httpx._types import URLTypes

T = TypeVar("T")


def make_request_options(
    *,
    extra_headers: Headers | None = None,
    extra_query: Query | None = None,
    extra_body: Body | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RequestOptions:
    """Create request options from parameters"""
    return RequestOptions(
        headers=extra_headers,
        params=extra_query,
        json_data=extra_body,
        timeout=timeout,
    )


class BaseClient:
    """Base client with common functionality"""
    
    def __init__(
        self,
        *,
        base_url: str | httpx.URL,
        timeout: float | httpx.Timeout,
        max_retries: int,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        self.base_url = httpx.URL(base_url)
        self.timeout = timeout
        self.max_retries = max_retries
        self._custom_headers = dict(default_headers or {})
        self._custom_query = dict(default_query or {})
        self._strict_response_validation = _strict_response_validation
    
    @property
    def auth_headers(self) -> dict[str, str]:
        return {}
    
    @property
    def default_headers(self) -> dict[str, str | NotGiven]:
        return {
            **self._custom_headers,
            **self.auth_headers,
        }
    
    def _build_request(
        self,
        *,
        method: str,
        url: str,
        json_data: Body | None = None,
        files: Any | None = None,
        params: Query | None = None,
        headers: Headers | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> httpx.Request:
        """Build an HTTP request"""
        headers = {**self.default_headers, **(headers or {})}
        
        # Remove NotGiven values
        headers = {k: v for k, v in headers.items() if is_given(v)}
        
        # Merge query params
        params = {**self._custom_query, **(params or {})}
        
        # Build URL
        if not url.startswith(("http://", "https://")):
            # Handle relative path joining properly
            base = str(self.base_url).rstrip('/')
            path = url.lstrip('/')
            url = f"{base}/{path}"
        
        # Prepare timeout
        if timeout is None:
            timeout = self.timeout
        elif isinstance(timeout, float):
            timeout = httpx.Timeout(timeout)
        
        # When files are provided with data, use data parameter instead of json
        if files and json_data:
            return self._client.build_request(
                method=method,
                url=url,
                data=json_data,  # Use data for form fields with files
                files=files,
                params=params,
                headers=headers,
                timeout=timeout,
            )
        else:
            return self._client.build_request(
                method=method,
                url=url,
                json=json_data,
                files=files,
                params=params,
                headers=headers,
                timeout=timeout,
            )
    
    def _process_response(
        self,
        *,
        response: httpx.Response,
        stream: bool = False,
        stream_cls: Type[Stream[Any]] | Type[AsyncStream[Any]] | None = None,
    ) -> Any:
        """Process HTTP response"""
        if stream and stream_cls:
            return stream_cls(response=response, client=self)
        
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._handle_error_response(e.response)
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text
    
    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses"""
        try:
            error_data = response.json()
            message = error_data.get("error", {}).get("message", "Unknown error")
        except json.JSONDecodeError:
            message = response.text or "Unknown error"
        
        if response.status_code == 400:
            raise BadRequestError(message, response=response)
        elif response.status_code == 401:
            raise AuthenticationError(message, response=response)
        elif response.status_code == 403:
            raise PermissionDeniedError(message, response=response)
        elif response.status_code == 404:
            raise NotFoundError(message, response=response)
        elif response.status_code == 409:
            raise ConflictError(message, response=response)
        elif response.status_code == 422:
            raise UnprocessableEntityError(message, response=response)
        elif response.status_code == 429:
            raise RateLimitError(message, response=response)
        elif response.status_code >= 500:
            raise InternalServerError(message, response=response)
        else:
            raise APIStatusError(message, response=response)


class SyncAPIClient(BaseClient):
    """Synchronous API client"""
    
    _client: httpx.Client
    
    def __init__(
        self,
        *,
        base_url: str | httpx.URL,
        timeout: float | httpx.Timeout,
        max_retries: int,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.Client | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            default_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )
        
        if http_client is not None:
            self._client = http_client
        else:
            self._client = httpx.Client(
                base_url=base_url,
                timeout=timeout,
                transport=httpx.HTTPTransport(retries=max_retries),
            )
    
    def close(self) -> None:
        """Close the HTTP client"""
        self._client.close()
    
    def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT] = None,
        body: Body | None = None,
        options: RequestOptions = None,
        files: Any | None = None,
        stream: bool = False,
        stream_cls: Type[Stream[Any]] | None = None,
    ) -> ResponseT | Stream[ResponseT]:
        """Make a POST request"""
        opts = options or RequestOptions()
        
        request = self._build_request(
            method="POST",
            url=path,
            json_data=body,
            files=files,
            params=opts.params,
            headers=opts.headers,
            timeout=opts.timeout if is_given(opts.timeout) else None,
        )
        
        response = self._client.send(request, stream=stream)
        
        if stream and stream_cls:
            return stream_cls(response=response, client=self)
        
        return self._process_response(
            response=response,
            stream=stream,
            stream_cls=stream_cls,
        )
    
    async def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT] = None,
        options: RequestOptions = None,
    ) -> ResponseT:
        """Make an async GET request"""
        opts = options or RequestOptions()
        
        request = self._build_request(
            method="GET",
            url=path,
            params=opts.params,
            headers=opts.headers,
            timeout=opts.timeout if is_given(opts.timeout) else None,
        )
        
        response = await self._client.send(request)
        return self._process_response(response=response)
    
    def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT] = None,
        options: RequestOptions = None,
    ) -> ResponseT:
        """Make a GET request"""
        opts = options or RequestOptions()
        
        request = self._build_request(
            method="GET",
            url=path,
            params=opts.params,
            headers=opts.headers,
            timeout=opts.timeout if is_given(opts.timeout) else None,
        )
        
        response = self._client.send(request)
        return self._process_response(response=response)


class AsyncAPIClient(BaseClient):
    """Asynchronous API client"""
    
    _client: httpx.AsyncClient
    
    def __init__(
        self,
        *,
        base_url: str | httpx.URL,
        timeout: float | httpx.Timeout,
        max_retries: int,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            default_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )
        
        if http_client is not None:
            self._client = http_client
        else:
            self._client = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                transport=httpx.AsyncHTTPTransport(retries=max_retries),
            )
    
    async def close(self) -> None:
        """Close the HTTP client"""
        await self._client.aclose()
    
    async def post(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT] = None,
        body: Body | None = None,
        options: RequestOptions = None,
        files: Any | None = None,
        stream: bool = False,
        stream_cls: Type[AsyncStream[Any]] | None = None,
    ) -> ResponseT | AsyncStream[ResponseT]:
        """Make an async POST request"""
        opts = options or RequestOptions()
        
        request = self._build_request(
            method="POST",
            url=path,
            json_data=body,
            files=files,
            params=opts.params,
            headers=opts.headers,
            timeout=opts.timeout if is_given(opts.timeout) else None,
        )
        
        response = await self._client.send(request, stream=stream)
        
        if stream and stream_cls:
            return stream_cls(response=response, client=self)
        
        return self._process_response(
            response=response,
            stream=stream,
            stream_cls=stream_cls,
        )
    
    async def get(
        self,
        path: str,
        *,
        cast_to: Type[ResponseT] = None,
        options: RequestOptions = None,
    ) -> ResponseT:
        """Make an async GET request"""
        opts = options or RequestOptions()
        
        request = self._build_request(
            method="GET",
            url=path,
            params=opts.params,
            headers=opts.headers,
            timeout=opts.timeout if is_given(opts.timeout) else None,
        )
        
        response = await self._client.send(request)
        return self._process_response(response=response)