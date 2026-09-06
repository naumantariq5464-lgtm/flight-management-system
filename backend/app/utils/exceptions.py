from fastapi import HTTPException, status

class AppBaseException(HTTPException):
    def __init__(self, status_code: int, message: str, details: dict = None):
        super().__init__(status_code=status_code, detail={"message": message, "details": details or {}})

class NotFoundException(AppBaseException):
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message, details=details)

class ConflictException(AppBaseException):
    def __init__(self, message: str = "Resource conflict or race condition detected", details: dict = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, message=message, details=details)

class SeatUnavailableException(ConflictException):
    def __init__(self, message: str = "Selected seat is already booked or held by another customer"):
        super().__init__(message=message)

class FlightCancelledException(ConflictException):
    def __init__(self, message: str = "This flight has been cancelled. Operations are restricted."):
        super().__init__(message=message)

class BadRequestException(AppBaseException):
    def __init__(self, message: str = "Invalid request payload or business validation failed", details: dict = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message, details=details)

class UnauthorizedException(AppBaseException):
    def __init__(self, message: str = "Authentication required or credentials invalid"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message)

class ForbiddenException(AppBaseException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message)

class HoldExpiredException(ConflictException):
    def __init__(self, message: str = "The temporary seat hold has expired. Please refresh seats and try again."):
        super().__init__(message=message)
