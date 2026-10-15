from fastapi import HTTPException, status

class LogSentinelException(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str = "ERROR"):
        super().__init__(status_code=status_code, detail={"message": detail, "code": code})

class NotFoundException(LogSentinelException):
    def __init__(self, resource: str, identifier: str = ""):
        detail = f"{resource} '{identifier}' not found" if identifier else f"{resource} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, code="NOT_FOUND")

class UnauthorizedException(LogSentinelException):
    def __init__(self, detail: str = "Invalid credentials or authorization header missing"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, code="UNAUTHORIZED")

class ForbiddenException(LogSentinelException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, code="FORBIDDEN")

class ConflictException(LogSentinelException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, code="CONFLICT")

class BadRequestException(LogSentinelException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, code="BAD_REQUEST")

class RateLimitException(LogSentinelException):
    def __init__(self, detail: str = "Rate limit exceeded. Please throttle requests."):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail, code="RATE_LIMITED")
