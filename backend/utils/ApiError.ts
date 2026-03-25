export class ApiError extends Error {
  statusCode: number;
  errors?: string[];

  constructor(statusCode: number, message: string, errors?: string[]) {
    super(message);
    this.statusCode = statusCode;
    this.errors = errors;
  }

  static ServiceUnavailable(message: string) {
    return new ApiError(503, message);
  }
}
