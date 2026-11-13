"""Resolve a GitHub OAuth authorization code to a verified account identity."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from application.dtos.auth_dto import GitHubIdentityDTO
from application.exceptions.identity_provider_error import IdentityProviderError


class GitHubOAuthIdentityVerifier:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def verify(self, authorization_code: str) -> GitHubIdentityDTO:
        token_payload = self._request_json(
            "https://github.com/login/oauth/access_token",
            data=urlencode({
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": authorization_code,
                "redirect_uri": self.redirect_uri,
            }).encode(),
            accept="application/json",
        )
        if not isinstance(token_payload, dict):
            raise IdentityProviderError("GitHub authorization could not be verified.")
        access_token = token_payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise IdentityProviderError("GitHub authorization could not be verified.")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "TODO-App",
        }
        profile = self._request_json("https://api.github.com/user", headers=headers)
        emails = self._request_json("https://api.github.com/user/emails", headers=headers)
        if not isinstance(profile, dict) or not isinstance(emails, list):
            raise IdentityProviderError("GitHub account information could not be verified.")
        email = next(
            (
                item.get("email")
                for item in emails
                if item.get("primary") is True and item.get("verified") is True
            ),
            None,
        )
        subject = profile.get("id")
        if not isinstance(subject, (int, str)) or not email:
            raise IdentityProviderError(
                "GitHub must provide a primary verified email address to sign in."
            )
        return GitHubIdentityDTO(str(subject), email)

    @staticmethod
    def _request_json(url: str, data: bytes | None = None, headers: dict | None = None, accept: str | None = None) -> dict | list:
        request_headers = {"User-Agent": "TODO-App"}
        if headers:
            request_headers.update(headers)
        if accept:
            request_headers["Accept"] = accept
        if data is not None:
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = Request(url, data=data, headers=request_headers)
        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read())
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise IdentityProviderError(
                "GitHub sign-in could not be completed. Please try again."
            ) from exc
