// API response types
export interface ApiResponse<T = any> {
  status: string;
  data?: T;
  message?: string;
}

export interface ErrorResponse {
  detail: string;
}