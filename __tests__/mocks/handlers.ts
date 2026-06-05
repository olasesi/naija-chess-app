import { http, HttpResponse } from 'msw';

const BASE_URL = 'https://api.example.com';

export const handlers = [
  // Auth
  http.post(`${BASE_URL}/auth/login`, () => {
    return HttpResponse.json({
      success: true,
      data: {
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
        token: 'mock-jwt-token',
      },
    });
  }),

  http.post(`${BASE_URL}/auth/logout`, () => {
    return HttpResponse.json({ success: true, message: 'Logged out' });
  }),

  // Users
  http.get(`${BASE_URL}/users/:id`, ({ params }) => {
    return HttpResponse.json({
      success: true,
      data: {
        id: params.id,
        email: 'test@example.com',
        name: 'Test User',
      },
    });
  }),
];
