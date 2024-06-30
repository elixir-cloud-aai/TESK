"""App exceptions."""

from connexion.exceptions import (
  BadRequestProblem,
  ExtraParameterProblem,
  Forbidden,
  OAuthProblem,
  Unauthorized,
)
from werkzeug.exceptions import (
  BadRequest,
  InternalServerError,
  NotFound,
)


class ConfigNotFoundError(FileNotFoundError):
  """Configuration file not found error."""


# exceptions raised in app context
exceptions = {
  Exception: {
    "title": "Unknown error",
    "detail": "An unexpected error occurred.",
    "status": 500,
  },
  BadRequestProblem: {
    "title": "Bad request",
    "detail": "The request is malformed",
    "status": 400,
  },
  BadRequest: {
    "title": "Bad request",
    "detail": "The request is malformed.",
    "status": 400,
  },
  ExtraParameterProblem: {
    "title": "Bad request",
    "detail": "The request is malformed.",
    "status": 400,
  },
  Unauthorized: {
    "title": "Unauthorized",
    "detail": "The request is unauthorized.",
    "status": 401,
  },
  OAuthProblem: {
    "title": "Unauthorized",
    "detail": "The request is unauthorized.",
    "status": 401,
  },
  Forbidden: {
    "title": "Forbidden",
    "detail": "The requester is not authorized to perform this action.",
    "status": 403,
  },
  NotFound: {
    "title": "Not found",
    "detail": "The requested resource wasn't found.",
    "status": 404,
  },
  InternalServerError: {
    "title": "Internal server error",
    "detail": "An unexpected error occurred.",
    "status": 500,
  },
}


# exceptions raised outside of app context
class ValidationError(Exception):
  """Value or object is not compatible with required type or schema."""
