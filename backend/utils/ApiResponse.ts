import { Response } from "express";

export class ApiResponse {
  static ok<T>(res: Response, data: T, message = "OK") {
    return res.status(200).json({
      success: true,
      message,
      data,
    });
  }
}
