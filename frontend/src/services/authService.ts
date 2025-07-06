// ================================================================
// SIMPLIFIED AUTHENTICATION SERVICE
// Tony WhatsApp Assistant - Frontend Authentication
// ================================================================

// Simple JWT decode without external dependencies
function simpleJwtDecode(token: string): any {
  try {
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload));
    return decoded;
  } catch (error) {
    console.error('JWT decode error:', error);
    return null;
  }
}

// Simple encryption using btoa/atob for basic security
function simpleEncrypt(text: string, key: string): string {
  return btoa(text + key);
}

function simpleDecrypt(encryptedText: string, key: string): string {
  try {
    const decoded = atob(encryptedText);
    return decoded.replace(key, '');
  } catch (error) {
    return '';
  }
}

// Types
interface AuthUser {
  id: string;
  username: string;
  email: string;
  roles: string[];
  permissions: string[];
  avatar?: string;
  firstName?: string;
  lastName?: string;
  lastLogin?: Date;
  isActive: boolean;
}

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  scope?: string;
}

interface LoginCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
}

// Constants
const TOKEN_STORAGE_KEY = 'tony_auth_tokens';
const USER_STORAGE_KEY = 'tony_user_data';
const REFRESH_TOKEN_KEY = 'tony_refresh_token';
const CSRF_TOKEN_KEY = 'tony_csrf_token';
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes

class AuthService {
  private sessionTimeout: number | null = null;
  private refreshTokenTimeout: number | null = null;
  private csrfToken: string = '';
  
  constructor() {
    this.generateCSRFToken();
    this.setupSessionTimeout();
  }
  
  // ================================================================
  // INITIALIZATION
  // ================================================================
  
  private generateCSRFToken(): void {
    this.csrfToken = Math.random().toString(36).substring(2, 15) + 
                     Math.random().toString(36).substring(2, 15);
    localStorage.setItem(CSRF_TOKEN_KEY, this.csrfToken);
  }
  
  // ================================================================
  // AUTHENTICATION METHODS
  // ================================================================
  
  async login(credentials: LoginCredentials): Promise<AuthUser> {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': this.csrfToken
        },
        body: JSON.stringify(credentials)
      });
      
      if (!response.ok) {
        throw new Error('Login failed');
      }
      
      const data = await response.json();
      
      // Store tokens securely
      this.storeTokens(data.tokens);
      
      // Decode and validate JWT
      const user = this.decodeAndValidateToken(data.tokens.accessToken);
      
      // Store user data
      this.storeUserData(user);
      
      // Setup auto-refresh
      this.setupTokenRefresh(data.tokens.expiresIn);
      
      // Reset session timeout
      this.resetSessionTimeout();
      
      return user;
      
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }
  
  async logout(): Promise<void> {
    try {
      // Clear local storage
      this.clearAuthData();
      
      // Clear timeouts
      this.clearTimeouts();
      
      // Notify backend
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'X-CSRF-Token': this.csrfToken
        }
      });
      
    } catch (error) {
      console.error('Logout error:', error);
      // Continue with logout even if backend call fails
    }
  }
  
  async refreshToken(): Promise<AuthTokens | null> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': this.csrfToken
        },
        body: JSON.stringify({ refreshToken })
      });
      
      if (!response.ok) {
        throw new Error('Token refresh failed');
      }
      
      const data = await response.json();
      
      // Store new tokens
      this.storeTokens(data.tokens);
      
      // Setup next refresh
      this.setupTokenRefresh(data.tokens.expiresIn);
      
      return data.tokens;
      
    } catch (error) {
      console.error('Token refresh error:', error);
      // Force logout on refresh failure
      this.logout();
      throw error;
    }
  }
  
  // ================================================================
  // TOKEN MANAGEMENT
  // ================================================================
  
  private storeTokens(tokens: AuthTokens): void {
    const encryptedTokens = simpleEncrypt(
      JSON.stringify(tokens),
      this.getEncryptionKey()
    );
    
    localStorage.setItem(TOKEN_STORAGE_KEY, encryptedTokens);
    
    // Store refresh token separately for security
    if (tokens.refreshToken) {
      const encryptedRefreshToken = simpleEncrypt(
        tokens.refreshToken,
        this.getEncryptionKey()
      );
      
      localStorage.setItem(REFRESH_TOKEN_KEY, encryptedRefreshToken);
    }
  }
  
  getAccessToken(): string | null {
    try {
      const encryptedTokens = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!encryptedTokens) return null;
      
      const decryptedTokens = simpleDecrypt(
        encryptedTokens,
        this.getEncryptionKey()
      );
      
      const tokens: AuthTokens = JSON.parse(decryptedTokens);
      
      // Check if token is expired
      if (this.isTokenExpired(tokens.accessToken)) {
        return null;
      }
      
      return tokens.accessToken;
      
    } catch (error) {
      console.error('Error getting access token:', error);
      return null;
    }
  }
  
  private decodeAndValidateToken(token: string): AuthUser {
    const decoded = simpleJwtDecode(token);
    
    if (!decoded) {
      throw new Error('Invalid token');
    }
    
    return {
      id: decoded.sub || '',
      username: decoded.username || '',
      email: decoded.email || '',
      roles: decoded.roles || [],
      permissions: decoded.permissions || [],
      firstName: decoded.firstName || '',
      lastName: decoded.lastName || '',
      isActive: true,
      lastLogin: new Date()
    };
  }
  
  private isTokenExpired(token: string): boolean {
    const decoded = simpleJwtDecode(token);
    if (!decoded || !decoded.exp) return true;
    
    return Date.now() >= decoded.exp * 1000;
  }
  
  private setupTokenRefresh(expiresIn: number): void {
    this.clearRefreshTimeout();
    
    // Refresh token 5 minutes before expiration
    const refreshTime = (expiresIn - 300) * 1000;
    
    this.refreshTokenTimeout = window.setTimeout(() => {
      this.refreshToken().catch(error => {
        console.error('Auto refresh failed:', error);
      });
    }, refreshTime);
  }
  
  private storeUserData(user: AuthUser): void {
    const encryptedUser = simpleEncrypt(
      JSON.stringify(user),
      this.getEncryptionKey()
    );
    localStorage.setItem(USER_STORAGE_KEY, encryptedUser);
  }
  
  getCurrentUser(): AuthUser | null {
    try {
      const encryptedUser = localStorage.getItem(USER_STORAGE_KEY);
      if (!encryptedUser) return null;
      
      const decryptedUser = simpleDecrypt(
        encryptedUser,
        this.getEncryptionKey()
      );
      
      return JSON.parse(decryptedUser);
      
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }
  
  isAuthenticated(): boolean {
    const token = this.getAccessToken();
    return token !== null && !this.isTokenExpired(token);
  }
  
  hasRole(role: string): boolean {
    const user = this.getCurrentUser();
    return user ? user.roles.includes(role) : false;
  }
  
  hasPermission(permission: string): boolean {
    const user = this.getCurrentUser();
    return user ? user.permissions.includes(permission) : false;
  }
  
  hasAnyRole(roles: string[]): boolean {
    const user = this.getCurrentUser();
    return user ? roles.some(role => user.roles.includes(role)) : false;
  }
  
  hasAnyPermission(permissions: string[]): boolean {
    const user = this.getCurrentUser();
    return user ? permissions.some(permission => user.permissions.includes(permission)) : false;
  }
  
  // ================================================================
  // SESSION MANAGEMENT
  // ================================================================
  
  private setupSessionTimeout(): void {
    this.resetSessionTimeout();
  }
  
  private resetSessionTimeout(): void {
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
    }
    
    this.sessionTimeout = window.setTimeout(() => {
      this.handleSessionTimeout();
    }, SESSION_TIMEOUT);
  }
  
  private handleSessionTimeout(): void {
    console.warn('Session timeout - logging out user');
    this.logout();
  }
  
  // ================================================================
  // UTILITIES
  // ================================================================
  
  private getEncryptionKey(): string {
    return 'tony-auth-key-' + (navigator.userAgent || 'default');
  }
  
  private clearAuthData(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(CSRF_TOKEN_KEY);
  }
  
  private clearTimeouts(): void {
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
      this.sessionTimeout = null;
    }
    this.clearRefreshTimeout();
  }
  
  private clearRefreshTimeout(): void {
    if (this.refreshTokenTimeout) {
      clearTimeout(this.refreshTokenTimeout);
      this.refreshTokenTimeout = null;
    }
  }
  
  // ================================================================
  // HTTP UTILITIES
  // ================================================================
  
  getAuthHeaders(): Record<string, string> {
    const token = this.getAccessToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-CSRF-Token': this.csrfToken
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }
  
  async makeAuthenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const authHeaders = this.getAuthHeaders();
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...authHeaders,
        ...options.headers
      }
    });
    
    // Handle token expiration
    if (response.status === 401) {
      try {
        await this.refreshToken();
        // Retry with new token
        const newAuthHeaders = this.getAuthHeaders();
        return fetch(url, {
          ...options,
          headers: {
            ...newAuthHeaders,
            ...options.headers
          }
        });
      } catch (error) {
        // Force logout on refresh failure
        this.logout();
        throw error;
      }
    }
    
    return response;
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService; 