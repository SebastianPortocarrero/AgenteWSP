export interface User {
  id: string;
  name: string;
  avatar?: string;
  lastSeen?: Date;
}

export interface Message {
  id: string;
  content: string;
  timestamp: Date;
  sender: 'user' | 'bot' | 'operator';
  edited?: boolean;
  status?: 'sent' | 'delivered' | 'read' | 'pending_approval' | 'approved' | 'rejected';
}

export interface PendingResponse {
  id: string;
  content: string;
  timestamp: number;
  is_error?: boolean;
}

export interface Conversation {
  id: string;
  user: User;
  messages: Message[];
  status: 'pending' | 'in_progress' | 'closed';
  mode: 'auto' | 'manual' | 'hybrid';
  lastActivity: Date;
  unreadCount: number;
  tags: string[];
  assignedOperator?: string;
  pending_response?: PendingResponse | null;
}

export interface QuickResponse {
  id: string;
  text: string;
  category: string;
}

export type SenderMode = 'bot' | 'operator';

export interface ConversationFilters {
  status: string;
  dateRange: string;
  tags: string[];
  operator: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'success' | 'error';
  timestamp: Date;
  read: boolean;
  conversationId?: string;
}