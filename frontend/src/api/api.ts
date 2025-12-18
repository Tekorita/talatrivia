/** HTTP API client for TalaTrivia backend. */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// Global handler for 401 errors
let onUnauthorized: (() => void) | null = null;

/**
 * Set the handler for 401 unauthorized errors.
 */
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

/**
 * Generic GET request.
 */
export async function get<T>(endpoint: string): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Handle 401 Unauthorized globally
      if (response.status === 401 && onUnauthorized) {
        onUnauthorized();
      }
      return {
        error: `HTTP error! status: ${response.status}`,
      };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

/**
 * Generic POST request.
 */
export async function post<T>(
  endpoint: string,
  body?: unknown
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const requestOptions: RequestInit = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    };
    
    const response = await fetch(url, requestOptions);

    if (!response.ok) {
      // Handle 401 Unauthorized globally
      if (response.status === 401 && onUnauthorized) {
        onUnauthorized();
      }
      
      // Try to parse error message from response
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // If parsing fails, use default message
      }
      return {
        error: errorMessage,
      };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    // Provide more detailed error information
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      // Log the actual error for debugging
      console.error('Fetch error:', error);
      console.error('URL:', `${API_BASE_URL}${endpoint}`);
      console.error('Body:', body);
      return {
        error: `Network error: Could not connect to ${API_BASE_URL}. Please check if the backend is running and CORS is configured correctly.`,
      };
    }
    return {
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

