import { Conversation, Message, QuickResponse, Notification } from '../types';

export const mockMessages: Message[] = [
  {
    id: '1',
    content: 'Hola, necesito información sobre mis vacaciones pendientes',
    timestamp: new Date('2024-01-15T10:30:00'),
    sender: 'user',
    status: 'read'
  },
  {
    id: '2',
    content: 'Hola! Te ayudo con esa consulta. Déjame verificar tu información en el sistema.',
    timestamp: new Date('2024-01-15T10:31:00'),
    sender: 'bot',
    status: 'read'
  },
  {
    id: '3',
    content: 'Según tus registros, tienes 15 días de vacaciones disponibles. ¿Te gustaría solicitar algún período específico?',
    timestamp: new Date('2024-01-15T10:32:00'),
    sender: 'operator',
    status: 'read'
  },
  {
    id: '4',
    content: 'Perfecto, me gustaría solicitar del 20 al 30 de enero',
    timestamp: new Date('2024-01-15T10:35:00'),
    sender: 'user',
    status: 'read'
  }
];

export const mockConversations: Conversation[] = [
  {
    id: '1',
    user: {
      id: 'user1',
      name: 'María González',
      lastSeen: new Date('2024-01-15T10:35:00')
    },
    messages: mockMessages,
    status: 'in_progress',
    mode: 'manual',
    lastActivity: new Date('2024-01-15T10:35:00'),
    unreadCount: 0,
    tags: ['vacaciones', 'solicitud'],
    assignedOperator: 'Ana García'
  },
  {
    id: '2',
    user: {
      id: 'user2',
      name: 'Carlos Ruiz',
      lastSeen: new Date('2024-01-15T09:15:00')
    },
    messages: [
      {
        id: '5',
        content: '¿Cómo puedo acceder a mi recibo de nómina?',
        timestamp: new Date('2024-01-15T09:15:00'),
        sender: 'user',
        status: 'read'
      },
      {
        id: '6',
        content: 'Puedes acceder a través del portal de empleados. Te envío el enlace.',
        timestamp: new Date('2024-01-15T09:16:00'),
        sender: 'bot',
        status: 'read'
      }
    ],
    status: 'closed',
    mode: 'auto',
    lastActivity: new Date('2024-01-15T09:16:00'),
    unreadCount: 0,
    tags: ['nómina', 'acceso']
  },
  {
    id: '3',
    user: {
      id: 'user3',
      name: 'Laura Martín',
      lastSeen: new Date('2024-01-15T11:45:00')
    },
    messages: [
      {
        id: '7',
        content: 'Tengo una duda sobre el proceso de evaluación',
        timestamp: new Date('2024-01-15T11:45:00'),
        sender: 'user',
        status: 'delivered'
      }
    ],
    status: 'pending',
    mode: 'auto',
    lastActivity: new Date('2024-01-15T11:45:00'),
    unreadCount: 1,
    tags: ['evaluación', 'consulta']
  }
];

export const quickResponses: QuickResponse[] = [
  {
    id: '1',
    text: 'Gracias por contactarnos. Te ayudo con tu consulta.',
    category: 'saludo'
  },
  {
    id: '2',
    text: 'Estoy revisando tu solicitud, te respondo en breve.',
    category: 'proceso'
  },
  {
    id: '3',
    text: 'Para más información, consulta nuestro portal de empleados.',
    category: 'información'
  },
  {
    id: '4',
    text: '¿Hay algo más en lo que pueda ayudarte?',
    category: 'seguimiento'
  }
];

export const mockNotifications: Notification[] = [
  {
    id: '1',
    title: 'Nuevo mensaje',
    message: 'Laura Martín envió un mensaje sobre evaluación',
    type: 'info',
    timestamp: new Date('2024-01-15T11:45:00'),
    read: false,
    conversationId: '3'
  },
  {
    id: '2',
    title: 'Conversación asignada',
    message: 'Se te asignó la conversación de María González',
    type: 'success',
    timestamp: new Date('2024-01-15T10:30:00'),
    read: true,
    conversationId: '1'
  },
  {
    id: '3',
    title: 'Sistema actualizado',
    message: 'El sistema de respuestas automáticas ha sido actualizado',
    type: 'info',
    timestamp: new Date('2024-01-15T09:00:00'),
    read: true
  }
];